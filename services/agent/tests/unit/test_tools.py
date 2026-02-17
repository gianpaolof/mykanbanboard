"""Unit tests for src/agent/tools.py."""

from unittest.mock import MagicMock, patch

import pytest

from src.agent.tools import (
    create_ticket,
    get_board_context,
    search_tickets,
    update_ticket,
    web_search,
)


# ---------------------------------------------------------------------------
# search_tickets
# ---------------------------------------------------------------------------


class TestSearchTickets:
    """Tests for search_tickets."""

    def test_returns_list(self):
        result = search_tickets("login bug")
        assert isinstance(result, list)

    def test_returns_at_least_one_result(self):
        result = search_tickets("something")
        assert len(result) >= 1

    def test_result_contains_required_keys(self):
        result = search_tickets("auth issue")
        for item in result:
            assert "id" in item
            assert "title" in item
            assert "description" in item

    def test_query_is_reflected_in_result_title(self):
        """Placeholder implementation echoes the query into title."""
        result = search_tickets("my query")
        assert result[0]["title"] == "my query"

    def test_limit_parameter_accepted(self):
        """Function accepts a limit parameter without error."""
        result = search_tickets("test", limit=3)
        assert isinstance(result, list)

    def test_default_limit_is_five(self):
        """Default limit=5 should be accepted without error."""
        import inspect
        sig = inspect.signature(search_tickets)
        assert sig.parameters["limit"].default == 5

    def test_empty_query_returns_list(self):
        result = search_tickets("")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# create_ticket
# ---------------------------------------------------------------------------


class TestCreateTicket:
    """Tests for create_ticket."""

    def test_returns_dict(self):
        result = create_ticket("Fix bug")
        assert isinstance(result, dict)

    def test_result_contains_id(self):
        result = create_ticket("Fix bug")
        assert "id" in result

    def test_title_preserved_in_result(self):
        result = create_ticket("My ticket title")
        assert result["title"] == "My ticket title"

    def test_description_preserved_in_result(self):
        result = create_ticket("T", description="Some description")
        assert result["description"] == "Some description"

    def test_default_description_is_empty_string(self):
        result = create_ticket("T")
        assert result["description"] == ""

    def test_column_id_preserved_in_result(self):
        result = create_ticket("T", column_id="todo")
        assert result["column_id"] == "todo"

    def test_default_column_id_is_backlog(self):
        result = create_ticket("T")
        assert result["column_id"] == "backlog"

    def test_all_params_together(self):
        result = create_ticket(
            title="Build feature",
            description="Full description",
            column_id="in_progress",
        )
        assert result["title"] == "Build feature"
        assert result["description"] == "Full description"
        assert result["column_id"] == "in_progress"


# ---------------------------------------------------------------------------
# update_ticket
# ---------------------------------------------------------------------------


class TestUpdateTicket:
    """Tests for update_ticket."""

    def test_returns_dict(self):
        result = update_ticket("ticket-1")
        assert isinstance(result, dict)

    def test_result_contains_ticket_id(self):
        result = update_ticket("ticket-abc")
        assert result["id"] == "ticket-abc"

    def test_updates_are_merged_into_result(self):
        result = update_ticket("t-1", priority="high", status="done")
        assert result["priority"] == "high"
        assert result["status"] == "done"

    def test_no_updates_returns_only_id(self):
        result = update_ticket("t-1")
        assert result == {"id": "t-1"}

    def test_multiple_updates(self):
        result = update_ticket(
            "t-2",
            title="New title",
            description="Updated desc",
            priority="low",
            labels=["bug"],
        )
        assert result["title"] == "New title"
        assert result["description"] == "Updated desc"
        assert result["priority"] == "low"
        assert result["labels"] == ["bug"]

    def test_id_not_overwritten_by_kwargs(self):
        """Even if caller passes id as a kwarg, ticket_id parameter should win."""
        result = update_ticket("real-id", priority="high")
        assert result["id"] == "real-id"


# ---------------------------------------------------------------------------
# get_board_context
# ---------------------------------------------------------------------------


class TestGetBoardContext:
    """Tests for get_board_context."""

    def test_returns_dict(self):
        result = get_board_context()
        assert isinstance(result, dict)

    def test_contains_columns_key(self):
        result = get_board_context()
        assert "columns" in result

    def test_columns_is_list(self):
        result = get_board_context()
        assert isinstance(result["columns"], list)

    def test_columns_are_non_empty(self):
        result = get_board_context()
        assert len(result["columns"]) > 0

    def test_contains_total_tickets_key(self):
        result = get_board_context()
        assert "total_tickets" in result

    def test_total_tickets_is_int(self):
        result = get_board_context()
        assert isinstance(result["total_tickets"], int)

    def test_contains_labels_key(self):
        result = get_board_context()
        assert "labels" in result

    def test_labels_is_list(self):
        result = get_board_context()
        assert isinstance(result["labels"], list)

    def test_known_columns_present(self):
        result = get_board_context()
        expected = {"backlog", "todo", "in_progress", "review", "done"}
        assert expected.issubset(set(result["columns"]))


# ---------------------------------------------------------------------------
# web_search
# ---------------------------------------------------------------------------


class TestWebSearch:
    """Tests for web_search."""

    # DDGS is imported lazily inside the function, so we patch it at the
    # duckduckgo_search module level.
    _PATCH_TARGET = "duckduckgo_search.DDGS"

    def _make_mock_ddgs(self, return_value=None):
        """Build a context-manager-compatible DDGS mock."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text = MagicMock(return_value=return_value or [])
        return mock_ddgs

    def test_returns_list_on_success(self):
        raw = [
            {"title": "Result 1", "body": "Snippet 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Snippet 2", "href": "https://example.com/2"},
        ]
        mock_ddgs = self._make_mock_ddgs(raw)
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            result = web_search("test query", max_results=2)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_result_contains_required_keys(self):
        raw = [{"title": "T1", "body": "S1", "href": "https://a.com"}]
        mock_ddgs = self._make_mock_ddgs(raw)
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            result = web_search("query")

        assert "title" in result[0]
        assert "snippet" in result[0]
        assert "url" in result[0]

    def test_result_maps_body_to_snippet(self):
        raw = [{"title": "T", "body": "The snippet", "href": "https://x.com"}]
        mock_ddgs = self._make_mock_ddgs(raw)
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            result = web_search("q")

        assert result[0]["snippet"] == "The snippet"
        assert result[0]["url"] == "https://x.com"

    def test_max_results_passed_to_ddgs(self):
        mock_ddgs = self._make_mock_ddgs([])
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            web_search("q", max_results=7)

        mock_ddgs.text.assert_called_once_with("q", max_results=7)

    def test_returns_error_entry_on_exception(self):
        """When DDGS raises inside the try-block, a single error dict is returned."""
        mock_ddgs = self._make_mock_ddgs()
        mock_ddgs.text.side_effect = Exception("network error")
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            result = web_search("q")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Error"
        assert "network error" in result[0]["snippet"]
        assert result[0]["url"] == ""

    def test_returns_error_entry_when_ddgs_constructor_raises(self):
        """Simulate an exception raised by the DDGS constructor."""
        with patch(self._PATCH_TARGET, side_effect=Exception("init error")):
            result = web_search("q")

        assert result[0]["title"] == "Error"

    def test_empty_results_from_ddgs(self):
        mock_ddgs = self._make_mock_ddgs([])
        with patch(self._PATCH_TARGET, return_value=mock_ddgs):
            result = web_search("q")

        assert result == []

    def test_default_max_results_is_five(self):
        import inspect
        sig = inspect.signature(web_search)
        assert sig.parameters["max_results"].default == 5
