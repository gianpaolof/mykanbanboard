"""Tests for AgentAnalytics - SQLite-backed analytics tracker.

Covers:
- _hash_data: determinism, collision resistance, edge cases
- log_call: persistence, field mapping
- get_stats: aggregation, period filtering, empty state
- get_module_stats: module-level aggregation
- get_hourly_breakdown: grouping logic
- get_module_breakdown: multi-module breakdown
- get_recent_errors: failure filtering and limit
- cleanup_old_data: TTL deletion
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.agent.analytics import AgentAnalytics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def analytics(tmp_path: Path) -> AgentAnalytics:
    """Fresh AgentAnalytics instance backed by a temp SQLite DB."""
    db_file = tmp_path / "test_analytics.db"
    return AgentAnalytics(db_path=str(db_file))


# ---------------------------------------------------------------------------
# _hash_data
# ---------------------------------------------------------------------------


class TestHashData:
    """Tests for the _hash_data helper method."""

    def test_returns_16_char_hex(self, analytics: AgentAnalytics) -> None:
        result = analytics._hash_data({"key": "value"})
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic_same_input(self, analytics: AgentAnalytics) -> None:
        data = {"title": "Fix bug", "priority": "high"}
        assert analytics._hash_data(data) == analytics._hash_data(data)

    def test_different_inputs_different_hashes(self, analytics: AgentAnalytics) -> None:
        h1 = analytics._hash_data({"a": 1})
        h2 = analytics._hash_data({"a": 2})
        assert h1 != h2

    def test_key_order_invariant(self, analytics: AgentAnalytics) -> None:
        # json.dumps with sort_keys=True makes order irrelevant
        h1 = analytics._hash_data({"b": 2, "a": 1})
        h2 = analytics._hash_data({"a": 1, "b": 2})
        assert h1 == h2

    def test_handles_non_serialisable_data(self, analytics: AgentAnalytics) -> None:
        # Falls back to str() for non-JSON-serialisable objects
        result = analytics._hash_data(object())
        assert len(result) == 16

    def test_empty_dict(self, analytics: AgentAnalytics) -> None:
        result = analytics._hash_data({})
        assert len(result) == 16

    def test_nested_dict(self, analytics: AgentAnalytics) -> None:
        data = {"outer": {"inner": [1, 2, 3]}}
        result = analytics._hash_data(data)
        assert len(result) == 16


# ---------------------------------------------------------------------------
# log_call + persistence
# ---------------------------------------------------------------------------


class TestLogCall:
    """Tests for log_call and raw data persistence."""

    def test_log_call_inserts_row(self, analytics: AgentAnalytics) -> None:
        analytics.log_call(
            module_name="triage",
            input_data={"title": "Test"},
            output_data={"priority": "high"},
            latency_ms=42,
        )
        stats = analytics.get_stats(period="hour")
        assert stats["total_calls"] == 1

    def test_log_call_failure(self, analytics: AgentAnalytics) -> None:
        analytics.log_call(
            module_name="triage",
            input_data={},
            output_data={},
            latency_ms=10,
            success=False,
            error_message="LLM timeout",
        )
        errors = analytics.get_recent_errors(limit=10)
        assert len(errors) == 1
        assert errors[0]["error_message"] == "LLM timeout"
        assert errors[0]["module_name"] == "triage"

    def test_log_call_tokens_stored(self, analytics: AgentAnalytics) -> None:
        analytics.log_call(
            module_name="decompose",
            input_data={"task": "build feature"},
            output_data={"subtasks": []},
            latency_ms=200,
            tokens_used=500,
        )
        stats = analytics.get_stats(period="hour")
        assert stats["total_tokens"] == 500

    def test_multiple_calls_accumulate(self, analytics: AgentAnalytics) -> None:
        for i in range(5):
            analytics.log_call(
                module_name="triage",
                input_data={"i": i},
                output_data={"result": i},
                latency_ms=10 * i,
            )
        stats = analytics.get_stats(period="hour")
        assert stats["total_calls"] == 5


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


class TestGetStats:
    """Tests for the aggregate statistics method."""

    def test_empty_db_returns_zero_stats(self, analytics: AgentAnalytics) -> None:
        stats = analytics.get_stats(period="day")
        assert stats["total_calls"] == 0
        assert stats["avg_latency_ms"] == 0
        assert stats["success_rate"] == 0
        assert stats["total_tokens"] == 0

    def test_success_rate_all_success(self, analytics: AgentAnalytics) -> None:
        for _ in range(4):
            analytics.log_call("m", {}, {}, latency_ms=100, success=True)
        stats = analytics.get_stats(period="hour")
        assert stats["success_rate"] == 100.0

    def test_success_rate_mixed(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=50, success=True)
        analytics.log_call("m", {}, {}, latency_ms=50, success=False, error_message="err")
        stats = analytics.get_stats(period="hour")
        assert stats["success_rate"] == 50.0

    def test_avg_latency_calculated_correctly(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=100)
        analytics.log_call("m", {}, {}, latency_ms=200)
        stats = analytics.get_stats(period="hour")
        assert stats["avg_latency_ms"] == 150.0

    def test_period_hour_filters_old_data(self, analytics: AgentAnalytics, tmp_path: Path) -> None:
        """Calls logged with old timestamps should not appear in 'hour' period."""
        import sqlite3

        db_path = str(tmp_path / "test_analytics.db")
        fresh = AgentAnalytics(db_path=db_path)

        # Insert a row with a timestamp 2 hours in the past directly
        old_ts = (datetime.now() - timedelta(hours=2)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO agent_calls
                (timestamp, module_name, input_hash, output_hash, latency_ms, tokens_used, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (old_ts, "triage", "aaa", "bbb", 50, 0, True),
            )

        stats = fresh.get_stats(period="hour")
        assert stats["total_calls"] == 0

    def test_period_week_includes_recent(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10)
        stats = analytics.get_stats(period="week")
        assert stats["total_calls"] == 1

    def test_unknown_period_defaults_to_day(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10)
        stats = analytics.get_stats(period="unknown_period")
        # Should not raise; defaults to day window
        assert stats["total_calls"] == 1


# ---------------------------------------------------------------------------
# get_module_stats
# ---------------------------------------------------------------------------


class TestGetModuleStats:
    """Tests for per-module statistics."""

    def test_module_stats_empty(self, analytics: AgentAnalytics) -> None:
        stats = analytics.get_module_stats("nonexistent", period="day")
        assert stats["total_calls"] == 0
        assert stats["module_name"] == "nonexistent"

    def test_module_stats_correct_module_only(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("triage", {}, {}, latency_ms=100)
        analytics.log_call("decompose", {}, {}, latency_ms=200)
        stats = analytics.get_module_stats("triage", period="hour")
        assert stats["total_calls"] == 1
        assert stats["avg_latency_ms"] == 100.0

    def test_module_stats_min_max_latency(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {"i": 0}, {}, latency_ms=50)
        analytics.log_call("m", {"i": 1}, {}, latency_ms=300)
        analytics.log_call("m", {"i": 2}, {}, latency_ms=150)
        stats = analytics.get_module_stats("m", period="hour")
        assert stats["min_latency_ms"] == 50
        assert stats["max_latency_ms"] == 300

    def test_module_stats_unique_inputs(self, analytics: AgentAnalytics) -> None:
        # Two calls with same input → 1 unique; one different → 2 unique
        analytics.log_call("m", {"x": 1}, {}, latency_ms=10)
        analytics.log_call("m", {"x": 1}, {}, latency_ms=10)
        analytics.log_call("m", {"x": 2}, {}, latency_ms=10)
        stats = analytics.get_module_stats("m", period="hour")
        assert stats["unique_inputs"] == 2

    def test_module_stats_total_tokens(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10, tokens_used=100)
        analytics.log_call("m", {}, {}, latency_ms=10, tokens_used=200)
        stats = analytics.get_module_stats("m", period="hour")
        assert stats["total_tokens"] == 300


# ---------------------------------------------------------------------------
# get_hourly_breakdown
# ---------------------------------------------------------------------------


class TestGetHourlyBreakdown:
    """Tests for hourly breakdown reporting."""

    def test_empty_returns_empty_list(self, analytics: AgentAnalytics) -> None:
        result = analytics.get_hourly_breakdown(hours=24)
        assert result == []

    def test_breakdown_contains_expected_keys(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=100)
        result = analytics.get_hourly_breakdown(hours=1)
        assert len(result) >= 1
        row = result[0]
        assert "hour" in row
        assert "total_calls" in row
        assert "avg_latency_ms" in row
        assert "success_count" in row
        assert "total_tokens" in row

    def test_breakdown_counts_recent_calls(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=50)
        analytics.log_call("m", {}, {}, latency_ms=150)
        result = analytics.get_hourly_breakdown(hours=1)
        total = sum(row["total_calls"] for row in result)
        assert total == 2


# ---------------------------------------------------------------------------
# get_module_breakdown
# ---------------------------------------------------------------------------


class TestGetModuleBreakdown:
    """Tests for module-level breakdown reporting."""

    def test_empty_returns_empty_list(self, analytics: AgentAnalytics) -> None:
        result = analytics.get_module_breakdown(period="day")
        assert result == []

    def test_breakdown_lists_all_modules(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("triage", {}, {}, latency_ms=100)
        analytics.log_call("decompose", {}, {}, latency_ms=200)
        analytics.log_call("summary", {}, {}, latency_ms=50)
        result = analytics.get_module_breakdown(period="hour")
        module_names = {row["module_name"] for row in result}
        assert "triage" in module_names
        assert "decompose" in module_names
        assert "summary" in module_names

    def test_breakdown_ordered_by_total_desc(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("rare", {}, {}, latency_ms=10)
        for _ in range(3):
            analytics.log_call("common", {}, {}, latency_ms=10)
        result = analytics.get_module_breakdown(period="hour")
        assert result[0]["module_name"] == "common"

    def test_breakdown_row_structure(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=100)
        result = analytics.get_module_breakdown(period="hour")
        row = result[0]
        for key in ("module_name", "total_calls", "avg_latency_ms", "success_rate", "total_tokens"):
            assert key in row


# ---------------------------------------------------------------------------
# get_recent_errors
# ---------------------------------------------------------------------------


class TestGetRecentErrors:
    """Tests for the recent errors report."""

    def test_no_errors_returns_empty(self, analytics: AgentAnalytics) -> None:
        assert analytics.get_recent_errors(limit=5) == []

    def test_success_calls_not_included(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10, success=True)
        assert analytics.get_recent_errors() == []

    def test_error_message_captured(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10, success=False, error_message="boom")
        errors = analytics.get_recent_errors()
        assert errors[0]["error_message"] == "boom"

    def test_limit_respected(self, analytics: AgentAnalytics) -> None:
        for i in range(10):
            analytics.log_call(
                "m", {"i": i}, {}, latency_ms=10, success=False, error_message=f"err{i}"
            )
        errors = analytics.get_recent_errors(limit=3)
        assert len(errors) == 3

    def test_ordered_most_recent_first(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("a", {}, {}, latency_ms=10, success=False, error_message="first")
        time.sleep(0.01)
        analytics.log_call("b", {}, {}, latency_ms=10, success=False, error_message="second")
        errors = analytics.get_recent_errors()
        assert errors[0]["error_message"] == "second"


# ---------------------------------------------------------------------------
# cleanup_old_data
# ---------------------------------------------------------------------------


class TestCleanupOldData:
    """Tests for the TTL cleanup method."""

    def test_cleanup_removes_old_rows(self, tmp_path: Path) -> None:
        import sqlite3

        db_path = str(tmp_path / "cleanup.db")
        fresh = AgentAnalytics(db_path=db_path)

        # Insert a 40-day-old row directly
        old_ts = (datetime.now() - timedelta(days=40)).isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO agent_calls
                (timestamp, module_name, input_hash, output_hash, latency_ms, tokens_used, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (old_ts, "triage", "xxx", "yyy", 10, 0, True),
            )

        deleted = fresh.cleanup_old_data(days=30)
        assert deleted == 1
        assert fresh.get_stats(period="week")["total_calls"] == 0

    def test_cleanup_keeps_recent_rows(self, analytics: AgentAnalytics) -> None:
        analytics.log_call("m", {}, {}, latency_ms=10)
        deleted = analytics.cleanup_old_data(days=30)
        assert deleted == 0
        assert analytics.get_stats(period="hour")["total_calls"] == 1

    def test_cleanup_returns_zero_when_nothing_to_delete(self, analytics: AgentAnalytics) -> None:
        deleted = analytics.cleanup_old_data(days=7)
        assert deleted == 0
