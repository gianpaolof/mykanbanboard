"""Tests for DSPy 3.x compatibility shims.

These tests verify that the compatibility layer in modules.py works correctly
for both DSPy 2.x and 3.x, particularly around assertions and suggestions.
"""

import pytest
import dspy
import logging

# Import the compatibility shims (they're applied on module load)
from src.agent.modules import _dspy_assert, VALID_PRIORITIES, VALID_EFFORTS


class TestDSpyAssertShim:
    """Test _dspy_assert() compatibility shim."""

    def test_assert_passes_when_condition_true(self):
        """Assert should pass silently when condition is True."""
        # Should not raise
        _dspy_assert(True, "This should not raise")
        dspy.Assert(True, "This should also not raise")

    def test_assert_raises_when_condition_false(self):
        """Assert should raise AssertionError when condition is False."""
        with pytest.raises(AssertionError, match="Test failure message"):
            _dspy_assert(False, "Test failure message")

        with pytest.raises(AssertionError, match="Another test failure"):
            dspy.Assert(False, "Another test failure")

    def test_assert_with_valid_priority(self):
        """Assert should pass for valid priority values."""
        priority = "high"
        dspy.Assert(
            priority in VALID_PRIORITIES,
            f"Priority must be one of {VALID_PRIORITIES}",
        )

    def test_assert_with_invalid_priority(self):
        """Assert should fail for invalid priority values."""
        priority = "urgent"  # Invalid value
        with pytest.raises(AssertionError, match="Priority must be one of"):
            dspy.Assert(
                priority in VALID_PRIORITIES,
                f"Priority must be one of {VALID_PRIORITIES}",
            )

    def test_assert_with_valid_effort(self):
        """Assert should pass for valid effort values."""
        effort = "m"
        dspy.Assert(
            effort in VALID_EFFORTS,
            f"Effort must be one of {VALID_EFFORTS}",
        )

    def test_assert_with_invalid_effort(self):
        """Assert should fail for invalid effort values."""
        effort = "huge"  # Invalid value
        with pytest.raises(AssertionError, match="Effort must be one of"):
            dspy.Assert(
                effort in VALID_EFFORTS,
                f"Effort must be one of {VALID_EFFORTS}",
            )


class TestDSpySuggestShim:
    """Test _dspy_suggest() compatibility shim."""

    def test_suggest_logs_warning_when_condition_false(self, caplog):
        """Suggest should log warning when condition is False, but not raise."""
        with caplog.at_level(logging.WARNING):
            dspy.Suggest(False, "This is a suggestion")

        # Should have logged warning
        assert "This is a suggestion" in caplog.text

    def test_suggest_silent_when_condition_true(self, caplog):
        """Suggest should be silent when condition is True."""
        with caplog.at_level(logging.WARNING):
            dspy.Suggest(True, "This should not be logged")

        # Should not have logged anything
        assert "This should not be logged" not in caplog.text

    def test_suggest_reasoning_length(self, caplog):
        """Test reasoning length suggestion (soft constraint)."""
        reasoning = "Too short"  # Less than 20 chars
        with caplog.at_level(logging.WARNING):
            dspy.Suggest(
                len(reasoning) >= 20,
                "Reasoning should be at least 20 characters for clarity",
            )

        assert "Reasoning should be at least 20 characters" in caplog.text

    def test_suggest_label_count(self, caplog):
        """Test label count suggestion (soft constraint)."""
        labels = ["label1", "label2", "label3", "label4"]  # More than 3
        with caplog.at_level(logging.WARNING):
            dspy.Suggest(
                len(labels) <= 3,
                "Suggest limiting to 3 labels for better organization",
            )

        assert "Suggest limiting to 3 labels" in caplog.text


class TestDSpyCompatibilityIntegration:
    """Integration tests for DSPy compatibility across versions."""

    def test_assert_and_suggest_together(self, caplog):
        """Test using both assert and suggest in validation logic."""
        priority = "high"
        labels = ["bug", "auth", "urgent", "critical"]  # 4 labels (too many)
        reasoning = "Short"  # Too short

        # Hard constraint (must pass)
        dspy.Assert(priority in VALID_PRIORITIES, f"Invalid priority: {priority}")

        # Soft constraints (log warnings but don't fail)
        with caplog.at_level(logging.WARNING):
            dspy.Suggest(len(labels) <= 3, "Consider reducing labels to 3 or fewer")
            dspy.Suggest(len(reasoning) >= 20, "Reasoning should be more detailed")

        # Verify warnings were logged
        assert "Consider reducing labels" in caplog.text
        assert "Reasoning should be more detailed" in caplog.text

    def test_validation_with_all_invalid(self):
        """Test that invalid values fail hard assertions."""
        priority = "urgent"  # Invalid
        effort = "huge"  # Invalid

        # Should raise for priority
        with pytest.raises(AssertionError):
            dspy.Assert(priority in VALID_PRIORITIES, "Invalid priority")

        # Should raise for effort
        with pytest.raises(AssertionError):
            dspy.Assert(effort in VALID_EFFORTS, "Invalid effort")

    def test_validation_with_all_valid(self):
        """Test that valid values pass all checks."""
        priority = "critical"
        effort = "xl"
        labels = ["bug", "urgent"]
        reasoning = "This is a critical bug affecting production users"

        # All assertions should pass
        dspy.Assert(priority in VALID_PRIORITIES, "Invalid priority")
        dspy.Assert(effort in VALID_EFFORTS, "Invalid effort")
        dspy.Suggest(len(labels) <= 3, "Too many labels")
        dspy.Suggest(len(reasoning) >= 20, "Reasoning too short")

        # No exceptions raised = success
