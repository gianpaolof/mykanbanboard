"""Edge case tests: error handling paths.

Tests that every major endpoint returns the correct HTTP status code and a
meaningful error message when:
- The underlying DSPy module raises an exception
- The module returns data that fails Pydantic validation
- Required fields are missing from the request
- Fields have the wrong type
- ChromaDB is unavailable

Mock wiring note
----------------
The route instantiates the module then *calls* it:
    basic_triage = TriageModule()      → mock_cls.return_value
    result = basic_triage(...)         → mock_cls.return_value.return_value

To make the module *raise* an exception on invocation, set:
    mock_cls.return_value.side_effect = SomeException(...)
"""

from unittest.mock import Mock, patch


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


# ---------------------------------------------------------------------------
# Module raises an unhandled exception → 500
# ---------------------------------------------------------------------------


class TestModuleExceptionPaths:
    """When the DSPy module raises, the API must catch it and return 500."""

    async def test_triage_module_raises_returns_500(self, client, mock_chromadb):
        """An unhandled RuntimeError inside TriageModule should yield HTTP 500."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            # Calling the instance raises the exception
            mock_cls.return_value.side_effect = RuntimeError("LLM API unreachable")

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-err-500",
                    "title": "Something broke",
                    "description": "See title",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Triage failed" in detail

    async def test_decompose_module_raises_returns_500(self, client, mock_chromadb):
        """An unhandled exception in DecomposeModule should yield HTTP 500."""
        with patch("src.api.routes.DecomposeModule") as mock_cls:
            mock_cls.return_value.side_effect = ValueError("DSPy assertion failed")

            response = client.post(
                "/api/decompose",
                json={
                    "ticket_id": "t-dec-err",
                    "title": "Build feature X",
                    "description": "Complex feature that needs decomposition",
                },
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Decomposition failed" in detail

    async def test_chat_module_raises_returns_500(self, client):
        """An unhandled exception in ActionDeciderModule should yield HTTP 500."""
        with patch("src.api.routes.ActionDeciderModule") as mock_cls:
            mock_cls.return_value.side_effect = ConnectionError("Network error")

            response = client.post(
                "/api/chat",
                json={"message": "Create a ticket for me", "context": {}},
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Chat failed" in detail

    async def test_daily_summary_module_raises_returns_500(self, client, mock_chromadb):
        """An exception in DailySummaryModule should yield HTTP 500."""
        with patch("src.api.routes.DailySummaryModule") as mock_cls:
            mock_cls.return_value.side_effect = Exception("Unexpected DSPy error")

            response = client.post(
                "/api/daily-summary",
                json={
                    "in_progress": [],
                    "blocked": [],
                    "due_soon": [],
                    "recently_completed": [],
                },
            )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Daily summary failed" in detail


# ---------------------------------------------------------------------------
# Module returns structurally invalid data → 500
# ---------------------------------------------------------------------------


class TestModuleInvalidDataPaths:
    """When the DSPy module returns data that cannot build a valid response."""

    async def test_triage_module_returns_invalid_priority_causes_error(
        self, client, mock_chromadb
    ):
        """If DSPy returns an unrecognised priority the route must return 500 or 422."""
        invalid_result = MockPrediction(
            priority="EXTREME",   # not a valid Literal
            labels=["bug"],
            effort_estimate="m",
            reasoning="Some reasoning text here",
        )

        with patch("src.api.routes.TriageModule") as mock_cls:
            mock_cls.return_value.return_value = invalid_result

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-invalid-priority",
                    "title": "Invalid priority test",
                    "description": "Testing invalid priority handling",
                    "existing_labels": ["bug"],
                },
            )

        # Either 422 (Pydantic validation) or 500 (internal error) is acceptable
        assert response.status_code in (422, 500)

    async def test_triage_module_returns_invalid_effort_causes_error(
        self, client, mock_chromadb
    ):
        """If DSPy returns an invalid effort value the response should fail validation."""
        invalid_result = MockPrediction(
            priority="medium",
            labels=[],
            effort_estimate="HUGE",   # not in xs/s/m/l/xl
            reasoning="Some reasoning text here",
        )

        with patch("src.api.routes.TriageModule") as mock_cls:
            mock_cls.return_value.return_value = invalid_result

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-invalid-effort",
                    "title": "Invalid effort test",
                    "description": "Testing invalid effort handling",
                    "existing_labels": [],
                },
            )

        assert response.status_code in (422, 500)


# ---------------------------------------------------------------------------
# Missing required fields in request → 422
# ---------------------------------------------------------------------------


class TestMissingRequiredFields:
    """Pydantic should reject requests that omit required fields with HTTP 422."""

    async def test_triage_missing_ticket_id_returns_422(self, client):
        """Omitting ticket_id should return 422."""
        response = client.post(
            "/api/triage",
            json={
                # ticket_id is required
                "title": "Some title",
                "description": "",
                "existing_labels": [],
            },
        )
        assert response.status_code == 422

    async def test_triage_missing_title_returns_422(self, client):
        """Omitting title should return 422."""
        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "t-no-title",
                # title is required
                "description": "Some description",
                "existing_labels": [],
            },
        )
        assert response.status_code == 422

    async def test_chat_missing_message_returns_422(self, client):
        """Omitting message from /api/chat should return 422."""
        response = client.post(
            "/api/chat",
            json={
                # message is required
                "context": {}
            },
        )
        assert response.status_code == 422

    async def test_search_missing_query_returns_422(self, client):
        """Omitting query from /api/search should return 422."""
        response = client.post(
            "/api/search",
            json={
                # query is required
                "limit": 5
            },
        )
        assert response.status_code == 422

    async def test_decompose_missing_title_returns_422(self, client):
        """Omitting title from /api/decompose should return 422."""
        response = client.post(
            "/api/decompose",
            json={
                "ticket_id": "t-dec-no-title",
                # title is required (min_length=1)
                "description": "Some description",
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Wrong type for a field → 422
# ---------------------------------------------------------------------------


class TestWrongFieldTypes:
    """Pydantic should reject requests with wrong types and return 422."""

    async def test_triage_labels_as_string_instead_of_list(self, client):
        """existing_labels must be a list; sending a string should return 422."""
        response = client.post(
            "/api/triage",
            json={
                "ticket_id": "t-wrong-type",
                "title": "Type error test",
                "description": "Testing type validation",
                "existing_labels": "bug,feature",  # string instead of list
            },
        )
        assert response.status_code == 422

    async def test_search_limit_as_string_returns_422(self, client):
        """limit must be an integer; passing a non-numeric string should return 422."""
        response = client.post(
            "/api/search",
            json={
                "query": "authentication",
                "limit": "five",  # string instead of int
            },
        )
        assert response.status_code == 422

    async def test_triage_ticket_id_as_integer_does_not_crash(self, client, mock_chromadb):
        """ticket_id as integer: Pydantic v2 coerces int→str, so it should not 500."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            prediction = MockPrediction(
                priority="medium",
                labels=[],
                effort_estimate="m",
                reasoning="Integer ticket id coerced to string",
            )
            mock_cls.return_value.return_value = prediction

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": 12345,   # int → Pydantic v2 coerces to str
                    "title": "Type test",
                    "description": "",
                    "existing_labels": [],
                },
            )

        # Pydantic v2 coerces int to str for str fields, so 200 is expected.
        # We only ensure it does not raise an internal 500 crash.
        assert response.status_code != 500


# ---------------------------------------------------------------------------
# ChromaDB connection failure
# ---------------------------------------------------------------------------


class TestChromaDBFailure:
    """When ChromaDB is unavailable, the search endpoint should return 500."""

    async def test_search_chromadb_failure_returns_500(self, client, mock_chromadb):
        """A ChromaDB exception during search should propagate as HTTP 500."""
        mock_chromadb.query.side_effect = Exception("Connection refused to ChromaDB")

        response = client.post(
            "/api/search",
            json={"query": "authentication", "limit": 5},
        )

        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "Search failed" in detail

    async def test_search_chromadb_timeout_returns_500(self, client, mock_chromadb):
        """A ChromaDB timeout during search should propagate as HTTP 500."""
        mock_chromadb.query.side_effect = TimeoutError("ChromaDB query timed out")

        response = client.post(
            "/api/search",
            json={"query": "login issue", "limit": 3},
        )

        assert response.status_code == 500
