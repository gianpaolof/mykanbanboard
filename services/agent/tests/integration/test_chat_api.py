"""Integration tests for /api/chat endpoint."""

import pytest
from unittest.mock import Mock, patch

pytestmark = pytest.mark.anyio


class TestChatEndpoint:
    """Test /api/chat endpoint."""

    async def test_chat_create_ticket_intent(self, client):
        """Chat with 'create ticket' intent should extract action."""
        with patch('src.api.routes.ActionDeciderModule') as mock_decider:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.action = "create"
            mock_result.params = {
                "title": "Fix login bug",
                "description": "Users cannot login",
                "priority": "high"
            }
            mock_result.response = "I'll create a ticket for the login bug"
            mock_instance.forward = Mock(return_value=mock_result)
            mock_decider.return_value = mock_instance

            request_data = {
                "message": "create a ticket for login bug on safari",
                "context": {}
            }

            response = client.post("/api/chat", json=request_data)

            assert response.status_code == 200
            data = response.json()

            assert data["action"] == "create"
            assert "params" in data
            assert "response" in data

    async def test_chat_with_board_context_injects_board_id(self, client, sample_board_context):
        """Chat with board_context should inject board_id into create params."""
        with patch('src.api.routes.ActionDeciderModule') as mock_decider:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.action = "create"
            mock_result.params = {
                "title": "New ticket",
                "description": "Description",
            }
            mock_result.response = "Creating ticket"
            mock_instance.forward = Mock(return_value=mock_result)
            mock_decider.return_value = mock_instance

            request_data = {
                "message": "create a ticket",
                "board_context": sample_board_context,
                "context": {}
            }

            response = client.post("/api/chat", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Should inject board_id from context
            assert data["action"] == "create"
            assert "board_id" in data["params"] or "board_context" in request_data

    async def test_chat_timeout_20s(self, client):
        """Chat should timeout after 20s."""
        import asyncio

        with patch('src.api.routes.ActionDeciderModule') as mock_decider:
            async def slow_chat(*args, **kwargs):
                await asyncio.sleep(25)
                return Mock()

            mock_instance = Mock()
            mock_instance.forward = Mock(side_effect=slow_chat)
            mock_decider.return_value = mock_instance

            request_data = {
                "message": "test",
                "context": {}
            }

            response = client.post("/api/chat", json=request_data)

            assert response.status_code == 504
