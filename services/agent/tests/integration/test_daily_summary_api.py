"""Integration tests for /api/daily-summary endpoint.

Tests the full daily-summary flow: FastAPI -> DailySummaryModule -> response.
Uses mocked LLM to avoid API costs during testing.

IMPORTANT: extract_value() in routes.py unwraps single-element lists into scalars.
To avoid validation errors, we always use multi-element lists or empty lists
when mocking module return values that the route passes through extract_value.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ticket_data(
    ticket_id: str = "ticket-1",
    title: str = "Fix login bug",
    status: str = "in_progress",
    priority: str = "high",
) -> dict:
    """Return a minimal valid TicketData dict."""
    return {
        "id": ticket_id,
        "title": title,
        "description": "Description",
        "status": status,
        "priority": priority,
        "labels": [],
        "column_id": "col-1",
    }


def _make_summary_result(
    greeting: str = "Good morning!",
    focus_today: list | None = None,
    blockers: list | None = None,
    quick_wins: list | None = None,
) -> object:
    """Return a simple object with concrete attribute values.

    Uses a plain object (not Mock) to avoid extract_value treating
    attributes as callable Mocks.

    NOTE: extract_value() unwraps single-element lists into scalars,
    so multi-element lists or empty lists are safe; single-element
    lists would cause a string to be passed where a list is expected.
    """
    class _Result:
        pass

    r = _Result()
    r.greeting = greeting
    # Use multi-element lists (or empty) to avoid extract_value single-element unwrap
    r.focus_today = focus_today if focus_today is not None else ["Focus item A", "Focus item B"]
    r.blockers = blockers if blockers is not None else []
    r.quick_wins = quick_wins if quick_wins is not None else []
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDailySummaryEndpoint:
    """Test POST /api/daily-summary."""

    def test_daily_summary_empty_board_returns_200(self, client, mock_daily_summary_module, mock_chromadb):
        """Empty board (no tickets) should return 200 with valid structure."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Good morning! Your board is empty.",
            focus_today=[],
            blockers=[],
            quick_wins=[],
        )

        response = client.post("/api/daily-summary", json={})

        assert response.status_code == 200
        data = response.json()
        assert "greeting" in data
        assert "focus_today" in data
        assert "blockers" in data
        assert "quick_wins" in data
        assert isinstance(data["focus_today"], list)
        assert isinstance(data["blockers"], list)
        assert isinstance(data["quick_wins"], list)

    def test_daily_summary_with_in_progress_tickets(self, client, mock_daily_summary_module, mock_chromadb):
        """In-progress tickets should be accepted and module called."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Good morning! You have 2 tickets in progress.",
            focus_today=["Fix login bug", "Implement dark mode"],
            blockers=[],
            quick_wins=[],
        )

        request_data = {
            "in_progress": [
                _make_ticket_data("t-1", "Fix login bug", "in_progress", "high"),
                _make_ticket_data("t-2", "Implement dark mode", "in_progress", "medium"),
            ],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data["focus_today"]) <= 3  # Route caps at 3

    def test_daily_summary_with_blocked_tickets(self, client, mock_daily_summary_module, mock_chromadb):
        """Blocked tickets should be accepted and produce a valid response."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Good morning!",
            focus_today=["Resolve blockers", "Check PR status"],
            blockers=["API integration blocked", "Waiting on design"],
            quick_wins=[],
        )

        request_data = {
            "blocked": [
                _make_ticket_data("t-blocked", "API integration", "blocked", "high"),
            ],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["blockers"], list)

    def test_daily_summary_with_all_ticket_categories(self, client, mock_daily_summary_module, mock_chromadb):
        """All ticket categories should be accepted without error."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Good morning! Productive day ahead.",
            focus_today=["Fix login bug", "Code review"],
            blockers=["Waiting for design review", "External API down"],
            quick_wins=["Update changelog", "Close stale PR"],
        )

        request_data = {
            "in_progress": [_make_ticket_data("t-1", "Fix login bug", "in_progress")],
            "blocked": [_make_ticket_data("t-2", "Design review", "blocked")],
            "due_soon": [_make_ticket_data("t-3", "Release v1.0", "todo")],
            "recently_completed": [_make_ticket_data("t-4", "Setup CI", "done")],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["greeting"] == "Good morning! Productive day ahead."

    def test_daily_summary_focus_today_capped_at_3(self, client, mock_daily_summary_module, mock_chromadb):
        """focus_today should be capped at 3 items by the route."""
        mock_daily_summary_module.return_value = _make_summary_result(
            focus_today=["Task 1", "Task 2", "Task 3", "Task 4", "Task 5"],
        )

        request_data = {
            "in_progress": [
                _make_ticket_data(f"t-{i}", f"Ticket {i}", "in_progress")
                for i in range(5)
            ],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200
        data = response.json()
        # Route slices focus_today[:3]
        assert len(data["focus_today"]) <= 3

    def test_daily_summary_with_board_context(self, client, mock_daily_summary_module, mock_chromadb):
        """Board context should be accepted and not cause errors."""
        mock_daily_summary_module.return_value = _make_summary_result()

        request_data = {
            "in_progress": [_make_ticket_data()],
            "board_context": {
                "board_id": "board-123",
                "board_name": "My Board",
                "columns": [{"id": "col-1", "name": "In Progress", "position": 0}],
                "labels": ["bug", "feature"],
                "total_tickets": 10,
            },
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200

    def test_daily_summary_module_called_once(self, client, mock_daily_summary_module, mock_chromadb):
        """DailySummaryModule should be instantiated and called exactly once."""
        mock_daily_summary_module.return_value = _make_summary_result()

        request_data = {
            "in_progress": [_make_ticket_data("ticket-abc-123", "Fix bug", "in_progress")],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 200
        mock_daily_summary_module.assert_called_once()

    def test_daily_summary_module_failure_returns_500(self, client, mock_daily_summary_module, mock_chromadb):
        """Module exception should return 500 with descriptive detail."""
        mock_daily_summary_module.side_effect = RuntimeError("LLM call failed")

        response = client.post("/api/daily-summary", json={})

        assert response.status_code == 500
        assert "daily summary failed" in response.json()["detail"].lower()

    def test_daily_summary_invalid_ticket_missing_id(self, client, mock_chromadb):
        """Ticket data with missing required 'id' field should return 422."""
        request_data = {
            "in_progress": [
                {
                    # Missing 'id' field
                    "title": "Fix login bug",
                    "status": "in_progress",
                }
            ],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 422

    def test_daily_summary_invalid_ticket_missing_title(self, client, mock_chromadb):
        """Ticket data with missing 'title' field should return 422."""
        request_data = {
            "in_progress": [
                {
                    "id": "t-1",
                    # Missing 'title' field
                    "status": "in_progress",
                }
            ],
        }

        response = client.post("/api/daily-summary", json=request_data)

        assert response.status_code == 422

    def test_daily_summary_response_greeting_is_string(self, client, mock_daily_summary_module, mock_chromadb):
        """Greeting field in response should be a non-empty string."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Good morning team!",
            focus_today=[],
            blockers=[],
            quick_wins=[],
        )

        response = client.post("/api/daily-summary", json={})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["greeting"], str)
        assert len(data["greeting"]) > 0

    def test_daily_summary_quick_wins_returned(self, client, mock_daily_summary_module, mock_chromadb):
        """quick_wins field should be present as a list."""
        mock_daily_summary_module.return_value = _make_summary_result(
            greeting="Morning!",
            focus_today=[],
            blockers=[],
            quick_wins=["Close stale PR", "Update README"],
        )

        response = client.post("/api/daily-summary", json={})

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["quick_wins"], list)
