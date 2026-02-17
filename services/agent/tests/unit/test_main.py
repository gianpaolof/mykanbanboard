"""Unit tests for the FastAPI application defined in src/main.py.

Tests cover:
- Root endpoint GET /
- Global exception handler
- setup_dspy() function branches (openai, anthropic, unknown, missing keys)
- CORS middleware presence
- App metadata (title, version)

The lifespan (which calls setup_dspy()) is bypassed by patching before
the TestClient starts the app, avoiding real API calls.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App and client setup
# We patch setup_dspy so the lifespan does not try to contact any LLM API.
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """TestClient with lifespan mocked out."""
    with patch("src.main.setup_dspy"):
        from src.main import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


class TestRootEndpoint:
    """Tests for GET /."""

    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_json(self, client):
        response = client.get("/")
        assert response.headers["content-type"].startswith("application/json")

    def test_root_service_field(self, client):
        data = client.get("/").json()
        assert data["service"] == "Kanban AI Agent"

    def test_root_version_field(self, client):
        data = client.get("/").json()
        assert data["version"] == "0.1.0"

    def test_root_status_field(self, client):
        data = client.get("/").json()
        assert data["status"] == "running"

    def test_root_model_field_present(self, client):
        data = client.get("/").json()
        assert "model" in data
        assert isinstance(data["model"], str)


# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------


class TestAppMetadata:
    def test_app_title(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi = response.json()
        assert openapi["info"]["title"] == "Kanban AI Agent"

    def test_app_version(self, client):
        response = client.get("/openapi.json")
        openapi = response.json()
        assert openapi["info"]["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------


class TestCORSMiddleware:
    """Verify CORS headers are returned for cross-origin requests."""

    def test_cors_headers_for_localhost_3000(self, client):
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_for_localhost_5173(self, client):
        response = client.get("/", headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight(self, client):
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Either 200 or 405 is fine; the important thing is CORS headers exist
        assert "access-control-allow-origin" in response.headers


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


class TestGlobalExceptionHandler:
    """Tests for the @app.exception_handler(Exception) handler."""

    def test_unhandled_exception_returns_500(self):
        """Inject a route that raises an unhandled exception."""
        with patch("src.main.setup_dspy"):
            from src.main import app
            from fastapi import APIRouter

            test_router = APIRouter()

            @test_router.get("/_test_crash")
            async def _crash():
                raise RuntimeError("boom")

            app.include_router(test_router)

            with TestClient(app, raise_server_exceptions=False) as c:
                response = c.get("/_test_crash")

            assert response.status_code == 500

    def test_unhandled_exception_response_body_error_key(self):
        with patch("src.main.setup_dspy"):
            from src.main import app
            from fastapi import APIRouter

            test_router = APIRouter()

            @test_router.get("/_test_crash2")
            async def _crash2():
                raise ValueError("test error")

            app.include_router(test_router)

            with TestClient(app, raise_server_exceptions=False) as c:
                response = c.get("/_test_crash2")

            data = response.json()
            assert data["error"] == "internal_error"
            assert data["message"] == "An unexpected error occurred"


# ---------------------------------------------------------------------------
# setup_dspy() function
# ---------------------------------------------------------------------------


def _mock_settings(**kwargs) -> MagicMock:
    """Build a MagicMock settings object with sensible defaults."""
    s = MagicMock()
    s.llm_provider = kwargs.get("llm_provider", "openai")
    s.openai_api_key = kwargs.get("openai_api_key", None)
    s.anthropic_api_key = kwargs.get("anthropic_api_key", None)
    s.default_model = kwargs.get("default_model", "gpt-4o-mini")
    s.debug = kwargs.get("debug", False)
    return s


class TestSetupDspy:
    """Tests for the setup_dspy() function in isolation.

    We patch 'src.main.settings' entirely (replacing the pydantic-settings
    singleton) because pydantic-settings attributes cannot be overridden with
    patch.object.
    """

    def test_openai_provider_calls_dspy_configure(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="openai", openai_api_key="sk-test")
        with patch("src.main.settings", mock_s), \
             patch("src.main.dspy.LM") as mock_lm, \
             patch("src.main.dspy.configure") as mock_configure:

            mock_lm.return_value = MagicMock()
            setup_dspy()

            mock_lm.assert_called_once()
            mock_configure.assert_called_once()
            call_kwargs = mock_lm.call_args[1]
            assert "openai/" in call_kwargs["model"]

    def test_openai_provider_missing_key_raises(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="openai", openai_api_key=None)
        with patch("src.main.settings", mock_s):
            with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                setup_dspy()

    def test_anthropic_provider_calls_dspy_configure(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(
            llm_provider="anthropic",
            anthropic_api_key="ant-test",
            default_model="claude-3-haiku-20240307",
        )
        with patch("src.main.settings", mock_s), \
             patch("src.main.dspy.LM") as mock_lm, \
             patch("src.main.dspy.configure") as mock_configure:

            mock_lm.return_value = MagicMock()
            setup_dspy()

            mock_lm.assert_called_once()
            mock_configure.assert_called_once()
            call_kwargs = mock_lm.call_args[1]
            assert "anthropic/" in call_kwargs["model"]

    def test_anthropic_provider_missing_key_raises(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="anthropic", anthropic_api_key=None)
        with patch("src.main.settings", mock_s):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
                setup_dspy()

    def test_unknown_provider_raises(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="unknown_provider")
        with patch("src.main.settings", mock_s):
            with pytest.raises(ValueError, match="Unknown LLM provider"):
                setup_dspy()

    def test_openai_lm_init_failure_re_raises(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="openai", openai_api_key="sk-test")
        with patch("src.main.settings", mock_s), \
             patch("src.main.dspy.LM", side_effect=Exception("LM init failed")):
            with pytest.raises(Exception, match="LM init failed"):
                setup_dspy()

    def test_anthropic_lm_init_failure_re_raises(self):
        from src.main import setup_dspy

        mock_s = _mock_settings(llm_provider="anthropic", anthropic_api_key="ant-test")
        with patch("src.main.settings", mock_s), \
             patch("src.main.dspy.LM", side_effect=Exception("Anthropic init failed")):
            with pytest.raises(Exception, match="Anthropic init failed"):
                setup_dspy()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


class TestLifespan:
    def test_lifespan_logs_and_calls_setup_dspy(self):
        """Verify the lifespan startup calls setup_dspy."""
        with patch("src.main.setup_dspy") as mock_setup:
            from src.main import app
            with TestClient(app):
                pass
            mock_setup.assert_called_once()

    def test_lifespan_raises_if_setup_dspy_fails(self):
        """If setup_dspy raises, the lifespan should propagate the exception."""
        with patch("src.main.setup_dspy", side_effect=RuntimeError("No API key")):
            from src.main import app
            with pytest.raises(RuntimeError, match="No API key"):
                with TestClient(app):
                    pass
