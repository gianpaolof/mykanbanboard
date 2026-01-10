"""Configuration management using pydantic-settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Agent configuration with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Configuration
    anthropic_api_key: Optional[str] = Field(
        None,
        description="Anthropic API key for Claude (optional)",
    )
    openai_api_key: Optional[str] = Field(
        None,
        description="OpenAI API key",
    )
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: 'openai' or 'anthropic'",
    )
    default_model: str = Field(
        default="gpt-4o-mini",
        description="Primary LLM model to use",
    )
    fallback_model: str = Field(
        default="gpt-4o-mini",
        description="Fallback model if primary fails",
    )

    # Embedding Configuration
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Model for generating embeddings",
    )
    embedding_dimensions: int = Field(
        default=1536,
        description="Embedding vector dimensions",
    )

    # Database Configuration
    chroma_path: str = Field(
        default="./data/chroma",
        description="Path to ChromaDB storage",
    )
    chroma_collection: str = Field(
        default="tickets",
        description="ChromaDB collection name",
    )

    # Server Configuration
    port: int = Field(
        default=8765,
        ge=1024,
        le=65535,
        description="Server port",
    )
    host: str = Field(
        default="127.0.0.1",
        description="Server host",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Behavior Configuration
    auto_triage_enabled: bool = Field(
        default=True,
        description="Enable automatic ticket triage",
    )
    max_decompose_subtasks: int = Field(
        default=7,
        ge=3,
        le=15,
        description="Maximum number of subtasks when decomposing",
    )
    search_results_limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum search results to return",
    )

    # Rate Limiting
    max_requests_per_minute: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum requests per minute",
    )

    @field_validator("chroma_path")
    @classmethod
    def validate_chroma_path(cls, v: str) -> str:
        """Ensure chroma_path is normalized."""
        return v.rstrip("/")


# Global settings instance
settings = AgentSettings()
