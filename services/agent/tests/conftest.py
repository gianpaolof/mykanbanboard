"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_ticket():
    """Sample ticket data for testing."""
    return {
        "ticket_id": "test-123",
        "title": "Fix login bug on Safari",
        "description": "Users report they cannot login when using Safari browser",
        "existing_labels": ["bug", "auth", "browser", "urgent"],
    }


@pytest.fixture
def sample_complex_task():
    """Sample complex task for decomposition."""
    return {
        "ticket_id": "test-456",
        "title": "Build authentication system",
        "description": "Implement complete OAuth authentication with social providers",
        "context": "Using FastAPI backend with PostgreSQL database",
    }


@pytest.fixture
def sample_chat_context():
    """Sample chat context."""
    return {
        "tickets": [
            {
                "id": "1",
                "title": "Fix login bug",
                "status": "in_progress",
                "priority": "high",
            },
            {
                "id": "2",
                "title": "Add dark mode",
                "status": "todo",
                "priority": "medium",
            },
        ],
        "current_view": "board",
    }
