"""Tests for DSPy value extraction and normalization helpers.

These tests call the actual production functions from src.api.routes:
- extract_value()
- safe_extract()
- unwrap_single_element_list()

The functions handle DSPy 3.x quirks:
- Single-element list unwrapping
- Bound method detection and calling
- Fallback to _store dict for DSPy Prediction objects
"""

import pytest
from unittest.mock import Mock

from src.api.routes import extract_value, safe_extract, unwrap_single_element_list


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakePrediction:
    """Simulates a DSPy Prediction object with direct attribute storage."""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return f"Prediction({self.__dict__})"


class FakePredictionWithStore:
    """Simulates a DSPy 3.x Prediction object that stores values in _store."""

    def __init__(self, **kwargs):
        object.__setattr__(self, "_store", dict(kwargs))

    def __getattr__(self, name):
        store = object.__getattribute__(self, "_store")
        if name in store:
            return store[name]
        raise AttributeError(name)

    def __repr__(self):
        store = object.__getattribute__(self, "_store")
        return f"Prediction({store})"


# ===========================================================================
# unwrap_single_element_list
# ===========================================================================


class TestUnwrapSingleElementList:
    """Test unwrap_single_element_list() utility."""

    def test_single_element_list_is_unwrapped(self):
        """['low'] should become 'low'."""
        assert unwrap_single_element_list(["low"]) == "low"

    def test_multi_element_list_is_unchanged(self):
        """['bug', 'auth'] should remain a list."""
        result = unwrap_single_element_list(["bug", "auth"])
        assert result == ["bug", "auth"]

    def test_empty_list_is_unchanged(self):
        """[] should remain []."""
        result = unwrap_single_element_list([])
        assert result == []

    def test_plain_string_is_unchanged(self):
        """A bare string should pass through without modification."""
        assert unwrap_single_element_list("high") == "high"

    def test_integer_is_unchanged(self):
        """An integer should pass through without modification."""
        assert unwrap_single_element_list(42) == 42

    def test_none_is_unchanged(self):
        """None should pass through without modification."""
        assert unwrap_single_element_list(None) is None

    def test_single_element_nested_list(self):
        """[['bug', 'auth']] should unwrap to ['bug', 'auth']."""
        result = unwrap_single_element_list([["bug", "auth"]])
        assert result == ["bug", "auth"]

    def test_single_element_dict(self):
        """[{'key': 'val'}] should unwrap to the dict."""
        result = unwrap_single_element_list([{"key": "val"}])
        assert result == {"key": "val"}


# ===========================================================================
# extract_value
# ===========================================================================


class TestExtractValuePrimitives:
    """Test extract_value() with primitive/non-DSPy inputs."""

    def test_none_returns_none(self):
        """None input should return None."""
        assert extract_value(None) is None

    def test_string_returned_as_is(self):
        """Plain strings should pass through unchanged."""
        assert extract_value("high") == "high"

    def test_integer_returned_as_is(self):
        """Integers should pass through unchanged."""
        assert extract_value(7) == 7

    def test_float_returned_as_is(self):
        """Floats should pass through unchanged."""
        assert extract_value(0.9) == 0.9

    def test_dict_is_processed(self):
        """Dicts should be returned with each value extracted."""
        result = extract_value({"a": "foo", "b": 42})
        assert result == {"a": "foo", "b": 42}

    def test_dict_skips_internal_keys(self):
        """Keys starting with '_' should be excluded from dict extraction."""
        result = extract_value({"priority": "high", "_internal": "skip"})
        assert "priority" in result
        assert "_internal" not in result


class TestExtractValueLists:
    """Test extract_value() list-specific behaviours."""

    def test_multi_element_list_extracted(self):
        """A multi-element list should have each item extracted."""
        result = extract_value(["bug", "auth", "urgent"])
        assert result == ["bug", "auth", "urgent"]

    def test_single_element_list_unwrapped(self):
        """Single-element list ['low'] should unwrap to 'low'."""
        assert extract_value(["low"]) == "low"

    def test_empty_list_stays_empty(self):
        """Empty list should return empty list."""
        result = extract_value([])
        assert result == []

    def test_list_with_none_items(self):
        """None items in a list should each become None after extraction."""
        result = extract_value([None, "bug", None])
        assert result == [None, "bug", None]


class TestExtractValueCallables:
    """Test extract_value() callable handling."""

    def test_callable_is_called_and_result_extracted(self):
        """A callable should be called and its return value extracted."""
        mock = Mock(return_value="high")
        result = extract_value(mock)
        assert result == "high"
        mock.assert_called_once_with()

    def test_callable_returning_none_gives_none(self):
        """A callable returning None should produce None."""
        mock = Mock(return_value=None)
        result = extract_value(mock)
        assert result is None

    def test_callable_raising_exception_returns_none(self):
        """A callable that raises should return None without propagating."""
        mock = Mock(side_effect=RuntimeError("DSPy error"))
        result = extract_value(mock)
        assert result is None


class TestExtractValuePredictionObjects:
    """Test extract_value() with DSPy-like Prediction objects."""

    def test_prediction_with_store_extracts_store(self):
        """Prediction._store dict should be extracted when present."""
        pred = FakePredictionWithStore(priority="critical", effort="xl")
        result = extract_value(pred)
        # The _store dict itself is returned (without the underscore-prefixed key)
        assert isinstance(result, dict)
        assert result.get("priority") == "critical"
        assert result.get("effort") == "xl"

    def test_prediction_without_store_uses_dict(self):
        """Prediction without _store should fall back to __dict__."""
        pred = FakePrediction(priority="high", effort="m")
        result = extract_value(pred)
        # Should return the __dict__ (which has no _store, so it recurses via __dict__)
        assert isinstance(result, dict)

    def test_plain_object_without_prediction_in_name(self):
        """Objects whose class name does NOT contain 'Prediction' are not treated specially."""

        class OrdinaryObject:
            def __init__(self):
                self.value = "hello"

        obj = OrdinaryObject()
        # Non-Prediction objects with no call semantics are returned as-is
        result = extract_value(obj)
        assert result is obj


# ===========================================================================
# safe_extract
# ===========================================================================


class TestSafeExtractFromStore:
    """Test safe_extract() accessing DSPy 3.x _store dict."""

    def test_extracts_from_store_dict(self):
        """Should read value from _store when available."""
        pred = FakePredictionWithStore(priority="medium", effort="s")
        assert safe_extract(pred, "priority") == "medium"
        assert safe_extract(pred, "effort") == "s"

    def test_single_element_list_in_store_is_unwrapped(self):
        """_store value ['high'] should be unwrapped to 'high'."""
        pred = FakePredictionWithStore(priority=["high"])
        result = safe_extract(pred, "priority")
        assert result == "high"

    def test_multi_element_list_in_store_stays_list(self):
        """Multi-element list in _store should not be unwrapped."""
        pred = FakePredictionWithStore(labels=["bug", "auth"])
        result = safe_extract(pred, "labels")
        assert result == ["bug", "auth"]

    def test_missing_key_in_store_uses_default(self):
        """Missing attribute should return the given default."""
        pred = FakePredictionWithStore(priority="high")
        result = safe_extract(pred, "effort", default="m")
        assert result == "m"

    def test_default_is_none_when_not_specified(self):
        """Default should be None when not explicitly provided."""
        pred = FakePredictionWithStore(priority="high")
        result = safe_extract(pred, "nonexistent")
        assert result is None


class TestSafeExtractFromDict:
    """Test safe_extract() falling back to __dict__ access."""

    def test_extracts_plain_attribute(self):
        """Direct attribute on a plain object should be extracted."""
        pred = FakePrediction(priority="low", effort="xs")
        assert safe_extract(pred, "priority") == "low"

    def test_single_element_list_attribute_is_unwrapped(self):
        """['critical'] stored as direct attribute should unwrap to 'critical'."""
        pred = FakePrediction(priority=["critical"])
        result = safe_extract(pred, "priority")
        assert result == "critical"

    def test_callable_attribute_is_skipped(self):
        """Callable attributes should be skipped and default returned."""
        pred = FakePrediction(priority="high")
        pred.effort = lambda: "m"  # Callable attribute
        result = safe_extract(pred, "effort", default="m")
        assert result == "m"  # Default, because callable is skipped

    def test_internal_attribute_skipped_in_dict_branch_but_found_via_getattr(self):
        """The __dict__ branch skips '_' prefixed names, but getattr fallback finds them.

        safe_extract's Method 2 checks 'not attr_name.startswith(_)' before returning,
        so it falls through to Method 3 (getattr) which does NOT have that restriction.
        Therefore the value is ultimately returned.
        """
        pred = FakePrediction()
        pred.__dict__["_internal"] = "secret"
        result = safe_extract(pred, "_internal", default="fallback")
        # getattr fallback returns the value; internal-name restriction is only in __dict__ branch
        assert result == "secret"


class TestSafeExtractEdgeCases:
    """Edge cases for safe_extract()."""

    def test_none_object_raises_or_returns_default(self):
        """Passing None as obj should return default (no crash)."""
        result = safe_extract(None, "priority", default="medium")
        # None has no __dict__ and no _store, so should fall through to default
        assert result == "medium"

    def test_plain_dict_object_uses_getattr_fallback(self):
        """A plain dict has no attribute 'priority', should return default."""
        result = safe_extract({}, "priority", default="low")
        assert result == "low"

    def test_object_with_none_attribute_returns_none(self):
        """When the attribute exists but is None, safe_extract returns None.

        The __dict__ branch (Method 2) returns the value immediately
        when it's non-callable and not '_'-prefixed, even if the value
        is None. None is therefore returned rather than the default.
        """
        pred = FakePrediction(priority=None)
        result = safe_extract(pred, "priority", default="medium")
        assert result is None

    def test_string_value_from_direct_attribute(self):
        """A non-empty string attribute should be returned correctly."""
        pred = FakePrediction(reasoning="This is the reasoning text.")
        result = safe_extract(pred, "reasoning", default="")
        assert result == "This is the reasoning text."

    def test_multi_element_list_from_direct_attribute(self):
        """A multi-element list should not be unwrapped."""
        pred = FakePrediction(labels=["bug", "auth", "urgent"])
        result = safe_extract(pred, "labels", default=[])
        assert result == ["bug", "auth", "urgent"]
