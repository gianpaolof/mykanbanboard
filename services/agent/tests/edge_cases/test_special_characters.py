"""Edge case tests: special character handling.

Verifies that ticket titles/descriptions containing Unicode, SQL-injection
patterns, newlines, and special JSON characters are handled safely and do
not crash the API or introduce unexpected failures.

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
# Unicode in title and description
# ---------------------------------------------------------------------------


class TestUnicodeHandling:
    """Triage with Unicode content in various fields."""

    async def test_triage_unicode_special_chars(self, client, mock_chromadb):
        """Title with special Unicode characters should be accepted without crashing."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="medium",
                labels=[],
                effort_estimate="m",
                reasoning="Special chars processed fine",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-special",
                    "title": "Fix crash \u2014 critical failure \u2192 severity HIGH",
                    "description": "App crashes with message: \u00ab critical failure \u00bb",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200

    async def test_triage_unicode_latin_extended(self, client, mock_chromadb):
        """Title with extended Latin characters (accents, umlauts) should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["bug"],
                effort_estimate="m",
                reasoning="Latin extended processed",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-latin",
                    "title": "Probl\u00e8me d\u2019authentification \u00e9chou\u00e9e",
                    "description": "Les utilisateurs ne peuvent pas se connecter",
                    "existing_labels": ["bug"],
                },
            )

        assert response.status_code == 200

    async def test_triage_unicode_cjk_characters(self, client, mock_chromadb):
        """Title with Chinese/Japanese/Korean characters should not crash."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="medium",
                labels=[],
                effort_estimate="m",
                reasoning="CJK processed",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-cjk",
                    "title": "\u30ed\u30b0\u30a4\u30f3\u30d0\u30b0\u4fee\u6b63",
                    "description": "\u30e6\u30fc\u30b6\u30fc\u304c\u30ed\u30b0\u30a4\u30f3\u3067\u304d\u306a\u3044",
                    "existing_labels": [],
                },
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# SQL-injection-like strings
# ---------------------------------------------------------------------------


class TestSQLInjectionStrings:
    """API should treat SQL-like strings as plain text, not execute anything."""

    async def test_triage_sql_injection_in_title(self, client, mock_chromadb):
        """SQL injection pattern in title should be treated as plain text."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["security"],
                effort_estimate="m",
                reasoning="SQL string treated as text",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-sqli",
                    "title": "'; DROP TABLE tickets; --",
                    "description": "Potential SQL injection attack vector in search",
                    "existing_labels": ["security"],
                },
            )

        # API should accept the request (it's valid text), not crash or 500
        assert response.status_code == 200

    async def test_triage_sql_injection_in_description(self, client, mock_chromadb):
        """SQL injection pattern in description should be treated as plain text."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["security", "bug"],
                effort_estimate="m",
                reasoning="SQL desc treated as text",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-sqli-desc",
                    "title": "Security audit finding",
                    "description": "Input field accepts: 1 OR 1=1 UNION SELECT * FROM users",
                    "existing_labels": ["security", "bug"],
                },
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Newlines and multi-line text
# ---------------------------------------------------------------------------


class TestNewlinesInFields:
    """Multi-line text in title and description fields."""

    async def test_triage_newlines_in_description(self, client, mock_chromadb):
        """Newlines and tabs in description should be handled gracefully."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="high",
                labels=["bug"],
                effort_estimate="m",
                reasoning="Newlines in description handled fine",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-newline-desc",
                    "title": "Multi-line bug report",
                    "description": "Steps to reproduce:\n1. Open the app\n2. Click login\n\tResult: crash\n\nExpected: success",
                    "existing_labels": ["bug"],
                },
            )

        assert response.status_code == 200

    async def test_chat_message_with_newlines(self, client):
        """Chat message containing newlines should be passed through correctly."""
        with patch("src.api.routes.ActionDeciderModule") as mock_cls:
            result = Mock()
            result.action = "none"
            result.params = {}
            result.response = "Understood your multi-line request"
            mock_cls.return_value.return_value = result

            response = client.post(
                "/api/chat",
                json={
                    "message": "Show me:\n- All bugs\n- High priority only",
                    "context": {},
                },
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Special JSON characters
# ---------------------------------------------------------------------------


class TestSpecialJsonCharacters:
    """Fields containing characters that are special in JSON (quotes, backslashes)."""

    async def test_triage_double_quotes_in_title(self, client, mock_chromadb):
        """Title with embedded double-quotes should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="low",
                labels=["ui", "bug"],
                effort_estimate="xs",
                reasoning="Quotes handled",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-quotes",
                    "title": 'Button shows "Submit" instead of "Save"',
                    "description": 'The label reads "Submit" but should read "Save"',
                    "existing_labels": ["ui", "bug"],
                },
            )

        assert response.status_code == 200

    async def test_triage_backslashes_in_description(self, client, mock_chromadb):
        """Description with backslashes (e.g. file paths) should be accepted."""
        with patch("src.api.routes.TriageModule") as mock_cls:
            _patch_triage(
                mock_cls,
                priority="medium",
                labels=["bug", "windows"],
                effort_estimate="s",
                reasoning="Backslashes handled",
            )

            response = client.post(
                "/api/triage",
                json={
                    "ticket_id": "t-backslash",
                    "title": "File path error on Windows",
                    "description": "Error occurs at path C:\\Users\\admin\\AppData\\config.json",
                    "existing_labels": ["bug", "windows"],
                },
            )

        assert response.status_code == 200
