"""Integration tests for /api/decompose endpoint."""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

pytestmark = pytest.mark.anyio


class TestDecomposeEndpoint:
    """Test /api/decompose endpoint."""

    async def test_decompose_with_valid_task(self, client, sample_complex_task, mock_decompose_response):
        """POST /api/decompose with valid task should return 200."""
        with patch('src.api.routes.DecomposeModule') as mock_module:
            mock_instance = Mock()
            mock_instance.forward = Mock(return_value=mock_decompose_response)
            mock_module.return_value = mock_instance

            response = client.post("/api/decompose", json=sample_complex_task)

            assert response.status_code == 200
            data = response.json()

            assert "subtasks" in data
            assert "dependencies" in data
            assert isinstance(data["subtasks"], list)
            assert len(data["subtasks"]) >= 2

    async def test_decompose_timeout(self, client, sample_complex_task):
        """Decompose timeout should return 504."""
        import asyncio

        with patch('src.api.routes.DecomposeModule') as mock_module:
            async def slow_decompose(*args, **kwargs):
                await asyncio.sleep(15)
                return Mock(subtasks=[], dependencies=[], reasoning="")

            mock_instance = Mock()
            mock_instance.forward = Mock(side_effect=slow_decompose)
            mock_module.return_value = mock_instance

            response = client.post("/api/decompose", json=sample_complex_task)

            assert response.status_code == 504
            assert "timed out" in response.json()["detail"].lower()

    async def test_decompose_invalid_subtask_count(self, client, sample_complex_task):
        """Invalid subtask count should return 422/500."""
        with patch('src.api.routes.DecomposeModule') as mock_module:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [{"title": "Only one", "description": "Bad", "effort": "m"}]
            mock_result.dependencies = []
            mock_result.reasoning = "Too few"
            mock_instance.forward = Mock(return_value=mock_result)
            mock_module.return_value = mock_instance

            response = client.post("/api/decompose", json=sample_complex_task)

            assert response.status_code in [422, 500]
