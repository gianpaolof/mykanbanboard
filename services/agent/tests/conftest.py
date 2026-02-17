"""Pytest configuration and fixtures."""

from typing import Any, Generator
from unittest.mock import Mock, patch

import chromadb
import dspy
import pytest
from fastapi.testclient import TestClient

from src.main import app


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


def pytest_configure(config: pytest.Config) -> None:
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


# ============================================================================
# FASTAPI CLIENT FIXTURE
# ============================================================================


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


# ============================================================================
# DSPY FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def reset_dspy_settings() -> Generator[None, None, None]:
    """Save and restore dspy.settings.lm around each test.

    This prevents one test's LM configuration from leaking into another.
    Applied automatically to every test via autouse=True.
    """
    original_lm = dspy.settings.lm
    yield
    dspy.configure(lm=original_lm)


@pytest.fixture
def stub_lm() -> dspy.utils.DummyLM:
    """Stub DSPy LM using DummyLM for deterministic testing.

    Returns a DummyLM configured with a generic answer dict and sets it
    as the active DSPy LM. The reset_dspy_settings autouse fixture
    restores the original LM after the test.
    """
    lm = dspy.utils.DummyLM(
        answers=[
            {
                "priority": "high",
                "labels": ["bug", "backend"],
                "effort": "m",
                "reasoning": "Stub reasoning for testing",
            }
        ]
    )
    dspy.configure(lm=lm)
    return lm


# ============================================================================
# MODULE MOCK FIXTURES
# ============================================================================


@pytest.fixture
def mock_triage_module() -> Generator[Mock, None, None]:
    """Mock TriageModule at the routes layer."""
    with patch("src.api.routes.TriageModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_decompose_module() -> Generator[Mock, None, None]:
    """Mock DecomposeModule at the routes layer."""
    with patch("src.api.routes.DecomposeModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_daily_summary_module() -> Generator[Mock, None, None]:
    """Mock DailySummaryModule at the routes layer."""
    with patch("src.api.routes.DailySummaryModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_action_decider_module() -> Generator[Mock, None, None]:
    """Mock ActionDeciderModule at the routes layer."""
    with patch("src.api.routes.ActionDeciderModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


# ============================================================================
# CHROMADB FIXTURE
# ============================================================================


@pytest.fixture
def isolated_chroma() -> chromadb.ClientAPI:
    """Isolated in-memory ChromaDB client for testing.

    Uses EphemeralClient so no data persists between tests.
    """
    return chromadb.EphemeralClient()


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_ticket() -> dict[str, Any]:
    """Sample ticket data for testing."""
    return {
        "ticket_id": "test-123",
        "title": "Fix login bug on Safari",
        "description": "Users report they cannot login when using Safari browser",
        "existing_labels": ["bug", "auth", "browser", "urgent"],
    }


@pytest.fixture
def sample_complex_task() -> dict[str, Any]:
    """Sample complex task for decomposition."""
    return {
        "ticket_id": "test-456",
        "title": "Build authentication system",
        "description": "Implement complete OAuth authentication with social providers",
        "context": "Using FastAPI backend with PostgreSQL database",
    }


@pytest.fixture
def sample_chat_context() -> dict[str, Any]:
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
def sample_board_context() -> dict[str, Any]:
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
def sample_project_context() -> dict[str, Any]:
    """Sample project context for triage."""
    return {
        "tech_stack": ["Python", "FastAPI", "React", "TypeScript"],
        "conventions": ["Use conventional commits", "Write tests for all features"],
        "priority_rules": ["urgent label = critical priority", "bug = high priority"],
    }


# ============================================================================
# MOCK RESPONSE FIXTURES
# ============================================================================


class MockPrediction:
    """Mock DSPy Prediction object for testing."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with response fields."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        attrs = {k: v for k, v in self.__dict__.items()}
        return f"Prediction({attrs})"


@pytest.fixture
def mock_triage_response() -> MockPrediction:
    """Mock triage response with valid data."""
    return MockPrediction(
        priority="high",
        labels=["bug", "auth", "urgent"],
        effort="m",
        reasoning="Login issues on Safari indicate browser compatibility problem",
    )


@pytest.fixture
def mock_decompose_response() -> MockPrediction:
    """Mock decompose response with valid subtasks."""
    return MockPrediction(
        subtasks=[
            {"title": "Setup OAuth provider", "description": "Configure OAuth", "effort": "s"},
            {"title": "Create user model", "description": "Database schema", "effort": "s"},
            {"title": "Implement auth endpoints", "description": "API routes", "effort": "m"},
            {"title": "Add auth middleware", "description": "Security layer", "effort": "s"},
            {"title": "Write tests", "description": "Test coverage", "effort": "m"},
        ],
        dependencies=[(2, 1), (3, 1), (4, 2)],
        reasoning="Breaking down authentication system into logical phases",
    )


@pytest.fixture
def mock_analyze_response() -> MockPrediction:
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
def mock_chromadb(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock ChromaDB for isolated testing."""
    mock_collection = Mock()
    mock_collection.query = Mock(
        return_value={
            "ids": [["ticket-1", "ticket-2"]],
            "documents": [["Similar ticket 1", "Similar ticket 2"]],
            "metadatas": [[{"title": "Auth bug"}, {"title": "Login issue"}]],
            "distances": [[0.1, 0.2]],
        }
    )
    mock_collection.add = Mock()
    mock_collection.delete = Mock()
    mock_collection.get = Mock(
        return_value={"ids": [], "documents": [], "metadatas": []}
    )

    mock_client = Mock()
    mock_client.get_or_create_collection = Mock(return_value=mock_collection)

    monkeypatch.setattr("chromadb.PersistentClient", lambda *args, **kwargs: mock_client)
    return mock_collection
