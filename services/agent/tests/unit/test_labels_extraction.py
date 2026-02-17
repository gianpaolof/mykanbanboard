import pytest
from unittest.mock import MagicMock, Mock
from src.api.routes import extract_labels

class TestExtractLabels:
    """Unit tests for extract_labels() helper function."""

    def test_extracts_simple_list(self):
        """Should extract clean list of strings."""
        mock = MagicMock()
        mock.labels = ["bug", "frontend", "urgent"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "frontend", "urgent"]

    def test_calls_bound_method(self):
        """Should call bound method if labels is callable."""
        mock = MagicMock()
        mock.labels = lambda: ["bug", "auth"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth"]

    def test_filters_bound_method_strings(self):
        """Should filter out '<bound method' strings."""
        mock = MagicMock()
        mock.labels = [
            "<bound method Example.labels of Prediction(",
            "bug",
            "auth"
        ]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth"]
        assert "<bound method" not in str(result)

    def test_filters_reasoning_fragments(self):
        """Should filter out reasoning text fragments."""
        mock = MagicMock()
        mock.labels = [
            "bug",
            "This is because the authentication flow is broken",
            "auth",
            "We should fix this immediately"
        ]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth"]

    def test_filters_long_strings(self):
        """Should filter strings longer than 30 chars."""
        mock = MagicMock()
        mock.labels = [
            "bug",
            "this-is-a-very-long-label-that-should-be-filtered-out",
            "auth"
        ]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth"]

    def test_handles_comma_separated_string(self):
        """Should split comma-separated string into list."""
        mock = MagicMock()
        mock.labels = "bug, frontend, urgent"
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "frontend", "urgent"]

    def test_handles_single_string(self):
        """Should wrap single string in list."""
        mock = MagicMock()
        mock.labels = "bug"
        result = extract_labels(mock, 'labels')
        assert result == ["bug"]

    def test_handles_empty_list(self):
        """Should return empty list for empty input."""
        mock = MagicMock()
        mock.labels = []
        result = extract_labels(mock, 'labels')
        assert result == []

    def test_handles_none(self):
        """Should return empty list for None."""
        mock = MagicMock()
        mock.labels = None
        result = extract_labels(mock, 'labels')
        assert result == []

    def test_limits_to_five_labels(self):
        """Should limit output to 5 labels max."""
        mock = MagicMock()
        mock.labels = ["a", "b", "c", "d", "e", "f", "g"]
        result = extract_labels(mock, 'labels')
        assert len(result) == 5
        assert result == ["a", "b", "c", "d", "e"]

    def test_unwraps_single_element_list(self):
        """Should handle single-element list correctly."""
        mock = MagicMock()
        mock.labels = ["bug"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug"]

    def test_handles_mixed_types(self):
        """Should filter non-string types."""
        mock = MagicMock()
        mock.labels = ["bug", 123, None, "auth", {"key": "value"}]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth"]

    def test_removes_duplicates(self):
        """Should remove duplicate labels (case-sensitive)."""
        mock = MagicMock()
        mock.labels = ["bug", "auth", "bug", "bug", "urgent"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth", "urgent"]
        assert len(result) == 3

    def test_preserves_case(self):
        """Should preserve original case (no normalization)."""
        mock = MagicMock()
        mock.labels = ["BUG", "Bug", "bug"]
        result = extract_labels(mock, 'labels')
        # All three are different labels (case-sensitive)
        assert len(result) == 3
        assert "BUG" in result
        assert "Bug" in result
        assert "bug" in result

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        mock = MagicMock()
        mock.labels = ["  bug  ", " auth", "urgent "]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth", "urgent"]

    def test_filters_empty_strings(self):
        """Should filter out empty strings and whitespace-only."""
        mock = MagicMock()
        mock.labels = ["bug", "", "auth", "   ", "urgent", "\t\n"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "auth", "urgent"]

    def test_handles_unicode_labels(self):
        """Should handle Unicode labels correctly."""
        mock = MagicMock()
        mock.labels = ["バグ", "bug", "ошибка", "🐛"]
        result = extract_labels(mock, 'labels')
        assert len(result) == 4
        assert "バグ" in result
        assert "ошибка" in result
        assert "🐛" in result

    def test_filters_html_content(self):
        """Should filter labels containing HTML/script tags."""
        mock = MagicMock()
        mock.labels = ["<script>alert('xss')</script>", "bug", "<b>auth</b>", "urgent"]
        result = extract_labels(mock, 'labels')
        assert result == ["bug", "urgent"]
        assert "<script>" not in str(result)
        assert "<b>" not in str(result)

    def test_handles_exception_in_callable(self):
        """Should return empty list if calling bound method raises exception."""
        mock = MagicMock()
        mock.labels = Mock(side_effect=RuntimeError("DSPy error"))
        result = extract_labels(mock, 'labels')
        assert result == []
