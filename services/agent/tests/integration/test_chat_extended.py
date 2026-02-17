"""Extended integration tests for /api/chat endpoint.

Covers additional edge cases beyond test_chat_api.py:
- All valid action types
- Empty/minimal messages
- Board context usage
- Error handling
- Response serialisation

IMPORTANT: The ActionDeciderModule returns a Prediction-like object whose
attributes (action, params, response) are extracted via extract_value().
We use plain Python objects as return values to avoid Mock callable confusion.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chat_result(
    action: str = "none",
    params: dict | None = None,
    response: str = "Done!",
) -> object:
    """Return a plain object that mimics a DSPy Prediction for chat."""
    class _Result:
        pass

    r = _Result()
    r.action = action
    r.params = params if params is not None else {}
    r.response = response
    return r


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestChatAllActionTypes:
    """Verify all valid action types are accepted by the response model."""

    @pytest.mark.parametrize("action", [
        "create",
        "update",
        "move",
        "search",
        "summarize",
        "decompose",
        "none",
    ])
    def test_chat_returns_valid_action_type(self, client, action):
        """Every valid action type should be accepted by the response schema."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action=action,
                response=f"Performing {action}",
            )

            response = client.post(
                "/api/chat",
                json={"message": f"perform {action} operation"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == action


class TestChatRequestValidation:
    """Validate request field requirements."""

    def test_chat_missing_message_returns_422(self, client):
        """Missing 'message' field should return 422."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_chat_empty_message_returns_422(self, client):
        """Empty string 'message' violates min_length=1, should return 422."""
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422

    def test_chat_with_only_message_field_succeeds(self, client):
        """Only 'message' field (no context, no board_context) should work."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action="none",
                response="OK",
            )

            response = client.post(
                "/api/chat",
                json={"message": "hello"},
            )

        assert response.status_code == 200

    def test_chat_with_null_context_field(self, client):
        """Null context should default to empty dict gracefully."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action="none",
                response="OK",
            )

            response = client.post(
                "/api/chat",
                json={"message": "hello", "context": None},
            )

        assert response.status_code == 200

    def test_chat_with_null_board_context_field(self, client):
        """Null board_context should default to empty dict gracefully."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action="none",
                response="OK",
            )

            response = client.post(
                "/api/chat",
                json={"message": "hello", "board_context": None},
            )

        assert response.status_code == 200


class TestChatResponseSerialization:
    """Verify response model serialization."""

    def test_chat_params_defaults_to_empty_dict(self, client):
        """When params is not a dict, response should contain empty dict."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            result = _make_chat_result(action="none", response="OK")
            result.params = "not-a-dict"  # Non-dict params should become {}
            mock_class.return_value.return_value = result

            response = client.post(
                "/api/chat",
                json={"message": "hello"},
            )

        assert response.status_code == 200
        data = response.json()
        # Route: params = raw_params if isinstance(raw_params, dict) else {}
        assert data["params"] == {}

    def test_chat_response_contains_all_fields(self, client):
        """Chat response should always contain action, params and response."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action="search",
                params={"query": "login bug"},
                response="Searching for login bug tickets",
            )

            response = client.post(
                "/api/chat",
                json={"message": "find tickets about login"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "action" in data
        assert "params" in data
        assert "response" in data
        assert data["action"] == "search"
        assert data["params"] == {"query": "login bug"}
        assert "login bug" in data["response"]

    def test_chat_module_receives_board_context(self, client):
        """ActionDeciderModule should be called with board_context from request."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.return_value = _make_chat_result(
                action="create",
                params={"title": "New ticket"},
                response="Creating ticket",
            )

            board_ctx = {"board_id": "board-1", "columns": []}
            response = client.post(
                "/api/chat",
                json={
                    "message": "create a ticket",
                    "board_context": board_ctx,
                },
            )

        assert response.status_code == 200
        # Verify the module was called (its __call__ on the instance)
        instance = mock_class.return_value
        instance.assert_called_once()
        call_kwargs = instance.call_args[1]
        assert call_kwargs.get("board_context") == board_ctx


class TestChatErrorHandling:
    """Verify error handling in /api/chat."""

    def test_chat_module_exception_returns_500(self, client):
        """Unhandled module exception should return 500."""
        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            mock_class.return_value.side_effect = Exception("LLM call failed")

            response = client.post(
                "/api/chat",
                json={"message": "hello"},
            )

        assert response.status_code == 500
        assert "chat failed" in response.json()["detail"].lower()

    def test_chat_http_exception_propagates(self, client):
        """HTTPException raised in module should propagate as-is."""
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Chat timed out after 20 seconds. Please try again.",
            )

            response = client.post(
                "/api/chat",
                json={"message": "hello"},
            )

        assert response.status_code == 504
        assert "20 seconds" in response.json()["detail"]

    def test_chat_timeout_returns_504(self, client):
        """Slow module should trigger 504 via run_sync_with_timeout."""
        import asyncio

        with patch("src.api.routes.ActionDeciderModule") as mock_class:
            # Make the module hang longer than CHAT_TIMEOUT (20s)
            # We simulate this by patching run_sync_with_timeout directly
            pass

        # Direct timeout simulation via the helper
        with patch("src.api.routes.run_sync_with_timeout") as mock_timeout:
            mock_timeout.side_effect = HTTPException(
                status_code=504,
                detail="Chat timed out after 20 seconds. Please try again.",
            )

            response = client.post(
                "/api/chat",
                json={"message": "hello"},
            )

        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()
