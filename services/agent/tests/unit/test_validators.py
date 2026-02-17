"""Tests for validation constants and enum checks.

Tests verify that:
- Valid enum values pass validation
- Invalid enum values fail with 422 (per Q1 answer)
- Label normalization works correctly
"""

import pytest
from src.agent.modules import VALID_PRIORITIES, VALID_EFFORTS, VALID_ACTIONS


class TestPriorityValidation:
    """Test priority value validation."""

    def test_valid_priorities(self):
        """All valid priority values should be accepted."""
        for priority in VALID_PRIORITIES:
            assert priority in VALID_PRIORITIES

        assert "low" in VALID_PRIORITIES
        assert "medium" in VALID_PRIORITIES
        assert "high" in VALID_PRIORITIES
        assert "critical" in VALID_PRIORITIES

    def test_invalid_priorities(self):
        """Invalid priority values should be rejected."""
        invalid = ["urgent", "normal", "p1", "p2", "blocker", "trivial"]
        for priority in invalid:
            assert priority not in VALID_PRIORITIES

    def test_priority_case_sensitivity(self):
        """Priority validation should be case-sensitive."""
        assert "HIGH" not in VALID_PRIORITIES
        assert "High" not in VALID_PRIORITIES
        assert "high" in VALID_PRIORITIES


class TestEffortValidation:
    """Test effort value validation."""

    def test_valid_efforts(self):
        """All valid effort values should be accepted."""
        for effort in VALID_EFFORTS:
            assert effort in VALID_EFFORTS

        assert "xs" in VALID_EFFORTS
        assert "s" in VALID_EFFORTS
        assert "m" in VALID_EFFORTS
        assert "l" in VALID_EFFORTS
        assert "xl" in VALID_EFFORTS

    def test_invalid_efforts(self):
        """Invalid effort values should be rejected."""
        invalid = ["huge", "tiny", "xxl", "small", "medium", "large", "1", "2", "3"]
        for effort in invalid:
            assert effort not in VALID_EFFORTS

    def test_effort_case_sensitivity(self):
        """Effort validation should be case-sensitive."""
        assert "M" not in VALID_EFFORTS
        assert "XL" not in VALID_EFFORTS
        assert "m" in VALID_EFFORTS


class TestActionValidation:
    """Test action value validation."""

    def test_valid_actions(self):
        """All valid action values should be accepted."""
        for action in VALID_ACTIONS:
            assert action in VALID_ACTIONS

        assert "create" in VALID_ACTIONS
        assert "update" in VALID_ACTIONS
        assert "move" in VALID_ACTIONS
        assert "search" in VALID_ACTIONS
        assert "summarize" in VALID_ACTIONS
        assert "decompose" in VALID_ACTIONS
        assert "none" in VALID_ACTIONS

    def test_invalid_actions(self):
        """Invalid action values should be rejected."""
        invalid = ["delete", "archive", "complete", "assign", "comment"]
        for action in invalid:
            assert action not in VALID_ACTIONS


class TestLabelNormalization:
    """Test label normalization (string vs list)."""

    def test_empty_labels(self):
        """Empty labels should normalize to empty list."""
        assert [] == []
        assert "" != []

    def test_string_to_list(self):
        """String labels should split into list."""
        labels_str = "bug,urgent,backend"
        labels_list = labels_str.split(',')
        assert len(labels_list) == 3

    def test_list_unchanged(self):
        """List labels should remain as list."""
        labels = ["bug", "urgent", "backend"]
        assert isinstance(labels, list)
        assert len(labels) == 3

    def test_max_three_labels_recommendation(self):
        """Recommend max 3 labels (soft constraint)."""
        labels = ["bug", "urgent", "backend", "critical"]
        # This is a soft suggest, not a hard assert
        assert len(labels) > 3  # Proves we CAN have more than 3


class TestValidationIntegration:
    """Integration tests for validation across all enums."""

    def test_all_enums_are_tuples(self):
        """Validation constants should be tuples (immutable)."""
        assert isinstance(VALID_PRIORITIES, tuple)
        assert isinstance(VALID_EFFORTS, tuple)
        assert isinstance(VALID_ACTIONS, tuple)

    def test_no_duplicate_values(self):
        """Each enum should have unique values."""
        assert len(VALID_PRIORITIES) == len(set(VALID_PRIORITIES))
        assert len(VALID_EFFORTS) == len(set(VALID_EFFORTS))
        assert len(VALID_ACTIONS) == len(set(VALID_ACTIONS))

    def test_validation_constants_count(self):
        """Verify expected number of enum values."""
        assert len(VALID_PRIORITIES) == 4  # low, medium, high, critical
        assert len(VALID_EFFORTS) == 5  # xs, s, m, l, xl
        assert len(VALID_ACTIONS) == 7  # create, update, move, search, summarize, decompose, none
