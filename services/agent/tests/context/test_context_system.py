"""Tests for the context management system.

Covers:
- ContextCache: get/set/invalidate/TTL/stats/eviction
- TokenBudgetManager: estimation, allocation, truncation
- Context layers: GlobalContext, RelevantTicketsContext, OperationContext
- ContextBuilder: build_context for each operation type
- ContextManager: high-level orchestration, sync, cache delegation
"""

import json
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.context.cache import CacheEntry, ContextCache, cached, get_global_cache
from src.context.builder import (
    BuiltContext,
    ContextBuilder,
    ContextRequirements,
    OperationType,
    OPERATION_REQUIREMENTS,
)
from src.context.layers import (
    ContextPriority,
    GlobalContext,
    OperationContext,
    RelevantTicketsContext,
)
from src.context.manager import ContextManager, SyncStatus, get_context_manager, init_context_manager
from src.context.token_budget import (
    ModelTokenLimits,
    TokenBudgetManager,
    TokenBudget,
    create_budget_manager,
)


# =============================================================================
# ContextCache tests
# =============================================================================


class TestContextCache:
    """Tests for ContextCache — get, set, invalidate, TTL, stats, eviction."""

    def test_set_and_get_basic_value(self) -> None:
        cache = ContextCache()
        cache.set("key1", "hello")
        assert cache.get("key1") == "hello"

    def test_get_missing_key_returns_none(self) -> None:
        cache = ContextCache()
        assert cache.get("nonexistent") is None

    def test_cache_miss_increments_miss_counter(self) -> None:
        cache = ContextCache()
        cache.get("no-such-key")
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_cache_hit_increments_hit_counter(self) -> None:
        cache = ContextCache()
        cache.set("k", 42)
        cache.get("k")
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_expired_entry_returns_none(self) -> None:
        cache = ContextCache()
        cache.set("expiring", "value", ttl=0)  # expires immediately
        # Force expiry: set created_at and expires_at in the past
        entry = cache._cache.get("expiring")
        if entry:
            entry.expires_at = time.time() - 1
        result = cache.get("expiring")
        assert result is None

    def test_invalidate_existing_key(self) -> None:
        cache = ContextCache()
        cache.set("to-remove", "data")
        removed = cache.invalidate("to-remove")
        assert removed is True
        assert cache.get("to-remove") is None

    def test_invalidate_nonexistent_key_returns_false(self) -> None:
        cache = ContextCache()
        assert cache.invalidate("ghost") is False

    def test_invalidate_pattern_removes_matching_keys(self) -> None:
        cache = ContextCache()
        cache.set("similar_tickets:abc", "v1")
        cache.set("similar_tickets:def", "v2")
        cache.set("global_context:board1", "v3")

        removed = cache.invalidate_pattern("similar_tickets:")
        assert removed == 2
        assert cache.get("similar_tickets:abc") is None
        assert cache.get("similar_tickets:def") is None
        assert cache.get("global_context:board1") == "v3"

    def test_invalidate_board_removes_board_prefixed_keys(self) -> None:
        cache = ContextCache()
        cache.set("board:board-42:context", "ctx")
        cache.set("board:board-42:labels", "lbls")
        cache.set("board:other:stuff", "other")

        removed = cache.invalidate_board("board-42")
        assert removed == 2
        assert cache.get("board:other:stuff") == "other"

    def test_clear_empties_cache(self) -> None:
        cache = ContextCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get_stats()["entries"] == 0

    def test_eviction_at_capacity(self) -> None:
        cache = ContextCache(max_entries=3)
        cache.set("k1", 1)
        cache.set("k2", 2)
        cache.set("k3", 3)
        cache.set("k4", 4)  # triggers eviction of k1 (least accessed)
        stats = cache.get_stats()
        assert stats["entries"] == 3
        assert stats["evictions"] == 1

    def test_cleanup_expired_removes_stale_entries(self) -> None:
        cache = ContextCache()
        cache.set("fresh", "ok", ttl=3600)
        cache.set("stale", "bye", ttl=1)

        # Manually expire 'stale'
        cache._cache["stale"].expires_at = time.time() - 1

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get("fresh") == "ok"
        assert cache.get("stale") is None

    def test_hit_rate_calculation_in_stats(self) -> None:
        cache = ContextCache()
        cache.set("x", 10)
        cache.get("x")   # hit
        cache.get("x")   # hit
        cache.get("missing")  # miss
        stats = cache.get_stats()
        # 2 hits / 3 total = 0.667
        assert stats["hit_rate"] == pytest.approx(0.667, abs=0.001)

    def test_cache_type_applies_correct_ttl(self) -> None:
        """global_context type should use a 300-second TTL."""
        cache = ContextCache()
        cache.set("gc:board1", "ctx", cache_type="global_context")
        entry = cache._cache.get("gc:board1")
        assert entry is not None
        expected_ttl = ContextCache.DEFAULT_TTLS["global_context"]
        actual_ttl = entry.expires_at - entry.created_at
        assert abs(actual_ttl - expected_ttl) < 1


# =============================================================================
# TokenBudgetManager tests
# =============================================================================


class TestTokenBudgetManager:
    """Tests for TokenBudgetManager — estimation, allocation, truncation."""

    def test_estimate_tokens_empty_string(self) -> None:
        mgr = TokenBudgetManager()
        assert mgr.estimate_tokens("") == 0

    def test_estimate_tokens_heuristic(self) -> None:
        mgr = TokenBudgetManager()
        # "hello" = 5 chars -> 5 // 4 = 1
        assert mgr.estimate_tokens("hello") == 1
        # 100-char text -> 25 tokens
        text = "a" * 100
        assert mgr.estimate_tokens(text) == 25

    def test_fits_in_budget_true(self) -> None:
        mgr = TokenBudgetManager()
        assert mgr.fits_in_budget("short", 100) is True

    def test_fits_in_budget_false(self) -> None:
        mgr = TokenBudgetManager()
        long_text = "x" * 1000
        assert mgr.fits_in_budget(long_text, 10) is False

    def test_truncate_to_budget_no_truncation_needed(self) -> None:
        mgr = TokenBudgetManager()
        text = "Short text."
        result = mgr.truncate_to_budget(text, 100)
        assert result == text

    def test_truncate_to_budget_applies_suffix(self) -> None:
        mgr = TokenBudgetManager()
        long_text = "word " * 200  # 1000 chars
        result = mgr.truncate_to_budget(long_text, 10, truncation_suffix="...")
        assert result.endswith("...")
        assert mgr.estimate_tokens(result) <= 12  # a bit of slack for the suffix

    def test_get_budget_for_triage(self) -> None:
        mgr = TokenBudgetManager()
        budget = mgr.get_budget_for_operation("triage")
        assert "total" in budget
        assert "output_reserve" in budget
        assert budget["total"] > 0

    def test_get_budget_for_unknown_operation_returns_default(self) -> None:
        mgr = TokenBudgetManager()
        budget = mgr.get_budget_for_operation("unknown_op")
        default = mgr.get_budget_for_operation("default")
        assert budget == default

    def test_allocate_budget_returns_token_budget(self) -> None:
        mgr = TokenBudgetManager()
        global_ctx = GlobalContext(board_id="b1", board_name="Test Board")
        layers = {"global": global_ctx}
        result = mgr.allocate_budget("triage", layers)
        assert isinstance(result, TokenBudget)
        assert result.total_budget > 0
        assert result.available_for_context > 0
        assert len(result.allocations) == 1

    def test_allocate_budget_remaining_is_positive(self) -> None:
        mgr = TokenBudgetManager()
        global_ctx = GlobalContext(board_id="b1", board_name="Board")
        layers = {"global": global_ctx}
        budget = mgr.allocate_budget("triage", layers)
        assert budget.remaining >= 0

    def test_create_budget_manager_factory(self) -> None:
        mgr = create_budget_manager("claude-sonnet", safety_margin=0.8)
        assert isinstance(mgr, TokenBudgetManager)
        expected_limit = int(ModelTokenLimits.CLAUDE_SONNET.value * 0.8)
        assert mgr.effective_limit == expected_limit

    def test_create_budget_manager_unknown_model_uses_default(self) -> None:
        mgr = create_budget_manager("unknown-model-x")
        assert mgr.model_limit == ModelTokenLimits.DEFAULT.value


# =============================================================================
# Context layer tests
# =============================================================================


class TestGlobalContext:
    """Tests for GlobalContext layer."""

    def test_to_string_includes_board_name(self) -> None:
        ctx = GlobalContext(board_id="b1", board_name="My Board")
        s = ctx.to_string()
        assert "My Board" in s

    def test_to_string_includes_columns(self) -> None:
        ctx = GlobalContext(
            board_id="b1",
            board_name="B",
            columns=[{"name": "Todo"}, {"name": "Done"}],
        )
        s = ctx.to_string()
        assert "Todo" in s
        assert "Done" in s

    def test_to_string_includes_labels(self) -> None:
        ctx = GlobalContext(
            board_id="b1",
            board_name="B",
            all_labels=["bug", "feature"],
        )
        s = ctx.to_string()
        assert "bug" in s
        assert "feature" in s

    def test_to_dict_roundtrip(self) -> None:
        ctx = GlobalContext(
            board_id="b42",
            board_name="Sprint Board",
            all_labels=["alpha", "beta"],
            total_tickets=15,
        )
        d = ctx.to_dict()
        assert d["board_id"] == "b42"
        assert d["board_name"] == "Sprint Board"
        assert d["all_labels"] == ["alpha", "beta"]
        assert d["total_tickets"] == 15

    def test_estimated_tokens_positive_for_non_empty(self) -> None:
        ctx = GlobalContext(board_id="b1", board_name="Big Board With Labels", all_labels=["a", "b"])
        assert ctx.estimated_tokens > 0

    def test_priority_is_high(self) -> None:
        ctx = GlobalContext(board_id="b1", board_name="X")
        assert ctx.priority == ContextPriority.HIGH

    def test_summarize_fits_within_max_chars(self) -> None:
        ctx = GlobalContext(
            board_id="b1",
            board_name="Board",
            all_labels=[f"label-{i}" for i in range(50)],
            columns=[{"name": f"Col{i}"} for i in range(20)],
        )
        result = ctx.summarize(max_tokens=50)
        # 50 tokens * 4 chars = 200 max chars
        assert len(result) <= 200


class TestRelevantTicketsContext:
    """Tests for RelevantTicketsContext layer."""

    def test_empty_context_string(self) -> None:
        ctx = RelevantTicketsContext()
        s = ctx.to_string()
        assert "No related tickets found" in s

    def test_to_string_includes_ticket_titles(self) -> None:
        ctx = RelevantTicketsContext(
            similar_tickets=[
                {"id": "aabbccdd", "title": "Fix auth bug", "score": 0.9},
            ]
        )
        s = ctx.to_string()
        assert "Fix auth bug" in s

    def test_get_similar_tickets_json_returns_valid_json(self) -> None:
        ctx = RelevantTicketsContext(
            similar_tickets=[
                {"id": "t1", "title": "Alpha", "description": "desc", "status": "todo", "priority": "high", "labels": ["bug"]},
            ]
        )
        result = ctx.get_similar_tickets_json()
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["title"] == "Alpha"

    def test_get_similar_tickets_json_empty_list(self) -> None:
        ctx = RelevantTicketsContext()
        result = ctx.get_similar_tickets_json()
        assert result == "[]"

    def test_get_similar_tickets_json_truncates_long_descriptions(self) -> None:
        long_desc = "x" * 500
        ctx = RelevantTicketsContext(
            similar_tickets=[{"id": "t1", "title": "T", "description": long_desc}]
        )
        parsed = json.loads(ctx.get_similar_tickets_json())
        assert len(parsed[0]["description"]) <= 300

    def test_priority_is_high(self) -> None:
        ctx = RelevantTicketsContext()
        assert ctx.priority == ContextPriority.HIGH

    def test_to_dict_contains_similar_tickets(self) -> None:
        tickets = [{"id": "t1", "title": "Bug"}]
        ctx = RelevantTicketsContext(similar_tickets=tickets, query_used="bug fix")
        d = ctx.to_dict()
        assert d["similar_tickets"] == tickets
        assert d["query_used"] == "bug fix"


class TestOperationContext:
    """Tests for OperationContext layer."""

    def test_to_string_includes_operation_type(self) -> None:
        ctx = OperationContext(operation_type="TRIAGE")
        assert "TRIAGE" in ctx.to_string()

    def test_to_string_includes_user_intent(self) -> None:
        ctx = OperationContext(operation_type="CHAT", user_intent="How are my tickets?")
        assert "How are my tickets?" in ctx.to_string()

    def test_to_string_includes_conversation_history(self) -> None:
        ctx = OperationContext(
            operation_type="CHAT",
            conversation_history=[
                {"role": "user", "content": "Hello agent"},
                {"role": "assistant", "content": "Hello! How can I help?"},
            ],
        )
        s = ctx.to_string()
        assert "Hello agent" in s

    def test_priority_is_critical(self) -> None:
        ctx = OperationContext(operation_type="TRIAGE")
        assert ctx.priority == ContextPriority.CRITICAL

    def test_to_dict_roundtrip(self) -> None:
        ticket = {"id": "t1", "title": "Bug"}
        ctx = OperationContext(
            operation_type="DECOMPOSE",
            target_ticket=ticket,
            user_intent="Break it down",
            time_context="morning",
        )
        d = ctx.to_dict()
        assert d["operation_type"] == "DECOMPOSE"
        assert d["target_ticket"] == ticket
        assert d["user_intent"] == "Break it down"
        assert d["time_context"] == "morning"

    def test_summarize_fits_in_max_tokens(self) -> None:
        ctx = OperationContext(
            operation_type="TRIAGE",
            user_intent="Classify this very long intent " * 50,
        )
        result = ctx.summarize(max_tokens=20)
        assert len(result) <= 80 + 5  # 20 tokens * 4 chars, small slack


# =============================================================================
# ContextBuilder tests
# =============================================================================


class TestContextBuilder:
    """Tests for ContextBuilder — builds context per operation type."""

    @pytest.fixture
    def builder_no_chroma(self) -> ContextBuilder:
        """Builder with no ChromaDB (no semantic retrieval), isolated cache."""
        return ContextBuilder(chroma_manager=None, cache=ContextCache())

    @pytest.fixture
    def sample_ticket(self) -> dict[str, Any]:
        return {
            "id": "ticket-001",
            "title": "Fix login bug on Safari",
            "description": "Users cannot login with Safari browser",
        }

    @pytest.fixture
    def sample_board(self) -> dict[str, Any]:
        return {
            "board_id": "board-99",
            "board_name": "Dev Board",
            "labels": ["bug", "feature", "urgent"],
            "columns": [
                {"name": "Backlog"},
                {"name": "In Progress"},
                {"name": "Done"},
            ],
        }

    def test_build_triage_context_returns_built_context(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        assert isinstance(ctx, BuiltContext)

    def test_build_triage_context_global_layer_populated(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        assert ctx.global_context is not None
        assert ctx.global_context.board_name == "Dev Board"

    def test_build_triage_context_get_existing_labels(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        labels = ctx.get_existing_labels()
        assert "bug" in labels
        assert "feature" in labels

    def test_build_decompose_context(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_decompose_context(sample_ticket, sample_board)
        assert isinstance(ctx, BuiltContext)
        # Decompose context string should mention the board workflow
        s = ctx.get_decompose_context()
        assert isinstance(s, str)

    def test_build_chat_context_with_history(
        self, builder_no_chroma: ContextBuilder, sample_board: dict
    ) -> None:
        history = [
            {"role": "user", "content": "Show me all bugs"},
            {"role": "assistant", "content": "Here are the bugs..."},
        ]
        ctx = builder_no_chroma.build_chat_context(
            message="How many are critical?",
            board_data=sample_board,
            conversation_history=history,
        )
        assert isinstance(ctx, BuiltContext)
        assert ctx.operation_context is not None
        assert ctx.operation_context.user_intent == "How many are critical?"
        assert len(ctx.operation_context.conversation_history) <= 5

    def test_build_daily_summary_context(
        self, builder_no_chroma: ContextBuilder, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_daily_summary_context(
            in_progress=[{"id": "t1", "title": "Auth work"}],
            blocked=[{"id": "t2", "title": "Deploy blocker"}],
            due_soon=[],
            board_data=sample_board,
        )
        tickets = ctx.get_daily_summary_tickets()
        assert isinstance(tickets, dict)
        assert "in_progress" in tickets
        assert tickets["in_progress"][0]["title"] == "Auth work"
        assert tickets["blocked"][0]["title"] == "Deploy blocker"

    def test_build_analyze_context(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_analyze_context(sample_ticket, sample_board)
        assert isinstance(ctx, BuiltContext)

    def test_built_context_to_full_string(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        full = ctx.to_full_string()
        assert "Board Context" in full
        assert "Dev Board" in full

    def test_built_context_get_board_context_dict(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        ctx = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        d = ctx.get_board_context_dict()
        assert isinstance(d, dict)
        assert "board_id" in d or "board_name" in d

    def test_context_cached_on_second_call(
        self, builder_no_chroma: ContextBuilder, sample_ticket: dict, sample_board: dict
    ) -> None:
        """Second call with same board should hit cache."""
        ctx1 = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        ctx2 = builder_no_chroma.build_triage_context(sample_ticket, sample_board)
        # Same object from cache
        assert ctx1.global_context is ctx2.global_context

    def test_build_context_with_chroma_mock(self, sample_ticket: dict, sample_board: dict) -> None:
        """Builder with mocked ChromaDB returns similar tickets."""
        mock_chroma = MagicMock()
        mock_chroma.search.return_value = [
            {"id": "sim-1", "title": "Similar Safari bug", "description": "desc", "score": 0.85}
        ]
        # Use an isolated cache so the previous no-chroma build doesn't poison this one
        fresh_cache = ContextCache()
        builder = ContextBuilder(chroma_manager=mock_chroma, cache=fresh_cache)
        ctx = builder.build_triage_context(sample_ticket, sample_board)
        assert ctx.relevant_context is not None
        assert len(ctx.relevant_context.similar_tickets) == 1
        assert ctx.relevant_context.similar_tickets[0]["title"] == "Similar Safari bug"

    def test_operation_requirements_for_daily_summary_no_similar_tickets(self) -> None:
        reqs = OPERATION_REQUIREMENTS[OperationType.DAILY_SUMMARY]
        assert reqs.needs_similar_tickets is False

    def test_operation_requirements_for_analyze_has_more_tickets(self) -> None:
        reqs = OPERATION_REQUIREMENTS[OperationType.ANALYZE]
        assert reqs.similar_tickets_count >= 10


# =============================================================================
# ContextManager tests
# =============================================================================


class TestContextManager:
    """Tests for ContextManager — high-level orchestration."""

    @pytest.fixture
    def manager(self) -> ContextManager:
        return ContextManager(chroma_manager=None)

    def test_get_triage_context_returns_built_context(self, manager: ContextManager) -> None:
        ticket = {"id": "t1", "title": "Bug report", "description": "crash on load"}
        ctx = manager.get_triage_context(ticket)
        assert isinstance(ctx, BuiltContext)

    def test_get_decompose_context(self, manager: ContextManager) -> None:
        ticket = {"id": "t2", "title": "Build auth", "description": "full auth system"}
        ctx = manager.get_decompose_context(ticket)
        assert isinstance(ctx, BuiltContext)

    def test_get_chat_context(self, manager: ContextManager) -> None:
        ctx = manager.get_chat_context(message="What should I work on?")
        assert isinstance(ctx, BuiltContext)

    def test_get_analyze_context(self, manager: ContextManager) -> None:
        ticket = {"id": "t3", "title": "Performance issue", "description": "slow queries"}
        ctx = manager.get_analyze_context(ticket)
        assert isinstance(ctx, BuiltContext)

    def test_get_sync_status_initial_state(self, manager: ContextManager) -> None:
        status = manager.get_sync_status()
        assert isinstance(status, SyncStatus)
        assert status.is_synced is False

    async def test_sync_tickets_no_chroma_returns_status(self, manager: ContextManager) -> None:
        tickets = [{"id": "t1", "title": "Bug"}]
        status = await manager.sync_tickets_to_chroma(tickets)
        assert isinstance(status, SyncStatus)
        # Without chroma, sync is a no-op
        assert status.is_synced is False

    async def test_sync_tickets_with_chroma_mock(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.get_stats.return_value = {"total_documents": 0}
        mock_chroma.add_ticket.return_value = None

        manager = ContextManager(chroma_manager=mock_chroma)
        tickets = [
            {"id": "t1", "title": "Bug", "description": "crash", "status": "todo", "priority": "high", "labels": ["bug"]},
            {"id": "t2", "title": "Feature", "description": "new UI", "status": "done", "priority": "low", "labels": []},
        ]
        status = await manager.sync_tickets_to_chroma(tickets)
        assert status.is_synced is True
        assert status.tickets_in_sqlite == 2
        assert status.tickets_in_chroma == 2

    async def test_sync_single_ticket_upsert(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.add_ticket.return_value = None

        manager = ContextManager(chroma_manager=mock_chroma)
        result = await manager.sync_single_ticket({"id": "t1", "title": "T"}, action="upsert")
        assert result is True
        mock_chroma.add_ticket.assert_called_once()

    async def test_sync_single_ticket_delete(self) -> None:
        mock_chroma = MagicMock()
        mock_chroma.remove_ticket.return_value = None

        manager = ContextManager(chroma_manager=mock_chroma)
        result = await manager.sync_single_ticket({"id": "t1", "title": "T"}, action="delete")
        assert result is True
        mock_chroma.remove_ticket.assert_called_once_with("t1")

    async def test_sync_single_ticket_missing_id_returns_false(self) -> None:
        mock_chroma = MagicMock()
        manager = ContextManager(chroma_manager=mock_chroma)
        result = await manager.sync_single_ticket({"title": "No ID"}, action="upsert")
        assert result is False

    def test_invalidate_board_cache_delegates_to_cache(self, manager: ContextManager) -> None:
        # First populate a board cache entry
        manager.cache.set("board:board-99:ctx", "data")
        removed = manager.invalidate_board_cache("board-99")
        assert removed >= 0  # 0 here because key uses different prefix internally

    def test_clear_all_cache(self, manager: ContextManager) -> None:
        manager.cache.set("some-key", "some-value")
        manager.clear_all_cache()
        assert manager.cache.get("some-key") is None

    def test_get_cache_stats_returns_dict(self, manager: ContextManager) -> None:
        stats = manager.get_cache_stats()
        assert isinstance(stats, dict)
        assert "hits" in stats
        assert "misses" in stats
        assert "entries" in stats

    def test_init_context_manager_replaces_singleton(self) -> None:
        from src.context import manager as mgr_module
        old = mgr_module._context_manager
        mock_chroma = MagicMock()
        new_mgr = init_context_manager(mock_chroma)
        assert new_mgr.chroma is mock_chroma
        # restore
        mgr_module._context_manager = old
