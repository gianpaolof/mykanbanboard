"""Edge-case integration tests for /api/decompose endpoint.

Covers scenarios not tested in test_decompose_api.py:
- Basic vs context-aware module selection
- Subtask effort normalisation
- String subtask format (non-dict)
- Dependencies parsing
- Missing optional fields
- Invalid inputs / error responses
- Module called with correct args

IMPORTANT: The route calls extract_value() on result.subtasks, result.dependencies,
and result.reasoning. Use plain objects with concrete attribute values.
Also: extract_value() unwraps single-element lists into scalars.
"""

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decompose_result(
    subtasks: list | None = None,
    dependencies: list | None = None,
    reasoning: str = "Decomposed into logical steps.",
) -> object:
    """Return a plain object compatible with extract_value."""
    class _Pred:
        pass

    p = _Pred()
    p.subtasks = subtasks if subtasks is not None else [
        {"title": "Step A", "description": "First step", "effort": "s"},
        {"title": "Step B", "description": "Second step", "effort": "m"},
    ]
    p.dependencies = dependencies if dependencies is not None else []
    p.reasoning = reasoning
    return p


def _valid_subtask(title: str = "Do something", effort: str = "m") -> dict:
    return {"title": title, "description": f"Description for {title}", "effort": effort}


# ---------------------------------------------------------------------------
# Tests - Module Selection
# ---------------------------------------------------------------------------

class TestDecomposeModuleSelection:
    """Verify correct module used based on context presence."""

    def test_basic_module_used_without_context(self, client, sample_complex_task):
        """Without context, DecomposeModule (basic) should be used."""
        with patch("src.api.routes.DecomposeModule") as mock_basic, \
             patch("src.api.routes.ContextAwareDecomposeModule") as mock_ctx:
            mock_basic.return_value.return_value = _decompose_result()

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        mock_basic.assert_called_once()
        mock_ctx.assert_not_called()

    def test_context_aware_module_used_with_board_context(self, client, sample_complex_task):
        """With board_context, ContextAwareDecomposeModule should be used."""
        board_context = {
            "board_id": "board-1",
            "board_name": "My Board",
            "columns": [{"id": "col-1", "name": "Todo"}],
            "labels": ["bug"],
            "total_tickets": 3,
        }

        with patch("src.api.routes.ContextAwareDecomposeModule") as mock_ctx, \
             patch("src.api.routes.DecomposeModule") as mock_basic:
            mock_ctx.return_value.return_value = _decompose_result()

            request_data = {**sample_complex_task, "board_context": board_context}
            response = client.post("/api/decompose", json=request_data)

        assert response.status_code == 200
        mock_ctx.assert_called_once()
        mock_basic.assert_not_called()

    def test_context_aware_module_used_with_project_context(self, client, sample_complex_task):
        """With project_context, ContextAwareDecomposeModule should be used."""
        project_context = {
            "tech_stack": ["Python", "FastAPI"],
            "conventions": "Use REST conventions",
            "architecture": "monolith",
        }

        with patch("src.api.routes.ContextAwareDecomposeModule") as mock_ctx, \
             patch("src.api.routes.DecomposeModule") as mock_basic:
            mock_ctx.return_value.return_value = _decompose_result()

            request_data = {**sample_complex_task, "project_context": project_context}
            response = client.post("/api/decompose", json=request_data)

        assert response.status_code == 200
        mock_ctx.assert_called_once()
        mock_basic.assert_not_called()


# ---------------------------------------------------------------------------
# Tests - Subtask Effort Normalisation
# ---------------------------------------------------------------------------

class TestDecomposeEffortNormalisation:
    """Verify effort values are normalised to valid xs/s/m/l/xl."""

    @pytest.mark.parametrize("raw_effort,expected", [
        ("small", "s"),
        ("medium", "m"),
        ("large", "l"),
        ("extra-small", "xs"),
        ("extra-large", "xl"),
        ("1", "xs"),
        ("2", "s"),
        ("3", "m"),
        ("4", "l"),
        ("5", "xl"),
    ])
    def test_effort_normalised_from_long_form(
        self, client, sample_complex_task, raw_effort, expected
    ):
        """Long-form effort strings should be normalised to short form."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=[
                    {"title": "Task A", "description": "desc", "effort": raw_effort},
                    {"title": "Task B", "description": "desc", "effort": "m"},
                ],
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()
        # First subtask should have normalised effort
        assert data["subtasks"][0]["effort"] == expected

    def test_subtask_without_effort_defaults_to_m(self, client, sample_complex_task):
        """Subtask without effort field should default to 'm'."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=[
                    {"title": "Task A", "description": "desc"},  # No effort
                    {"title": "Task B", "description": "desc"},  # No effort
                ],
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()
        for subtask in data["subtasks"]:
            assert subtask["effort"] == "m"


# ---------------------------------------------------------------------------
# Tests - String Subtask Handling
# ---------------------------------------------------------------------------

class TestDecomposeStringSubtasks:
    """Verify string subtasks (non-dict format) are handled."""

    def test_string_subtasks_are_converted_to_dict(self, client, sample_complex_task):
        """String subtasks should be converted to {title, description, effort} dicts."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=["Setup database", "Create API endpoints"],
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["subtasks"], list)
        assert len(data["subtasks"]) == 2
        # Each should be a dict with required fields
        for subtask in data["subtasks"]:
            assert "title" in subtask
            assert "effort" in subtask


# ---------------------------------------------------------------------------
# Tests - Request Validation
# ---------------------------------------------------------------------------

class TestDecomposeRequestValidation:
    """Validate input field requirements."""

    def test_decompose_missing_ticket_id_returns_422(self, client):
        """Missing ticket_id should return 422."""
        response = client.post(
            "/api/decompose",
            json={"title": "Big task", "description": "desc"},
        )
        assert response.status_code == 422

    def test_decompose_missing_title_returns_422(self, client):
        """Missing title should return 422."""
        response = client.post(
            "/api/decompose",
            json={"ticket_id": "t-1", "description": "desc"},
        )
        assert response.status_code == 422

    def test_decompose_empty_title_returns_422(self, client):
        """Empty title (violates min_length=1) should return 422."""
        response = client.post(
            "/api/decompose",
            json={"ticket_id": "t-1", "title": "", "description": "desc"},
        )
        assert response.status_code == 422

    def test_decompose_without_description_succeeds(self, client):
        """Description is optional; omitting it should not cause 422."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result()

            response = client.post(
                "/api/decompose",
                json={"ticket_id": "t-1", "title": "Some task"},
            )

        assert response.status_code == 200

    def test_decompose_with_context_string(self, client, sample_complex_task):
        """Optional context string should be accepted."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result()

            request_data = {
                **sample_complex_task,
                "context": "We use React and TypeScript for the frontend",
            }
            response = client.post("/api/decompose", json=request_data)

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests - Dependencies and Error Handling
# ---------------------------------------------------------------------------

class TestDecomposeResponseAndErrors:
    """Test response structure and error handling."""

    def test_decompose_returns_dependencies_as_tuples(self, client, sample_complex_task):
        """Dependencies should be returned as list of [int, int] pairs."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=[
                    _valid_subtask("Task A"),
                    _valid_subtask("Task B"),
                    _valid_subtask("Task C"),
                ],
                dependencies=[[1, 0], [2, 1]],
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()
        assert data["dependencies"] == [[1, 0], [2, 1]]

    def test_decompose_response_has_reasoning(self, client, sample_complex_task):
        """Response should always contain a reasoning string."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                reasoning="Breaking into steps allows parallel work.",
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["reasoning"], str)
        assert "parallel" in data["reasoning"]

    def test_decompose_module_exception_returns_500(self, client, sample_complex_task):
        """Module exception should return 500 with descriptive message."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.side_effect = RuntimeError("DSPy error")

            response = client.post("/api/decompose", json=sample_complex_task)

        assert response.status_code == 500
        assert "decomposition failed" in response.json()["detail"].lower()

    def test_decompose_empty_subtasks_list(self, client, sample_complex_task):
        """Empty subtasks list should return 200 (route does not enforce minimum)."""
        with patch("src.api.routes.DecomposeModule") as mock_class:
            mock_class.return_value.return_value = _decompose_result(
                subtasks=[],
                dependencies=[],
                reasoning="No subtasks generated.",
            )

            response = client.post("/api/decompose", json=sample_complex_task)

        # Route does not enforce minimum subtask count at serialization level
        assert response.status_code == 200
        assert response.json()["subtasks"] == []
