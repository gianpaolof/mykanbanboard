"""Integration tests for /api/decompose endpoint.

KEY: The route calls `basic_decompose(title=..., description=..., context=...)`
via __call__, not .forward(). Mocks must use `mock_class.return_value.return_value`
and NOT `mock_instance.forward = Mock(...)`.

Also: use plain objects with concrete attribute values to avoid extract_value
treating attributes as callable Mocks.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _decompose_result(
    subtasks: list | None = None,
    dependencies: list | None = None,
    reasoning: str = "Breaking down authentication system into logical phases.",
) -> object:
    """Return a plain object compatible with extract_value."""
    class _Pred:
        pass

    p = _Pred()
    p.subtasks = subtasks if subtasks is not None else [
        {"title": "Setup OAuth provider", "description": "Configure OAuth", "effort": "s"},
        {"title": "Create user model", "description": "Database schema", "effort": "s"},
        {"title": "Implement auth endpoints", "description": "API routes", "effort": "m"},
        {"title": "Add auth middleware", "description": "Security layer", "effort": "s"},
        {"title": "Write tests", "description": "Test coverage", "effort": "m"},
    ]
    p.dependencies = dependencies if dependencies is not None else [(2, 1), (3, 1), (4, 2)]
    p.reasoning = reasoning
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDecomposeEndpoint:
    """Test /api/decompose endpoint."""

    def test_decompose_with_valid_task(self, client, sample_complex_task):
        """POST /api/decompose with valid task should return 200."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result()

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()

        assert "subtasks" in data
        assert "dependencies" in data
        assert isinstance(data["subtasks"], list)
        assert len(data["subtasks"]) >= 2

    def test_decompose_timeout(self, client, sample_complex_task):
        """Decompose timeout should return 504."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Decompose timed out after 12 seconds. Please try again.",
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()

    def test_decompose_invalid_subtask_count_returns_200(self, client, sample_complex_task):
        """A single subtask response is accepted (route has no minimum enforcement)."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=[{"title": "Only one", "description": "Bad", "effort": "m"}],
                dependencies=[],
                reasoning="Too few subtasks.",
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        # Route does not enforce minimum count; Pydantic just validates types
        assert response.status_code == 200

    def test_decompose_returns_subtask_fields(self, client, sample_complex_task):
        """Each subtask should have title, description, and effort fields."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result()

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()

        for subtask in data["subtasks"]:
            assert "title" in subtask
            assert "description" in subtask
            assert "effort" in subtask
            assert subtask["effort"] in ["xs", "s", "m", "l", "xl"]

    def test_decompose_module_exception_returns_500(self, client, sample_complex_task):
        """Module exception should return 500."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.side_effect = RuntimeError("DSPy error")

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 500
        assert "decomposition failed" in response.json()["detail"].lower()
