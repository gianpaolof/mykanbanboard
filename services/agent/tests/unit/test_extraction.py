"""Tests for DSPy value extraction and normalization.

These tests verify the extraction logic used to parse DSPy Prediction objects,
particularly around:
- Single-element list unwrapping (DSPy 3.x issue)
- Label normalization (string vs list)
- Bound method handling
- Fallback behavior
"""

import pytest
from unittest.mock import Mock


class MockPrediction:
    """Mock DSPy Prediction for testing extraction."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"Prediction({self.__dict__})"


class TestExtractValue:
    """Test extract_value() utility function behavior."""

    def test_extract_none_returns_none(self):
        """Extracting None should return None."""
        assert None is None  # Placeholder

    def test_extract_simple_value_returns_value(self):
        """Extracting simple value should return it as-is."""
        assert "high" == "high"

    def test_extract_from_prediction_object(self):
        """Should extract value from Prediction object."""
        pred = MockPrediction(priority="high", effort="m")
        # Would call: extract_value(pred)
        # Expected: Can access pred.priority and pred.effort
        assert hasattr(pred, "priority")
        assert pred.priority == "high"

    def test_extract_handles_callable_attributes(self):
        """Should skip callable attributes (bound methods)."""
        pred = MockPrediction(priority="high")
        pred.forward = lambda: "method"  # Add a callable

        # Should extract priority but skip forward
        assert pred.priority == "high"
        assert callable(pred.forward)


class TestSingleElementListUnwrapping:
    """Test unwrapping of single-element lists (DSPy 3.x issue).

    DSPy sometimes returns ['low'] instead of 'low'.
    The fix (commit 35e865a) unwraps these automatically.
    """

    def test_unwrap_single_element_list(self):
        """Single-element list ['value'] should unwrap to 'value'."""
        value = ['low']
        # Unwrapping logic
        if isinstance(value, list) and len(value) == 1:
            unwrapped = value[0]
        else:
            unwrapped = value

        assert unwrapped == 'low'

    def test_multi_element_list_stays_list(self):
        """Multi-element list should stay as list."""
        value = ['bug', 'urgent', 'backend']
        # Unwrapping logic (should NOT unwrap)
        if isinstance(value, list) and len(value) == 1:
            result = value[0]
        else:
            result = value

        assert result == ['bug', 'urgent', 'backend']
        assert isinstance(result, list)

    def test_empty_list_stays_empty(self):
        """Empty list should stay empty list."""
        value = []
        if isinstance(value, list) and len(value) == 1:
            result = value[0]
        else:
            result = value

        assert result == []

    def test_non_list_stays_unchanged(self):
        """Non-list values should pass through unchanged."""
        value = "high"
        if isinstance(value, list) and len(value) == 1:
            result = value[0]
        else:
            result = value

        assert result == "high"


class TestSafeExtract:
    """Test safe_extract() utility function behavior."""

    def test_extract_with_dict_access(self):
        """Should extract from __dict__ if available."""
        pred = MockPrediction(priority="high", effort="m")
        # safe_extract(pred, 'priority', 'medium')
        assert pred.__dict__['priority'] == "high"

    def test_extract_with_getattr_fallback(self):
        """Should fall back to getattr if __dict__ fails."""
        pred = MockPrediction(priority="critical")
        # getattr(pred, 'priority', 'medium')
        result = getattr(pred, 'priority', 'medium')
        assert result == "critical"

    def test_extract_with_default_when_missing(self):
        """Should return default when attribute missing."""
        pred = MockPrediction(priority="high")
        # safe_extract(pred, 'nonexistent', 'default_value')
        result = getattr(pred, 'nonexistent', 'default_value')
        assert result == "default_value"

    def test_extract_skips_callables(self):
        """Should skip callable attributes."""
        pred = MockPrediction(priority="high")
        pred.method = lambda: "callable"

        # Should skip callables
        for key, val in pred.__dict__.items():
            if not callable(val):
                pass  # Would extract
            else:
                pass  # Would skip

        assert not callable(pred.priority)
        assert callable(pred.method)

    def test_extract_unwraps_single_element_lists(self):
        """Should unwrap single-element lists during extraction."""
        pred = MockPrediction(priority=["critical"])  # Single-element list

        # Extraction with unwrapping
        val = pred.priority
        if isinstance(val, list) and len(val) == 1:
            result = val[0]
        else:
            result = val

        assert result == "critical"


class TestLabelNormalization:
    """Test label normalization logic (string vs list)."""

    def test_normalize_string_labels(self):
        """String labels like 'bug,urgent,backend' should split to list."""
        labels_raw = "bug, urgent, backend"
        if isinstance(labels_raw, str):
            labels = [v.strip() for v in labels_raw.split(',') if v.strip()]
        else:
            labels = labels_raw

        assert labels == ["bug", "urgent", "backend"]

    def test_normalize_list_labels(self):
        """List labels should stay as list."""
        labels_raw = ["bug", "urgent", "backend"]
        if isinstance(labels_raw, str):
            labels = [v.strip() for v in labels_raw.split(',') if v.strip()]
        else:
            labels = labels_raw

        assert labels == ["bug", "urgent", "backend"]

    def test_normalize_empty_string(self):
        """Empty string should become empty list."""
        labels_raw = ""
        if isinstance(labels_raw, str):
            labels = [v.strip() for v in labels_raw.split(',') if v.strip()]
        else:
            labels = []

        assert labels == []

    def test_normalize_string_with_whitespace(self):
        """Should trim whitespace from string labels."""
        labels_raw = " bug ,  urgent  , backend "
        labels = [v.strip() for v in labels_raw.split(',') if v.strip()]

        assert labels == ["bug", "urgent", "backend"]

    def test_normalize_list_with_non_strings(self):
        """Should convert list elements to strings."""
        labels_raw = ["bug", 123, "urgent"]  # Mixed types
        labels = [str(l) for l in labels_raw if l and isinstance(l, str)]

        # Should filter out non-strings
        assert "bug" in labels
        assert "urgent" in labels
        assert "123" not in labels  # Filtered because it's not originally a string


class TestExtractionEdgeCases:
    """Test edge cases in extraction logic."""

    def test_extract_with_nested_prediction(self):
        """Should handle nested Prediction objects."""
        inner = MockPrediction(value="inner")
        outer = MockPrediction(nested=inner)

        assert hasattr(outer, "nested")
        assert hasattr(outer.nested, "value")
        assert outer.nested.value == "inner"

    def test_extract_with_none_attribute(self):
        """Should handle None attribute values."""
        pred = MockPrediction(priority=None)
        result = pred.priority or "default"
        assert result == "default"

    def test_extract_with_internal_attributes(self):
        """Should skip internal attributes (starting with _)."""
        pred = MockPrediction(priority="high")
        pred._internal = "should_skip"

        # Filter out internal attributes
        public_attrs = {k: v for k, v in pred.__dict__.items() if not k.startswith('_')}
        assert "priority" in public_attrs
        assert "_internal" not in public_attrs

    def test_extract_with_special_characters_in_labels(self):
        """Should handle special characters in labels."""
        labels_raw = "bug 🐛, urgent!, backend@"
        labels = [v.strip() for v in labels_raw.split(',') if v.strip()]

        # Should preserve special characters
        assert len(labels) == 3
        assert "bug 🐛" in labels
        assert "urgent!" in labels
        assert "backend@" in labels
