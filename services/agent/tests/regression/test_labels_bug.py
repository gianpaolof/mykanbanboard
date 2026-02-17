import pytest
from unittest.mock import MagicMock
from src.api.routes import extract_labels

class TestLabelsRegressionBug:
    """Regression tests for specific labels bug scenarios."""

    def test_live_api_bug_scenario(self):
        """
        Regression test for live API bug where labels returned:
        ["<bound method Example.labels of Prediction(", "...fragments...", "bug", "auth"]
        """
        mock = MagicMock()
        mock.labels = [
            "<bound method Example.labels of Prediction(",
            "reasoning text fragments here",
            "bug",
            "auth"
        ]
        result = extract_labels(mock, 'labels')

        # Should filter to clean labels only
        assert result == ["bug", "auth"]
        assert len(result) == 2
        assert all(isinstance(label, str) for label in result)
        assert all('<bound' not in label for label in result)

    def test_dspy_version_conflict_scenario(self):
        """
        Regression test for DSPy version conflict causing bound method returns.
        Simulates what happens when both dspy-ai 2.x and dspy 3.x are installed.
        """
        mock = MagicMock()
        # Simulate bound method attribute
        mock.labels = MagicMock(return_value=["bug", "frontend"])

        result = extract_labels(mock, 'labels')
        assert result == ["bug", "frontend"]

    def test_gpt4o_mini_output_parsing_issue(self):
        """
        Regression test for gpt-4o-mini mixing reasoning with labels.
        LLM sometimes outputs: "bug, auth, this is because..."
        """
        mock = MagicMock()
        mock.labels = "bug, auth, this is because the user authentication flow is compromised"

        result = extract_labels(mock, 'labels')
        # Should intelligently split and filter
        assert "bug" in result
        assert "auth" in result
        # Long reasoning fragments should be filtered
        assert not any(len(label) > 30 for label in result)

    def test_combined_corruption_scenario(self):
        """
        Regression test for multiple corruption types simultaneously:
        bound methods + reasoning fragments + HTML + duplicates.
        """
        mock = MagicMock()
        mock.labels = [
            "<bound method Example.labels of Prediction(",
            "bug",
            "This is because the authentication system is compromised",
            "<script>alert('xss')</script>",
            "auth",
            "bug",  # Duplicate
            "urgent"
        ]
        result = extract_labels(mock, 'labels')

        # Should filter to clean, unique labels only
        assert result == ["bug", "auth", "urgent"]
        assert len(result) == 3
        assert all('<' not in label for label in result)
        assert all(len(label) <= 30 for label in result)
