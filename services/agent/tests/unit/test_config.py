"""Tests for AgentSettings configuration (src.config).

Verifies that:
- Settings can be instantiated without environment variables
- All defaults are correct types and values
- Field validators work as expected
- Port and numeric constraints are valid
"""

import pytest
from pydantic import ValidationError

from src.config import AgentSettings


class TestSettingsDefaults:
    """Test that all default values are correct."""

    def test_settings_instantiate_without_env(self):
        """AgentSettings should load with defaults, no env file required."""
        settings = AgentSettings()
        assert settings is not None

    def test_default_llm_provider_is_openai(self):
        """Default LLM provider should be 'openai'."""
        settings = AgentSettings()
        assert settings.llm_provider == "openai"

    def test_default_model_is_gpt4o_mini(self):
        """Default model should be 'gpt-4o-mini'."""
        settings = AgentSettings()
        assert settings.default_model == "gpt-4o-mini"

    def test_fallback_model_is_gpt4o_mini(self):
        """Default fallback model should be 'gpt-4o-mini'."""
        settings = AgentSettings()
        assert settings.fallback_model == "gpt-4o-mini"

    def test_default_embedding_model(self):
        """Default embedding model should be 'text-embedding-3-small'."""
        settings = AgentSettings()
        assert settings.embedding_model == "text-embedding-3-small"

    def test_default_embedding_dimensions(self):
        """Default embedding dimensions should be 1536."""
        settings = AgentSettings()
        assert settings.embedding_dimensions == 1536

    def test_default_port_is_8765(self):
        """Default port should be 8765."""
        settings = AgentSettings()
        assert settings.port == 8765

    def test_default_host_is_localhost(self):
        """Default host should be '127.0.0.1'."""
        settings = AgentSettings()
        assert settings.host == "127.0.0.1"

    def test_debug_is_false_by_default(self):
        """Debug mode should default to False."""
        settings = AgentSettings()
        assert settings.debug is False

    def test_auto_triage_enabled_by_default(self):
        """Auto-triage should be enabled by default."""
        settings = AgentSettings()
        assert settings.auto_triage_enabled is True

    def test_default_max_decompose_subtasks(self):
        """Max decompose subtasks should default to 7."""
        settings = AgentSettings()
        assert settings.max_decompose_subtasks == 7

    def test_default_search_results_limit(self):
        """Search results limit should default to 10."""
        settings = AgentSettings()
        assert settings.search_results_limit == 10

    def test_default_max_requests_per_minute(self):
        """Max requests per minute should default to 20."""
        settings = AgentSettings()
        assert settings.max_requests_per_minute == 20


class TestSettingsTypes:
    """Test that all settings fields are the expected types."""

    def test_model_names_are_strings(self):
        """Model name fields should all be strings."""
        settings = AgentSettings()
        assert isinstance(settings.default_model, str)
        assert isinstance(settings.fallback_model, str)
        assert isinstance(settings.embedding_model, str)
        assert isinstance(settings.llm_provider, str)

    def test_port_is_integer(self):
        """Port should be an integer."""
        settings = AgentSettings()
        assert isinstance(settings.port, int)

    def test_embedding_dimensions_is_integer(self):
        """Embedding dimensions should be an integer."""
        settings = AgentSettings()
        assert isinstance(settings.embedding_dimensions, int)

    def test_boolean_fields_are_booleans(self):
        """Boolean config fields should be actual booleans."""
        settings = AgentSettings()
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.auto_triage_enabled, bool)

    def test_api_keys_are_optional_strings_or_none(self):
        """API keys should be None (optional) when not provided."""
        settings = AgentSettings()
        assert settings.anthropic_api_key is None or isinstance(settings.anthropic_api_key, str)
        assert settings.openai_api_key is None or isinstance(settings.openai_api_key, str)

    def test_chroma_path_is_string(self):
        """chroma_path should be a non-empty string."""
        settings = AgentSettings()
        assert isinstance(settings.chroma_path, str)
        assert len(settings.chroma_path) > 0

    def test_chroma_collection_is_string(self):
        """chroma_collection should be a non-empty string."""
        settings = AgentSettings()
        assert isinstance(settings.chroma_collection, str)
        assert len(settings.chroma_collection) > 0


class TestPortConstraints:
    """Test port validation constraints."""

    def test_default_port_in_valid_range(self):
        """Default port 8765 is within the 1024-65535 range."""
        settings = AgentSettings()
        assert 1024 <= settings.port <= 65535

    def test_minimum_valid_port(self):
        """Port 1024 is the minimum valid value."""
        settings = AgentSettings(port=1024)
        assert settings.port == 1024

    def test_maximum_valid_port(self):
        """Port 65535 is the maximum valid value."""
        settings = AgentSettings(port=65535)
        assert settings.port == 65535

    def test_port_too_low_raises_validation_error(self):
        """Port below 1024 should raise a ValidationError."""
        with pytest.raises(ValidationError):
            AgentSettings(port=80)

    def test_port_too_high_raises_validation_error(self):
        """Port above 65535 should raise a ValidationError."""
        with pytest.raises(ValidationError):
            AgentSettings(port=70000)


class TestChromaPathValidator:
    """Test the chroma_path field validator."""

    def test_trailing_slash_is_stripped(self):
        """validate_chroma_path should strip trailing slashes."""
        settings = AgentSettings(chroma_path="./data/chroma/")
        assert not settings.chroma_path.endswith("/")

    def test_multiple_trailing_slashes_stripped(self):
        """All trailing slashes should be stripped."""
        settings = AgentSettings(chroma_path="./data///")
        assert not settings.chroma_path.endswith("/")

    def test_path_without_trailing_slash_unchanged(self):
        """Path without trailing slash should remain unchanged."""
        settings = AgentSettings(chroma_path="./data/chroma")
        assert settings.chroma_path == "./data/chroma"

    def test_default_chroma_path_has_no_trailing_slash(self):
        """Default chroma_path should not end with '/'."""
        settings = AgentSettings()
        assert not settings.chroma_path.endswith("/")


class TestNumericConstraints:
    """Test numeric field constraints (ge/le bounds)."""

    def test_max_decompose_subtasks_minimum(self):
        """max_decompose_subtasks must be >= 3."""
        settings = AgentSettings(max_decompose_subtasks=3)
        assert settings.max_decompose_subtasks == 3

    def test_max_decompose_subtasks_maximum(self):
        """max_decompose_subtasks must be <= 15."""
        settings = AgentSettings(max_decompose_subtasks=15)
        assert settings.max_decompose_subtasks == 15

    def test_max_decompose_subtasks_too_low_raises(self):
        """max_decompose_subtasks below 3 should raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentSettings(max_decompose_subtasks=2)

    def test_search_results_limit_minimum(self):
        """search_results_limit must be >= 1."""
        settings = AgentSettings(search_results_limit=1)
        assert settings.search_results_limit == 1

    def test_search_results_limit_maximum(self):
        """search_results_limit must be <= 50."""
        settings = AgentSettings(search_results_limit=50)
        assert settings.search_results_limit == 50

    def test_search_results_limit_too_high_raises(self):
        """search_results_limit above 50 should raise ValidationError."""
        with pytest.raises(ValidationError):
            AgentSettings(search_results_limit=51)
