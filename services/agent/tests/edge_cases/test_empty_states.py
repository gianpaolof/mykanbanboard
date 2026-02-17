"""Edge case tests: empty / zero inputs.

Tests that the API behaves correctly when given minimal, empty,
or zero-valued inputs across every major endpoint.

Mock wiring note
----------------
The route instantiates the module then *calls* it:
    basic_triage = TriageModule()      → mock_cls.return_value
    result = basic_triage(...)         → mock_cls.return_value.return_value

So to control what the route receives we set
    mock_cls.return_value.return_value = <our MockPrediction>
"""

from unittest.mock import Mock, patch


class MockPrediction:
    """Minimal mock for a DSPy Prediction used in these tests.

    Stores values in both direct attributes AND a ``_store`` dict so that
    all three extraction strategies in ``extract_labels`` / ``safe_extract``
    find the right data.
    """

    def __init__(self, **kwargs):
        self._store = dict(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


def _patch_triage(mock_cls, **prediction_kwargs):
    """Wire ``mock_cls`` so calling the instance returns a MockPrediction."""
    prediction = MockPrediction(**prediction_kwargs)
    mock_cls.return_value.return_value = prediction
    return prediction


# ---------------------------------------------------------------------------
# Triage — empty title guard (Pydantic min_length=1 on title)
# ---------------------------------------------------------------------------


class TestEmptyTriage:
    """Triage endpoint behaviour with empty / minimal inputs."""

    async def test_triage_empty_title_returns_422(self, client):
        """Title with only an empty string is rejected (min_length=1)."""
        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "t-001",
                "title": "",
                "description": "Some description",
                "existing_labels": ["bug"],
            },
        )
        assert response.status_code == 422

    async def test_triage_empty_labels_list(self, client, mock_chromadb):
        """Triage with an empty existing_labels list should still succeed."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="medium",
                labels=["bug"],
                effort_estimate="m",
                reasoning="No existing labels, suggesting a generic one",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-002",
                    "title": "Fix crash on startup",
                    "description": "App crashes on first launch",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert isinstance(data["labels"], list)

    async def test_triage_empty_description(self, client, mock_chromadb):
        """Triage with an empty description should succeed (description defaults to '')."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=[],
                effort_estimate="xs",
                reasoning="No description provided, minimal effort assumed",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-003",
                    "title": "Minor typo fix",
                    "description": "",
                    "existing_labels": ["docs"],
                },
            )

        assert response.status_code == 200

    async def test_triage_missing_description_uses_default(self, client, mock_chromadb):
        """Triage without a description field uses the empty-string default."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="medium",
                labels=["feature"],
                effort_estimate="m",
                reasoning="Default description assumed",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-004",
                    "title": "Add dark mode",
                    # no 'description' key at all
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Search — empty collection
# ---------------------------------------------------------------------------


class TestEmptySearch:
    """Search endpoint behaviour when ChromaDB collection is empty."""

    async def test_search_empty_chromadb_returns_empty_list(self, client, mock_chromadb):
        """Search against an empty collection should return an empty results list."""
        mock_chromadb.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        response = client.post(
            "/api/search",
            json={"query": "authentication bug", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["query"] == "authentication bug"


# ---------------------------------------------------------------------------
# Daily summary — empty board (all categories empty)
# ---------------------------------------------------------------------------


class TestEmptyDailySummary:
    """Daily summary with an entirely empty board."""

    async def test_daily_summary_empty_board(self, client, mock_chromadb):
        """Daily summary with no tickets in any category should succeed."""
        with patch("src.api.routes.DailySummaryModule") as mock_cls:
            # Note: extract_value() unwraps single-element lists, so we pass
            # two items here so the list survives intact into DailySummaryResponse.
            prediction = MockPrediction(
                greeting="Good morning! The board is empty.",
                focus_today=["Plan new work", "Review backlog"],
                blockers=[],
                quick_wins=[],
            )
            mock_cls.return_value.return_value = prediction

            response = client.post(
                "/api/daily-summary",
                json={
                    "in_progress": [],
                    "blocked": [],
                    "due_soon": [],
                    "recently_completed": [],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "greeting" in data
        assert isinstance(data["focus_today"], list)
        assert isinstance(data["blockers"], list)
        assert isinstance(data["quick_wins"], list)


# ---------------------------------------------------------------------------
# Chat — empty context
# ---------------------------------------------------------------------------


class TestEmptyChatContext:
    """Chat endpoint with empty or missing context dicts."""

    async def test_chat_with_no_context_fields(self, client):
        """Chat with only a message (no context or board_context) should succeed."""
        with patch("src.api.routes.ActionDeciderModule") as mock_cls:
            result = Mock()
            result.action = "none"
            result.params = {}
            result.response = "Hello! How can I help?"
            mock_cls.return_value.return_value = result

            response = client.post(
                "/api/chat",
                json={"message": "Hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "none"

    async def test_chat_with_empty_context_dict(self, client):
        """Chat with explicit empty dicts for context and board_context should succeed."""
        with patch("src.api.routes.ActionDeciderModule") as mock_cls:
            result = Mock()
            result.action = "search"
            result.params = {"query": "login"}
            result.response = "Searching for login-related tickets"
            mock_cls.return_value.return_value = result

            response = client.post(
                "/api/chat",
                json={
                    "message": "show me login tickets",
                    "context": {},
                    "board_context": {},
                },
            )

        assert response.status_code == 200

    async def test_chat_empty_message_returns_422(self, client):
        """An empty message string fails Pydantic validation (min_length=1)."""
        response = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert response.status_code == 422
