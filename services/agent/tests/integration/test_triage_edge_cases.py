"""Edge-case integration tests for /api/triage endpoint.

Covers scenarios not tested in test_triage_api.py and test_triage_labels.py:
- Basic module path (no context) vs context-aware path
- Module called with correct args
- Effort/priority edge cases
- Large existing_labels list
- Unicode content
- Health endpoint sanity

IMPORTANT: safe_extract() reads from obj.__dict__['_store'] first, then
obj.__dict__, then getattr. We set attributes directly on a plain object
so that getattr works correctly and values are not callables.
"""

import pytest
from unittest.mock import Mock, patch


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _triage_result(
    priority: str = "medium",
    labels: list | None = None,
    effort: str = "m",
    reasoning: str = "Test reasoning for triage result.",
) -> object:
    """Return a plain object suitable for safe_extract / extract_labels."""
    class _Pred:
        pass

    p = _Pred()
    p.priority = priority
    # Multi-element or empty lists avoid extract_value single-elem unwrap
    p.labels = labels if labels is not None else []
    p.effort_estimate = effort
    p.reasoning = reasoning
    return p


# ---------------------------------------------------------------------------
# Tests - Basic Triage Path (no context)
# ---------------------------------------------------------------------------

class TestTriageBasicPath:
    """Tests for the basic (non-context-aware) triage code path."""

    def test_triage_basic_path_used_without_context(self, client, sample_ticket):
        """When no project/board_context, TriageModule (basic) should be used."""
        with patch("src.api.routes.TriageModule") as mock_basic, \
             patch("src.api.routes.ContextAwareTriageModule") as mock_ctx:
            mock_basic.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "auth"],
                effort="m",
                reasoning="Basic triage reasoning.",
            )

            response = client.post("/api/triage", json=sample_ticket)

            assert response.status_code == 200
            # TriageModule should be used, NOT context-aware
            mock_basic.assert_called_once()
            mock_ctx.assert_not_called()

    def test_triage_module_called_with_title_and_description(self, client, sample_ticket):
        """TriageModule should be called with title, description, existing_labels."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug"],
                effort="l",
                reasoning="Safari login issue is complex.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        instance = mock_class.return_value
        instance.assert_called_once()
        call_kwargs = instance.call_args[1]
        assert call_kwargs["title"] == sample_ticket["title"]
        assert call_kwargs["description"] == sample_ticket["description"]
        assert call_kwargs["existing_labels"] == sample_ticket["existing_labels"]

    def test_triage_context_aware_path_used_with_project_context(
        self, client, sample_ticket
    ):
        """When project_context provided, ContextAwareTriageModule should be used.

        ProjectContext model expects:
          tech_stack: list[str], conventions: Optional[str],
          priority_rules: Optional[dict], architecture: Optional[str]
        """
        project_context = {
            "tech_stack": ["Python", "FastAPI", "React"],
            "conventions": "Use conventional commits",
            "priority_rules": {"urgent": "critical"},
            "architecture": "microservices",
        }

        with patch("src.api.routes.ContextAwareTriageModule") as mock_ctx, \
             patch("src.api.routes.TriageModule") as mock_basic:
            mock_ctx.return_value.return_value = _triage_result(
                priority="critical",
                labels=["bug", "urgent"],
                effort="m",
                reasoning="Context-aware reasoning.",
            )

            request_data = {**sample_ticket, "project_context": project_context}
            response = client.post("/api/triage", json=request_data)

        assert response.status_code == 200
        mock_ctx.assert_called_once()
        mock_basic.assert_not_called()

    def test_triage_context_aware_path_used_with_board_context(
        self, client, sample_ticket
    ):
        """When board_context provided, ContextAwareTriageModule should be used.

        BoardContext model expects:
          board_id: str, board_name: str, columns: list[dict],
          labels: list[str], total_tickets: int
        """
        board_context = {
            "board_id": "board-1",
            "board_name": "My Board",
            "columns": [{"id": "col-1", "name": "Todo"}],
            "labels": ["bug", "feature"],
            "total_tickets": 5,
        }

        with patch("src.api.routes.ContextAwareTriageModule") as mock_ctx, \
             patch("src.api.routes.TriageModule") as mock_basic:
            mock_ctx.return_value.return_value = _triage_result(
                priority="medium",
                labels=["feature"],
                effort="s",
                reasoning="Board context reasoning.",
            )

            request_data = {**sample_ticket, "board_context": board_context}
            response = client.post("/api/triage", json=request_data)

        assert response.status_code == 200
        mock_ctx.assert_called_once()
        mock_basic.assert_not_called()


# ---------------------------------------------------------------------------
# Tests - All Valid Priority / Effort Combinations
# ---------------------------------------------------------------------------

class TestTriageValidValues:
    """Verify all valid enum values are accepted in the response."""

    @pytest.mark.parametrize("priority", ["low", "medium", "high", "critical"])
    def test_triage_all_valid_priorities(self, client, sample_ticket, priority):
        """All valid priority values should pass Pydantic validation."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority=priority,
                labels=["bug", "test"],
                effort="m",
                reasoning="Priority test.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        assert response.json()["priority"] == priority

    @pytest.mark.parametrize("effort", ["xs", "s", "m", "l", "xl"])
    def test_triage_all_valid_efforts(self, client, sample_ticket, effort):
        """All valid effort values should pass Pydantic validation."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=["bug", "test"],
                effort=effort,
                reasoning="Effort test.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        assert response.json()["effort"] == effort


# ---------------------------------------------------------------------------
# Tests - Input Edge Cases
# ---------------------------------------------------------------------------

class TestTriageInputEdgeCases:
    """Test input validation edge cases."""

    def test_triage_with_empty_existing_labels(self, client):
        """Empty existing_labels list should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="low",
                labels=[],
                effort="xs",
                reasoning="No existing labels to guide.",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "test-empty-labels",
                    "title": "Simple ticket",
                    "description": "Basic description",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200

    def test_triage_with_large_existing_labels_list(self, client):
        """Large existing_labels list (25 items) should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=["bug", "frontend"],
                effort="m",
                reasoning="Selected from many labels.",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "test-many-labels",
                    "title": "Feature request",
                    "description": "A new feature",
                    "existing_labels": [f"label-{i}" for i in range(25)],
                },
            )

        assert response.status_code == 200

    def test_triage_with_unicode_title(self, client):
        """Unicode content in title should be handled correctly."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="high",
                labels=["bug", "i18n"],
                effort="m",
                reasoning="Unicode ticket.",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "test-unicode",
                    "title": "Corregir error en página de inicio de sesión",
                    "description": "Los usuarios de habla hispana no pueden iniciar sesión",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200

    def test_triage_with_missing_ticket_id_returns_422(self, client):
        """Missing required ticket_id should return 422."""
        response = client.post(
            "/api/triage",
            json={
                "title": "Some ticket",
                "description": "Some description",
            },
        )
        assert response.status_code == 422

    def test_triage_with_empty_title_returns_422(self, client):
        """Empty title (violates min_length=1) should return 422."""
        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "test-123",
                "title": "",
                "description": "Some description",
            },
        )
        assert response.status_code == 422

    def test_triage_module_exception_returns_500(self, client, sample_ticket):
        """Module raising an exception should return 500."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.side_effect = RuntimeError("DSPy internal error")

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 500
        assert "triage failed" in response.json()["detail"].lower()

    def test_triage_response_reasoning_is_string(self, client, sample_ticket):
        """Reasoning field in response should always be a string."""
        with patch("src.api.routes.TriageModule") as mock_class:
            mock_class.return_value.return_value = _triage_result(
                priority="medium",
                labels=["bug"],
                effort="s",
                reasoning="Clear reasoning about ticket classification.",
            )

            response = client.post("/api/triage", json=sample_ticket)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["reasoning"], str)
