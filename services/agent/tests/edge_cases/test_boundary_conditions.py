"""Edge case tests: boundary / limit conditions.

Tests that the API correctly handles values exactly at, just inside,
and just outside defined limits.

Mock wiring note
----------------
The route instantiates the module then *calls* it:
    basic_triage = TriageModule()      → mock_cls.return_value
    result = basic_triage(...)         → mock_cls.return_value.return_value

So to control what the route receives we set
    mock_cls.return_value.return_value = <our MockPrediction>
"""

from unittest.mock import patch


class MockPrediction:
    """Minimal mock that mirrors DSPy Prediction extraction behaviour.

    Stores values in ``_store`` (DSPy 3.x path) and as direct attributes
    so that ``extract_labels`` / ``safe_extract`` can find them via all
    three extraction strategies.
    """

    def __init__(self, **kwargs):
        self._store = dict(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


def _patch_triage(mock_cls, **prediction_kwargs):
    """Wire ``mock_cls`` so calling the returned instance gives a MockPrediction."""
    prediction = MockPrediction(**prediction_kwargs)
    mock_cls.return_value.return_value = prediction
    return prediction


# ---------------------------------------------------------------------------
# Title length boundaries
# ---------------------------------------------------------------------------


class TestTitleBoundaries:
    """Triage title field length constraints."""

    async def test_triage_title_exactly_500_chars_accepted(self, client, mock_chromadb):
        """A 500-character title is the maximum allowed by TriageRequest."""
        long_title = "A" * 500

        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=[],
                effort_estimate="xs",
                reasoning="Very long title processed",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-boundary-500",
                    "title": long_title,
                    "description": "",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200

    async def test_triage_title_501_chars_rejected(self, client):
        """A 501-character title exceeds max_length=500 and should return 422."""
        too_long_title = "B" * 501

        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "t-boundary-501",
                "title": too_long_title,
                "description": "",
                "existing_labels": [],
            },
        )

        assert response.status_code == 422

    async def test_triage_very_long_title_over_1000_chars(self, client):
        """A title over 1000 characters must also return 422."""
        enormous_title = "X" * 1200

        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "t-huge",
                "title": enormous_title,
                "description": "",
                "existing_labels": [],
            },
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Labels count boundaries
# ---------------------------------------------------------------------------


class TestLabelsBoundaries:
    """Tests for label list size at and around the TriageResponse max_length=3 limit."""

    async def test_triage_returns_exactly_3_labels_accepted(self, client, mock_chromadb):
        """Exactly 3 labels in the DSPy result should pass response validation."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["bug", "backend", "urgent"],
                effort_estimate="m",
                reasoning="Three labels is the maximum recommended",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-3labels",
                    "title": "Critical auth failure",
                    "description": "Users cannot login",
                    "existing_labels": ["bug", "backend", "urgent", "frontend"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 3

    async def test_triage_returns_1_label_accepted(self, client, mock_chromadb):
        """A single label in the result is within bounds and should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=["docs"],
                effort_estimate="xs",
                reasoning="Only one label relevant",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-1label",
                    "title": "Update README",
                    "description": "Improve getting-started section",
                    "existing_labels": ["docs", "enhancement"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["labels"]) == 1


# ---------------------------------------------------------------------------
# Effort value boundaries
# ---------------------------------------------------------------------------


class TestEffortBoundaries:
    """Effort values at each valid boundary."""

    async def test_triage_effort_xs_boundary(self, client, mock_chromadb):
        """Smallest valid effort value 'xs' should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=[],
                effort_estimate="xs",
                reasoning="Quick fix under an hour",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-effort-xs",
                    "title": "Fix typo in README",
                    "description": "One word typo",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200
        assert response.json()["effort"] == "xs"

    async def test_triage_effort_xl_boundary(self, client, mock_chromadb):
        """Largest valid effort value 'xl' should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["epic"],
                effort_estimate="xl",
                reasoning="This is an epic-level task",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-effort-xl",
                    "title": "Rebuild entire authentication system",
                    "description": "Complete rewrite of auth",
                    "existing_labels": ["epic", "backend"],
                },
            )

        assert response.status_code == 200
        assert response.json()["effort"] == "xl"


# ---------------------------------------------------------------------------
# Priority value boundaries
# ---------------------------------------------------------------------------


class TestPriorityBoundaries:
    """Priority values at each extreme."""

    async def test_triage_priority_low_boundary(self, client, mock_chromadb):
        """'low' is the lowest priority and should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=[],
                effort_estimate="xs",
                reasoning="Nice to have, low urgency",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-prio-low",
                    "title": "Add emoji to commit messages",
                    "description": "Just for fun",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200
        assert response.json()["priority"] == "low"

    async def test_triage_priority_critical_boundary(self, client, mock_chromadb):
        """'critical' is the highest priority and should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="critical",
                labels=["security", "urgent"],
                effort_estimate="m",
                reasoning="Production data leak requires immediate action",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-prio-critical",
                    "title": "SQL injection vulnerability in login form",
                    "description": "Attackers can bypass authentication",
                    "existing_labels": ["security", "urgent", "bug"],
                },
            )

        assert response.status_code == 200
        assert response.json()["priority"] == "critical"


# ---------------------------------------------------------------------------
# Search limit boundaries
# ---------------------------------------------------------------------------


class TestSearchLimitBoundaries:
    """Search limit parameter boundary tests."""

    async def test_search_limit_1_minimum(self, client, mock_chromadb):
        """Search with limit=1 (minimum allowed) should succeed."""
        mock_chromadb.query.return_value = {
            "ids": [["ticket-1"]],
            "documents": [["Auth bug document"]],
            "metadatas": [[{"title": "Auth bug", "description": ""}]],
            "distances": [[0.1]],
        }

        response = client.post(
            "/api/search",
            json={"query": "authentication", "limit": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 1

    async def test_search_limit_20_maximum(self, client, mock_chromadb):
        """Search with limit=20 (maximum allowed) should succeed."""
        mock_chromadb.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        response = client.post(
            "/api/search",
            json={"query": "login", "limit": 20},
        )

        assert response.status_code == 200

    async def test_search_limit_0_rejected(self, client):
        """Search with limit=0 is below ge=1 and should return 422."""
        response = client.post(
            "/api/search",
            json={"query": "login", "limit": 0},
        )

        assert response.status_code == 422

    async def test_search_limit_21_rejected(self, client):
        """Search with limit=21 exceeds le=20 and should return 422."""
        response = client.post(
            "/api/search",
            json={"query": "login", "limit": 21},
        )

        assert response.status_code == 422
