"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
import dspy

from src.main import app


# ============================================================================
# FASTAPI CLIENT FIXTURE
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

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


@pytest.fixture
def sample_board_context():
    """Sample board context for context-aware operations."""
    return {
        "board_id": "board-123",
        "columns": [
            {"id": "col-1", "name": "Todo", "order": 0},
            {"id": "col-2", "name": "In Progress", "order": 1},
            {"id": "col-3", "name": "Done", "order": 2},
        ],
        "labels": ["bug", "feature", "enhancement", "urgent", "backend", "frontend"],
    }


@pytest.fixture
def sample_project_context():
    """Sample project context for triage."""
    return {
        "tech_stack": ["Python", "FastAPI", "React", "TypeScript"],
        "conventions": ["Use conventional commits", "Write tests for all features"],
        "priority_rules": ["urgent label = critical priority", "bug = high priority"],
    }


# ============================================================================
# DSPY MOCKING FIXTURES
# ============================================================================

class MockPrediction:
    """Mock DSPy Prediction object for testing."""

    def __init__(self, **kwargs):
        """Initialize with response fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = {k: v for k, v in self.__dict__.items()}
        return f"Prediction({attrs})"


@pytest.fixture
def mock_dspy_lm(monkeypatch):
    """Mock DSPy LM for deterministic testing."""
    mock_lm = Mock()
    mock_lm.history = []

    def mock_call(self, **kwargs):
        """Mock LM call that returns predefined responses."""
        # Return a mock prediction - tests can customize via monkeypatch
        return MockPrediction(
            priority="high",
            labels=["bug", "backend"],
            effort_estimate="m",
            reasoning="Sample reasoning for testing",
        )

    mock_lm.__call__ = mock_call
    monkeypatch.setattr("dspy.LM", lambda *args, **kwargs: mock_lm)
    return mock_lm


@pytest.fixture
def mock_triage_response():
    """Mock triage response with valid data."""
    return MockPrediction(
        priority="high",
        labels=["bug", "auth", "urgent"],
        effort_estimate="m",
        reasoning="Login issues on Safari indicate browser compatibility problem",
    )


@pytest.fixture
def mock_decompose_response():
    """Mock decompose response with valid subtasks."""
    return MockPrediction(
        subtasks=[
            {"title": "Setup OAuth provider", "description": "Configure OAuth", "effort": "s"},
            {"title": "Create user model", "description": "Database schema", "effort": "s"},
            {"title": "Implement auth endpoints", "description": "API routes", "effort": "m"},
            {"title": "Add auth middleware", "description": "Security layer", "effort": "s"},
            {"title": "Write tests", "description": "Test coverage", "effort": "m"},
        ],
        dependencies=[(2, 1), (3, 1), (4, 2)],  # indices must be valid
        reasoning="Breaking down authentication system into logical phases",
    )


@pytest.fixture
def mock_analyze_response():
    """Mock analyze response with all 3 hops."""
    return MockPrediction(
        context_summary="Found 3 similar authentication tickets",
        key_themes=["OAuth integration", "Security", "User management"],
        patterns=["Most auth implementations use JWT", "2FA is common requirement"],
        dependencies=["PostgreSQL database", "Redis for sessions"],
        insights=["Consider using existing OAuth library", "Plan for 2FA from start"],
        recommendations=[
            "Use Authlib for OAuth",
            "Implement JWT with refresh tokens",
            "Add rate limiting to auth endpoints",
        ],
        complexity="high",
    )


@pytest.fixture
def mock_chromadb(monkeypatch):
    """Mock ChromaDB for isolated testing."""
    mock_collection = Mock()
    mock_collection.query = Mock(return_value={
        "ids": [["ticket-1", "ticket-2"]],
        "documents": [["Similar ticket 1", "Similar ticket 2"]],
        "metadatas": [[{"title": "Auth bug"}, {"title": "Login issue"}]],
        "distances": [[0.1, 0.2]],
    })
    mock_collection.add = Mock()
    mock_collection.delete = Mock()
    mock_collection.get = Mock(return_value={"ids": [], "documents": [], "metadatas": []})

    mock_client = Mock()
    mock_client.get_or_create_collection = Mock(return_value=mock_collection)

    monkeypatch.setattr("chromadb.PersistentClient", lambda *args, **kwargs: mock_client)
    return mock_collection


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "live_api: mark test as requiring real LLM API (skipped by default)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (> 1s)"
    )
