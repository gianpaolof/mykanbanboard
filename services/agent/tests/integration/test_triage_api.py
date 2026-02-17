"""Integration tests for /api/triage endpoint.

Tests the full triage flow: FastAPI -> DSPy -> validation -> response.
Uses mocked LLM to avoid API costs during testing.

KEY: The route calls `basic_triage(title=..., ...)` directly via __call__,
not .forward(). So mocks must use `mock_instance.return_value = result`
(which configures __call__) and NOT `mock_instance.forward = Mock(...)`.

Also: use plain objects with concrete attribute values (not Mock objects)
to avoid extract_value / safe_extract treating attributes as callables.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _triage_result(
    priority: str = "high",
    labels: list | None = None,
    effort: str = "m",
    reasoning: str = "Detailed reasoning about the ticket.",
) -> object:
    """Return a plain object mimicking a DSPy Prediction for triage."""
    class _Pred:
        pass

    p = _Pred()
    p.priority = priority
    p.labels = labels if labels is not None else []
    p.effort_estimate = effort
    p.reasoning = reasoning
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTriageEndpoint:
    """Test /api/triage endpoint with valid inputs."""

    def test_triage_with_valid_ticket(self, client, sample_ticket):
        """POST /api/triage with valid ticket should return 200."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "auth"],
                effort="m",
                reasoning="Login issues on Safari indicate browser compatibility problem.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "priority" in data
        assert "labels" in data
        assert "effort" in data
        assert "reasoning" in data

        # Verify valid values
        assert data["priority"] in ["low", "medium", "high", "critical"]
        assert data["effort"] in ["xs", "s", "m", "l", "xl"]
        assert isinstance(data["labels"], list)

    def test_triage_returns_correct_format(self, client, sample_ticket):
        """Response should match expected schema with correct field values."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "urgent"],
                effort="m",
                reasoning="Login bug affecting Safari users requires immediate attention.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()

        assert data["priority"] == "high"
        assert "bug" in data["labels"]
        assert data["effort"] == "m"
        assert len(data["reasoning"]) >= 20


class TestTriageTimeout:
    """Test timeout behavior for triage endpoint."""

    @pytest.mark.slow
    def test_triage_timeout_returns_504(self, client, sample_ticket):
        """Triage that exceeds timeout should return 504."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Triage timed out after 12 seconds. Please try again.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()

    def test_triage_timeout_message_clear(self, client, sample_ticket):
        """Timeout error message should be clear and actionable."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Triage timed out after 12 seconds. Please try again.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 504
        detail = response.json()["detail"]
        assert "Triage" in detail
        assert "12 seconds" in detail
        assert "try again" in detail.lower()


class TestTriageValidation:
    """Test validation and error handling."""

    def test_triage_with_missing_title(self, client):
        """Missing title should return 422."""
        invalid_ticket = {
            "ticket_id": "test-123",
            # Missing title
            "description": "Some description",
            "existing_labels": [],
        }

        response = client.post("/api/triage", json=invalid_ticket)
        assert response.status_code == 422

    def test_triage_with_missing_description_succeeds(self, client):
        """Description has a default value so omitting it should succeed."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=[],
                effort="s",
                reasoning="No description provided, basic triage applied.",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "test-123",
                    "title": "Some title",
                    "existing_labels": [],
                },
            )

        # description has default="" in TriageRequest, so omitting is allowed
        assert response.status_code == 200

    def test_triage_with_invalid_priority_from_dspy(self, client, sample_ticket):
        """DSPy returning invalid priority should return 422 or 500."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="urgent",  # Invalid - not in Literal["low","medium","high","critical"]
                labels=["bug"],
                effort="m",
                reasoning="This is urgent.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        # Should return 422 (Pydantic validation) or 500
        assert response.status_code in [422, 500]


class TestTriageWithContext:
    """Test context-aware triage functionality."""

    def test_triage_with_board_context(self, client, sample_ticket):
        """Triage with board_context should use ContextAwareTriageModule."""
        board_context = {
            "board_id": "board-1",
            "board_name": "My Board",
            "columns": [],
            "labels": ["bug", "backend", "frontend", "feature", "auth", "urgent"],
            "total_tickets": 10,
        }

        with patch("src.api.routes.ContextAwareTriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "backend"],
                effort="m",
                reasoning="Using existing board labels for consistency.",
            )

            request_data = {**sample_ticket, "board_context": board_context}
            response = client.post("/api/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Labels returned should be valid strings
        for label in data["labels"]:
            assert isinstance(label, str)

    def test_triage_with_project_context(self, client, sample_ticket):
        """Triage with project_context should use ContextAwareTriageModule."""
        project_context = {
            "tech_stack": ["Python", "FastAPI"],
            "conventions": "Use conventional commits",
            "priority_rules": {"urgent": "critical"},
        }

        with patch("src.api.routes.ContextAwareTriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="critical",
                labels=["bug", "urgent"],
                effort="m",
                reasoning="Urgent label triggers critical priority per project rules.",
            )

            request_data = {**sample_ticket, "project_context": project_context}
            response = client.post("/api/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Should respect project priority rules
        if "urgent" in data["labels"]:
            assert data["priority"] == "critical"


class TestTriageEmptyChromaDB:
    """Test triage with empty ChromaDB (graceful degradation)."""

    def test_triage_with_empty_chromadb(self, client, sample_ticket, mock_chromadb):
        """Empty ChromaDB should gracefully degrade to basic module."""
        mock_chromadb.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=["bug"],
                effort="m",
                reasoning="No similar tickets found, using basic triage.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        # Should succeed even with empty ChromaDB
        assert response.status_code == 200


class TestTriageNewLabels:
    """Test that new labels are allowed."""

    def test_triage_can_suggest_new_labels(self, client, sample_ticket):
        """Triage should be able to suggest labels not in existing_labels."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "safari", "compatibility"],
                effort="m",
                reasoning="Suggesting new labels for better categorization.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()

        # Should include new labels
        assert "safari" in data["labels"] or "compatibility" in data["labels"]
