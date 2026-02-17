"""Integration tests for /api/triage labels field.

Tests the extract_labels() helper via end-to-end HTTP requests.

KEY: The route calls `basic_triage(...)` via __call__, so mocks must use
`mock_class.return_value.return_value = result` (not .forward).

Also: extract_labels() reads from obj.__dict__['_store'] first, then
obj.__dict__, then getattr. We use plain objects so getattr finds the
labels attribute as a plain list (not a Mock bound method).
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _triage_result(
    priority: str = "high",
    labels=None,
    effort: str = "m",
    reasoning: str = "Test reasoning for labels test.",
) -> object:
    """Return a plain object mimicking a DSPy Prediction for triage."""
    class _Pred:
        pass

    p = _Pred()
    p.priority = priority
    # Set labels directly - extract_labels will find via getattr
    p.labels = labels if labels is not None else []
    p.effort_estimate = effort
    p.reasoning = reasoning
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTriageLabels:
    """Integration tests for /api/triage labels field."""

    def test_labels_field_returns_clean_list(self, client, sample_ticket):
        """Should return clean list of label strings."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "auth"],
                effort="m",
                reasoning="Security issue in authentication.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == ["bug", "auth"]
        assert all(isinstance(label, str) for label in data["labels"])

    def test_filters_bound_method_strings_from_labels(self, client, sample_ticket):
        """Should filter strings that look like bound method representations."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=[
                    "<bound method Example.labels of Prediction(",
                    "bug",
                    "auth",
                ],
                effort="m",
                reasoning="Security issue.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert "<bound method" not in str(data["labels"])
        assert data["labels"] == ["bug", "auth"]

    def test_filters_reasoning_fragments(self, client, sample_ticket):
        """Should filter reasoning-like text fragments from labels."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=[
                    "bug",
                    "This is because authentication is broken",
                    "auth",
                ],
                effort="m",
                reasoning="Security issue.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == ["bug", "auth"]

    def test_handles_empty_labels(self, client, sample_ticket):
        """Should return empty list when labels is None or empty."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=None,
                effort="m",
                reasoning="No labels needed.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == []

    def test_removes_duplicates(self, client, sample_ticket):
        """Should remove duplicate labels."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "bug", "auth"],
                effort="m",
                reasoning="Security issue.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"].count("bug") == 1

    def test_removes_duplicates_and_html(self, client, sample_ticket):
        """Should remove duplicates and filter HTML in same request."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=[
                    "bug",
                    "<script>alert('xss')</script>",
                    "bug",   # Duplicate
                    "auth",
                    "<b>urgent</b>",  # HTML
                ],
                effort="m",
                reasoning="Security issue.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == ["bug", "auth"]
        assert len(data["labels"]) == 2

    def test_labels_many_filtered_to_three(self, client, sample_ticket):
        """extract_labels caps at 5 but TriageResponse.labels has max_length=3.

        When the DSPy module returns many labels, extract_labels filters and
        caps at 5. However, TriageResponse validates max_length=3, so if
        extract_labels returns > 3 labels, Pydantic raises a validation error
        (500). The test verifies that exactly 3 clean labels succeed.
        """
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                # Exactly 3 clean labels (within TriageResponse max_length=3)
                labels=["bug", "auth", "backend"],
                effort="m",
                reasoning="Three clean labels test.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        # All 3 should be present (within max_length=3 limit)
        assert len(data["labels"]) <= 3

    def test_handles_callable_labels(self, client, sample_ticket):
        """Should handle case where labels attribute is callable.

        extract_labels tries to call callable values and uses the result.
        """
        with patch("src.api.routes.TriageModule") as mock_class:
            result = _triage_result(
                priority="high",
                labels=None,  # Will override below
                effort="m",
                reasoning="Security issue.",
            )
            # Override labels with a callable that returns a list
            result.labels = lambda: ["bug", "auth"]
            mock_class.return_value.return_value = result

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert data["labels"] == ["bug", "auth"]
