"""Tests for Pydantic API models (src.api.models).

Covers:
- Valid construction of all request/response models
- Field constraint validation (min_length, max_length, ge, le, Literal types)
- JSON serialization round-trips
- Default values and optional fields
"""

import pytest
from pydantic import ValidationError

from src.api.models import (
    # Triage
    TriageRequest,
    TriageResponse,
    # Decompose
    SubtaskDict,
    DecomposeRequest,
    DecomposeResponse,
    # Chat
    ChatRequest,
    ChatResponse,
    # Search
    SearchRequest,
    SearchResult,
    SearchResponse,
    # Daily summary
    TicketSummary,
    DailySummaryResponse,
    # Rules
    ParseRuleRequest,
    ParseRuleResponse,
    # Judge
    JudgeRequest,
    JudgeResponse,
    # Analyze
    AnalyzeRequest,
    AnalyzeResponse,
    # Error
    ErrorResponse,
    # Suggestions
    ColumnInfo,
    TicketInfo,
    SuggestionsRequest,
    Suggestion,
    SuggestionsResponse,
)


# ===========================================================================
# TriageRequest
# ===========================================================================


class TestTriageRequest:
    """Tests for TriageRequest validation."""

    def test_valid_minimal(self):
        """Minimal valid request: ticket_id and title only."""
        req = TriageRequest(ticket_id="t-1", title="Fix login bug")
        assert req.ticket_id == "t-1"
        assert req.title == "Fix login bug"
        assert req.description == ""
        assert req.existing_labels == []

    def test_valid_with_all_fields(self):
        """Full request with all fields populates correctly."""
        req = TriageRequest(
            ticket_id="t-2",
            title="Add dark mode",
            description="Support dark theme across all pages",
            existing_labels=["frontend", "ui"],
        )
        assert req.description == "Support dark theme across all pages"
        assert req.existing_labels == ["frontend", "ui"]

    def test_title_cannot_be_empty(self):
        """title has min_length=1; empty string should raise."""
        with pytest.raises(ValidationError):
            TriageRequest(ticket_id="t-3", title="")

    def test_title_max_500_chars(self):
        """title cannot exceed 500 characters."""
        with pytest.raises(ValidationError):
            TriageRequest(ticket_id="t-4", title="x" * 501)

    def test_title_exactly_500_chars(self):
        """title of exactly 500 characters is valid."""
        req = TriageRequest(ticket_id="t-5", title="x" * 500)
        assert len(req.title) == 500

    def test_json_round_trip(self):
        """Model should serialise and deserialise without data loss."""
        req = TriageRequest(
            ticket_id="t-6",
            title="Round-trip test",
            description="desc",
            existing_labels=["bug"],
        )
        json_str = req.model_dump_json()
        restored = TriageRequest.model_validate_json(json_str)
        assert restored == req


# ===========================================================================
# TriageResponse
# ===========================================================================


class TestTriageResponse:
    """Tests for TriageResponse validation."""

    def test_valid_response(self):
        """All Literal fields accept their documented values."""
        resp = TriageResponse(
            priority="high",
            labels=["bug", "auth"],
            effort="m",
            reasoning="Login issues indicate a critical auth bug.",
        )
        assert resp.priority == "high"
        assert resp.effort == "m"

    def test_invalid_priority_rejected(self):
        """Priority outside Literal values should fail."""
        with pytest.raises(ValidationError):
            TriageResponse(priority="urgent", labels=[], effort="m", reasoning="x")

    def test_invalid_effort_rejected(self):
        """Effort outside Literal values should fail."""
        with pytest.raises(ValidationError):
            TriageResponse(priority="low", labels=[], effort="huge", reasoning="x")

    def test_all_valid_priorities(self):
        """Every valid priority value should be accepted."""
        for priority in ("low", "medium", "high", "critical"):
            resp = TriageResponse(priority=priority, labels=[], effort="s", reasoning="ok")
            assert resp.priority == priority

    def test_all_valid_efforts(self):
        """Every valid effort value should be accepted."""
        for effort in ("xs", "s", "m", "l", "xl"):
            resp = TriageResponse(priority="low", labels=[], effort=effort, reasoning="ok")
            assert resp.effort == effort

    def test_json_round_trip(self):
        """TriageResponse serialises and restores cleanly."""
        resp = TriageResponse(priority="critical", labels=["bug"], effort="xs", reasoning="prod down")
        assert TriageResponse.model_validate_json(resp.model_dump_json()) == resp


# ===========================================================================
# SubtaskDict and DecomposeRequest/Response
# ===========================================================================


class TestSubtaskDict:
    """Tests for SubtaskDict validation."""

    def test_valid_subtask(self):
        task = SubtaskDict(title="Write tests", description="Add pytest coverage", effort="s")
        assert task.effort == "s"

    def test_invalid_effort_in_subtask(self):
        with pytest.raises(ValidationError):
            SubtaskDict(title="t", description="d", effort="huge")


class TestDecomposeRequest:
    """Tests for DecomposeRequest validation."""

    def test_valid_minimal(self):
        req = DecomposeRequest(ticket_id="t-7", title="Build auth system")
        assert req.ticket_id == "t-7"
        assert req.description == ""
        assert req.context is None

    def test_title_required_and_non_empty(self):
        with pytest.raises(ValidationError):
            DecomposeRequest(ticket_id="t-8", title="")

    def test_context_optional(self):
        req = DecomposeRequest(ticket_id="t-9", title="Task", context="FastAPI backend")
        assert req.context == "FastAPI backend"


class TestDecomposeResponse:
    """Tests for DecomposeResponse validation."""

    def test_valid_response(self):
        resp = DecomposeResponse(
            subtasks=[{"title": "Step 1", "description": "Do it", "effort": "s"}],
            dependencies=[(1, 0)],
            reasoning="Break into phases",
        )
        assert len(resp.subtasks) == 1
        assert resp.dependencies == [(1, 0)]

    def test_empty_subtasks_allowed(self):
        resp = DecomposeResponse(subtasks=[], dependencies=[], reasoning="none")
        assert resp.subtasks == []

    def test_default_dependencies_empty(self):
        resp = DecomposeResponse(subtasks=[], reasoning="ok")
        assert resp.dependencies == []


# ===========================================================================
# ChatRequest and ChatResponse
# ===========================================================================


class TestChatRequest:
    """Tests for ChatRequest validation."""

    def test_valid_minimal(self):
        req = ChatRequest(message="What tickets are blocked?")
        assert req.message == "What tickets are blocked?"
        assert req.context is None
        assert req.board_context is None

    def test_message_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            ChatRequest(message="")

    def test_context_and_board_context_optional(self):
        req = ChatRequest(
            message="Create a ticket",
            context={"view": "board"},
            board_context={"board_id": "b-1"},
        )
        assert req.context == {"view": "board"}

    def test_json_round_trip(self):
        req = ChatRequest(message="Show me bugs")
        assert ChatRequest.model_validate_json(req.model_dump_json()) == req


class TestChatResponse:
    """Tests for ChatResponse validation."""

    def test_valid_response(self):
        resp = ChatResponse(
            action="create",
            params={"title": "New ticket"},
            response="I will create that ticket.",
        )
        assert resp.action == "create"

    def test_invalid_action_rejected(self):
        with pytest.raises(ValidationError):
            ChatResponse(action="delete", params={}, response="ok")

    def test_all_valid_actions(self):
        for action in ("create", "update", "move", "search", "summarize", "decompose", "none"):
            resp = ChatResponse(action=action, params={}, response="ok")
            assert resp.action == action

    def test_default_params_is_empty_dict(self):
        resp = ChatResponse(action="none", response="ok")
        assert resp.params == {}


# ===========================================================================
# SearchRequest and SearchResult/Response
# ===========================================================================


class TestSearchRequest:
    """Tests for SearchRequest validation."""

    def test_valid_request(self):
        req = SearchRequest(query="login bug", limit=5)
        assert req.query == "login bug"
        assert req.limit == 5

    def test_query_cannot_be_empty(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_default_limit(self):
        req = SearchRequest(query="auth")
        assert req.limit == 5

    def test_limit_min_is_1(self):
        req = SearchRequest(query="x", limit=1)
        assert req.limit == 1

    def test_limit_max_is_20(self):
        req = SearchRequest(query="x", limit=20)
        assert req.limit == 20

    def test_limit_too_high_rejected(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="x", limit=21)


class TestSearchResult:
    """Tests for SearchResult validation."""

    def test_valid_result(self):
        r = SearchResult(id="t-1", title="Bug", description="desc", score=0.9)
        assert r.score == 0.9
        assert r.explanation is None

    def test_score_must_be_0_to_1(self):
        with pytest.raises(ValidationError):
            SearchResult(id="x", title="x", description="x", score=1.5)

    def test_score_exactly_0_and_1_valid(self):
        r0 = SearchResult(id="x", title="x", description="x", score=0.0)
        r1 = SearchResult(id="x", title="x", description="x", score=1.0)
        assert r0.score == 0.0
        assert r1.score == 1.0


class TestSearchResponse:
    """Tests for SearchResponse validation."""

    def test_valid_response(self):
        result = SearchResult(id="t-1", title="Bug", description="desc", score=0.8)
        resp = SearchResponse(results=[result], query="bug")
        assert resp.query == "bug"
        assert len(resp.results) == 1

    def test_empty_results_valid(self):
        resp = SearchResponse(results=[], query="nothing")
        assert resp.results == []


# ===========================================================================
# JudgeRequest and JudgeResponse
# ===========================================================================


class TestJudgeRequest:
    """Tests for JudgeRequest validation."""

    def test_valid_minimal(self):
        req = JudgeRequest(title="Fix crash")
        assert req.title == "Fix crash"
        assert req.description == ""
        assert req.priority == "medium"
        assert req.effort == "m"
        assert req.labels == []

    def test_title_required(self):
        with pytest.raises(ValidationError):
            JudgeRequest(title="")

    def test_with_all_fields(self):
        req = JudgeRequest(
            title="Fix auth bug",
            description="Full description",
            priority="critical",
            effort="l",
            labels=["bug", "auth"],
        )
        assert req.labels == ["bug", "auth"]


class TestJudgeResponse:
    """Tests for JudgeResponse validation."""

    def test_valid_response(self):
        resp = JudgeResponse(
            clarity_score=8,
            completeness_score=7,
            actionability_score=9,
            feedback="Good ticket overall.",
            overall_score=8.0,
        )
        assert resp.clarity_score == 8

    def test_scores_must_be_0_to_10(self):
        with pytest.raises(ValidationError):
            JudgeResponse(
                clarity_score=11,
                completeness_score=5,
                actionability_score=5,
                feedback="x",
                overall_score=5.0,
            )

    def test_overall_score_0_to_10(self):
        with pytest.raises(ValidationError):
            JudgeResponse(
                clarity_score=5,
                completeness_score=5,
                actionability_score=5,
                feedback="x",
                overall_score=10.1,
            )

    def test_boundary_values_valid(self):
        resp = JudgeResponse(
            clarity_score=0,
            completeness_score=10,
            actionability_score=5,
            feedback="ok",
            overall_score=0.0,
        )
        assert resp.clarity_score == 0
        assert resp.completeness_score == 10


# ===========================================================================
# ErrorResponse
# ===========================================================================


class TestErrorResponse:
    """Tests for ErrorResponse validation."""

    def test_valid_error(self):
        err = ErrorResponse(error="NotFoundError", message="Ticket not found")
        assert err.error == "NotFoundError"
        assert err.details == {}

    def test_with_details(self):
        err = ErrorResponse(error="ValidationError", message="Bad input", details={"field": "title"})
        assert err.details == {"field": "title"}

    def test_json_round_trip(self):
        err = ErrorResponse(error="E", message="m", details={"k": "v"})
        assert ErrorResponse.model_validate_json(err.model_dump_json()) == err


# ===========================================================================
# SuggestionsRequest / Response
# ===========================================================================


class TestSuggestionsModels:
    """Tests for Suggestions models."""

    def test_column_info_defaults(self):
        col = ColumnInfo(id="c-1", name="Todo")
        assert col.position == 0

    def test_ticket_info_defaults(self):
        t = TicketInfo(id="t-1", title="Bug", column_id="c-1")
        assert t.priority == "medium"
        assert t.effort == "m"
        assert t.labels == []

    def test_suggestions_request_empty(self):
        req = SuggestionsRequest()
        assert req.columns == []
        assert req.tickets == []

    def test_suggestion_defaults(self):
        s = Suggestion(type="stale_ticket", message="This ticket is stale")
        assert s.action == ""
        assert s.priority == "medium"
        assert s.ticket_id is None
        assert s.column_id is None

    def test_suggestions_response(self):
        s = Suggestion(type="wip_limit", message="Too many WIP tickets", priority="high")
        resp = SuggestionsResponse(suggestions=[s])
        assert len(resp.suggestions) == 1
        assert resp.suggestions[0].priority == "high"
