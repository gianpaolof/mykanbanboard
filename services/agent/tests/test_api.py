"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "kanban-agent"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client: TestClient):
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Kanban AI Agent"
        assert data["version"] == "0.1.0"
        assert data["status"] == "running"


class TestTriageEndpoint:
    """Tests for triage endpoint."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_triage_ticket(self, client: TestClient, sample_ticket):
        """Test ticket triage."""
        response = client.post("/api/triage", json=sample_ticket)
        assert response.status_code == 200
        data = response.json()

        assert "priority" in data
        assert data["priority"] in ["low", "medium", "high", "critical"]

        assert "labels" in data
        assert isinstance(data["labels"], list)
        assert len(data["labels"]) <= 3

        assert "effort" in data
        assert data["effort"] in ["xs", "s", "m", "l", "xl"]

        assert "reasoning" in data
        assert isinstance(data["reasoning"], str)

    def test_triage_missing_fields(self, client: TestClient):
        """Test triage with missing required fields."""
        response = client.post("/api/triage", json={})
        assert response.status_code == 422  # Validation error


class TestDecomposeEndpoint:
    """Tests for decompose endpoint."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_decompose_task(self, client: TestClient, sample_complex_task):
        """Test task decomposition."""
        response = client.post("/api/decompose", json=sample_complex_task)
        assert response.status_code == 200
        data = response.json()

        assert "subtasks" in data
        assert isinstance(data["subtasks"], list)
        assert len(data["subtasks"]) > 0

        # Check subtask structure
        for subtask in data["subtasks"]:
            assert "title" in subtask
            assert "description" in subtask
            assert "effort" in subtask

        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)

        assert "reasoning" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_chat(self, client: TestClient, sample_chat_context):
        """Test chat interaction."""
        response = client.post(
            "/api/chat",
            json={
                "message": "What should I focus on today?",
                "context": sample_chat_context,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "action" in data
        assert data["action"] in [
            "create",
            "update",
            "move",
            "search",
            "summarize",
            "decompose",
            "none",
        ]

        assert "params" in data
        assert isinstance(data["params"], dict)

        assert "response" in data
        assert isinstance(data["response"], str)
