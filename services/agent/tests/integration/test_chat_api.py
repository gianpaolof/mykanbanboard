"""Integration tests for /api/chat endpoint.

KEY: The route calls `action_decider(user_message=..., ...)` via __call__,
not .forward(). Mocks must use `mock_class.return_value.return_value = result`.

Use plain objects with concrete attribute values (not Mock) to avoid extract_value
treating attributes as callable Mocks.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _chat_result(
    action: str = "none",
    params: dict | None = None,
    response: str = "Done!",
) -> object:
    """Return a plain object mimicking a DSPy Prediction for chat."""
    class _Pred:
        pass

    p = _Pred()
    p.action = action
    p.params = params if params is not None else {}
    p.response = response
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    """Test /api/chat endpoint."""

    def test_chat_create_ticket_intent(self, client):
        """Chat with 'create ticket' intent should extract action."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _chat_result(
                action="create",
                params={"title": "Fix login bug", "description": "Users cannot login", "priority": "high"},
                response="I'll create a ticket for the login bug",
            )

            request_data = {
                "message": "create a ticket for login bug on safari",
                "context": {},
            }

            response = client.post("/api/chat", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["action"] == "create"
        assert "params" in data
        assert "response" in data

    def test_chat_with_board_context(self, client, sample_board_context):
        """Chat with board_context should include board information."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _chat_result(
                action="create",
                params={"title": "New ticket", "description": "Description"},
                response="Creating ticket",
            )

            request_data = {
                "message": "create a ticket",
                "board_context": sample_board_context,
                "context": {},
            }

            response = client.post("/api/chat", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "create"

    def test_chat_timeout_20s(self, client):
        """Chat should timeout with 504 when run_sync_with_timeout raises HTTPException."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Chat timed out after 20 seconds. Please try again.",
            )

            request_data = {
                "message": "test",
                "context": {},
            }

            response = client.post("/api/chat", json=request_data)

        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()

    def test_chat_none_action_is_valid(self, client):
        """'none' is a valid action type in the response schema."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _chat_result(
                action="none",
                response="I'm not sure how to help with that.",
            )

            response = client.post("/api/chat", json={"message": "what is the weather?"})

        assert response.status_code == 200
        assert response.json()["action"] == "none"

    def test_chat_module_exception_returns_500(self, client):
        """Module exception should return 500."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.side_effect = Exception("LLM failure")

            response = client.post("/api/chat", json={"message": "hello"})

        assert response.status_code == 500
        assert "chat failed" in response.json()["detail"].lower()
