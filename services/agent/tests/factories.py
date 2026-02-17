"""Test data factories anchored to real Pydantic models.

Fails at import time if required fields change — not inside tests.
"""

from typing import Any

# Import the actual Pydantic models to anchor factories.
# If these imports fail, the model has changed and tests need updating.
from src.api.models import TriageRequest  # noqa: F401 — validates model exists


def make_triage_request(**overrides: Any) -> dict[str, Any]:
    """Factory for triage request data. Matches TriageRequest model."""
    defaults: dict[str, Any] = {
        "ticket_id": "test-123",
        "title": "Fix login bug on Safari",
        "description": "Users report they cannot login when using Safari browser",
        "existing_labels": ["bug", "auth", "browser"],
    }
    return {**defaults, **overrides}


def make_sample_board_context() -> dict[str, Any]:
    """Factory for board context data."""
    return {
        "board_id": "board-1",
        "board_name": "Test Board",
        "tickets": [],
        "columns": ["Todo", "In Progress", "Done"],
    }
