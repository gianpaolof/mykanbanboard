"""Tests for ProactiveSuggester's rule-based (non-LLM) methods.

The three methods under test have no LLM dependency:
  - quick_analysis(tickets, columns): pure rule-based checks
  - _normalize_suggestion(suggestion): normalises a single suggestion dict
  - _parse_text_suggestions(text): parses plain-text suggestions

Tests call the REAL functions without mocking LLM calls.
"""

import pytest

from src.agent.suggester import ProactiveSuggester


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def suggester() -> ProactiveSuggester:
    """Real ProactiveSuggester instance (no LLM initialised)."""
    return ProactiveSuggester()


@pytest.fixture
def base_columns() -> list[dict]:
    return [
        {"id": "col-1", "name": "Todo"},
        {"id": "col-2", "name": "In Progress"},
        {"id": "col-3", "name": "Done"},
    ]


# ---------------------------------------------------------------------------
# quick_analysis
# ---------------------------------------------------------------------------


class TestQuickAnalysis:
    """Tests for rule-based quick_analysis."""

    def test_empty_board_returns_no_suggestions(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        result = suggester.quick_analysis(tickets=[], columns=base_columns)
        assert result == []

    def test_overloaded_column_detected(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"Ticket {i}", "labels": ["bug"], "priority": "medium"}
            for i in range(11)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "overloaded_column" in types

    def test_overloaded_column_message_contains_count(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-2", "title": f"T{i}", "labels": ["bug"], "priority": "low"}
            for i in range(12)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        overloaded = [s for s in result if s["type"] == "overloaded_column"]
        assert len(overloaded) == 1
        assert "12" in overloaded[0]["message"]

    def test_no_overloaded_column_at_exactly_ten(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"T{i}", "labels": ["bug"], "priority": "low"}
            for i in range(10)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "overloaded_column" not in types

    def test_missing_labels_detected(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        # 4 unlabelled tickets → triggers missing_labels suggestion
        tickets = [
            {"column_id": "col-1", "title": f"T{i}", "labels": None, "priority": "low"}
            for i in range(4)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "missing_labels" in types

    def test_missing_labels_not_triggered_with_three_or_fewer(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"T{i}", "labels": None, "priority": "low"}
            for i in range(3)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "missing_labels" not in types

    def test_priority_imbalance_detected(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"Critical {i}", "labels": ["bug"], "priority": "critical"}
            for i in range(6)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "priority_imbalance" in types

    def test_priority_imbalance_not_triggered_at_five(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"Critical {i}", "labels": ["bug"], "priority": "critical"}
            for i in range(5)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        types = [s["type"] for s in result]
        assert "priority_imbalance" not in types

    def test_max_five_suggestions_returned(
        self, suggester: ProactiveSuggester
    ) -> None:
        # Build a board that triggers all three rule types many times
        many_columns = [{"id": f"col-{i}", "name": f"Column {i}"} for i in range(5)]
        tickets = (
            [
                {"column_id": f"col-{c}", "title": f"T{i}", "labels": None, "priority": "critical"}
                for c in range(5)
                for i in range(11)
            ]
        )
        result = suggester.quick_analysis(tickets=tickets, columns=many_columns)
        assert len(result) <= 5

    def test_suggestion_structure_complete(
        self, suggester: ProactiveSuggester, base_columns: list[dict]
    ) -> None:
        tickets = [
            {"column_id": "col-1", "title": f"T{i}", "labels": None, "priority": "low"}
            for i in range(4)
        ]
        result = suggester.quick_analysis(tickets=tickets, columns=base_columns)
        for s in result:
            assert "type" in s
            assert "message" in s
            assert "action" in s
            assert "priority" in s


# ---------------------------------------------------------------------------
# _normalize_suggestion
# ---------------------------------------------------------------------------


class TestNormalizeSuggestion:
    """Tests for _normalize_suggestion."""

    def test_valid_suggestion_unchanged(self, suggester: ProactiveSuggester) -> None:
        raw = {
            "type": "overloaded_column",
            "message": "Column has too many tickets",
            "action": "Archive old tickets",
            "priority": "high",
            "column_id": "col-1",
        }
        result = suggester._normalize_suggestion(raw)
        assert result["type"] == "overloaded_column"
        assert result["priority"] == "high"
        assert result["message"] == "Column has too many tickets"

    def test_unknown_type_defaults_to_stale_ticket(self, suggester: ProactiveSuggester) -> None:
        raw = {"type": "weird_type", "message": "Something odd", "priority": "low"}
        result = suggester._normalize_suggestion(raw)
        assert result["type"] == "stale_ticket"

    def test_unknown_priority_defaults_to_medium(self, suggester: ProactiveSuggester) -> None:
        raw = {"type": "stale_ticket", "message": "Old ticket", "priority": "urgent"}
        result = suggester._normalize_suggestion(raw)
        assert result["priority"] == "medium"

    def test_missing_message_defaults_to_review(self, suggester: ProactiveSuggester) -> None:
        raw = {"type": "stale_ticket", "priority": "low"}
        result = suggester._normalize_suggestion(raw)
        assert result["message"] == "Review this item"

    def test_missing_action_defaults_to_empty_string(self, suggester: ProactiveSuggester) -> None:
        raw = {"type": "stale_ticket", "message": "Some message", "priority": "low"}
        result = suggester._normalize_suggestion(raw)
        assert result["action"] == ""

    def test_type_space_converted_to_underscore(self, suggester: ProactiveSuggester) -> None:
        raw = {"type": "stale ticket", "message": "Old one", "priority": "medium"}
        result = suggester._normalize_suggestion(raw)
        # "stale ticket" → "stale_ticket" which IS a valid type
        assert result["type"] == "stale_ticket"

    def test_priority_uppercased_lowercased_and_accepted(self, suggester: ProactiveSuggester) -> None:
        # The implementation does .lower() before checking PRIORITIES,
        # so "HIGH" → "high" which IS valid and is preserved.
        raw = {"type": "overloaded_column", "message": "msg", "priority": "HIGH"}
        result = suggester._normalize_suggestion(raw)
        assert result["priority"] == "high"

    def test_all_valid_types_preserved(self, suggester: ProactiveSuggester) -> None:
        for stype in ProactiveSuggester.SUGGESTION_TYPES:
            raw = {"type": stype, "message": "msg", "priority": "low"}
            result = suggester._normalize_suggestion(raw)
            assert result["type"] == stype

    def test_ticket_id_and_column_id_propagated(self, suggester: ProactiveSuggester) -> None:
        raw = {
            "type": "stale_ticket",
            "message": "Stale",
            "priority": "low",
            "ticket_id": "t-99",
            "column_id": "col-3",
        }
        result = suggester._normalize_suggestion(raw)
        assert result["ticket_id"] == "t-99"
        assert result["column_id"] == "col-3"


# ---------------------------------------------------------------------------
# _parse_text_suggestions
# ---------------------------------------------------------------------------


class TestParseTextSuggestions:
    """Tests for _parse_text_suggestions (fallback plain-text parser)."""

    def test_empty_text_returns_empty_list(self, suggester: ProactiveSuggester) -> None:
        result = suggester._parse_text_suggestions("")
        assert result == []

    def test_comment_lines_ignored(self, suggester: ProactiveSuggester) -> None:
        text = "# This is a comment\n# Another comment"
        result = suggester._parse_text_suggestions(text)
        assert result == []

    def test_type_keyword_recognised(self, suggester: ProactiveSuggester) -> None:
        text = "There is a stale ticket in the backlog column"
        result = suggester._parse_text_suggestions(text)
        assert len(result) == 1
        assert result[0]["type"] == "stale_ticket"

    def test_overloaded_column_keyword_recognised(self, suggester: ProactiveSuggester) -> None:
        text = "The overloaded column has too many tickets"
        result = suggester._parse_text_suggestions(text)
        assert result[0]["type"] == "overloaded_column"

    def test_generic_long_line_becomes_stale_ticket(self, suggester: ProactiveSuggester) -> None:
        text = "This is a generic suggestion that does not match any known type at all."
        result = suggester._parse_text_suggestions(text)
        assert len(result) == 1
        assert result[0]["type"] == "stale_ticket"
        assert result[0]["priority"] == "low"

    def test_short_lines_ignored(self, suggester: ProactiveSuggester) -> None:
        text = "Ok\nYes\nNo"
        result = suggester._parse_text_suggestions(text)
        # All lines <= 10 chars → ignored
        assert result == []

    def test_max_five_suggestions_from_text(self, suggester: ProactiveSuggester) -> None:
        lines = "\n".join(
            [f"This is a stale ticket suggestion number {i} in the list" for i in range(10)]
        )
        result = suggester._parse_text_suggestions(lines)
        assert len(result) <= 5

    def test_default_priority_is_medium_for_typed(self, suggester: ProactiveSuggester) -> None:
        text = "The missing labels on tickets should be fixed"
        result = suggester._parse_text_suggestions(text)
        if result:
            assert result[0]["priority"] == "medium"
