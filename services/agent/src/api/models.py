"""Pydantic models for API request/response validation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# TRIAGE MODELS
# ============================================================================


class TriageRequest(BaseModel):
    """Request model for ticket triage."""

    ticket_id: str = Field(..., description="Ticket UUID")
    title: str = Field(..., min_length=1, max_length=500, description="Ticket title")
    description: str = Field(default="", description="Ticket description")
    existing_labels: list[str] = Field(
        default_factory=list,
        description="Labels already in use on the board",
    )


class TriageResponse(BaseModel):
    """Response model for ticket triage."""

    priority: Literal["low", "medium", "high", "critical"]
    labels: list[str] = Field(..., max_length=3)
    effort: Literal["xs", "s", "m", "l", "xl"]
    reasoning: str


# ============================================================================
# DECOMPOSE MODELS
# ============================================================================


class SubtaskDict(BaseModel):
    """Subtask structure."""

    title: str
    description: str
    effort: Literal["xs", "s", "m", "l", "xl"]


class DecomposeRequest(BaseModel):
    """Request model for task decomposition."""

    ticket_id: str = Field(..., description="Ticket UUID to decompose")
    title: str = Field(..., min_length=1, description="Task title")
    description: str = Field(default="", description="Task description")
    context: Optional[str] = Field(None, description="Additional board context")


class DecomposeResponse(BaseModel):
    """Response model for task decomposition."""

    subtasks: list[SubtaskDict]
    dependencies: list[tuple[int, int]] = Field(
        default_factory=list,
        description="Dependency pairs (subtask_index, depends_on_index)",
    )
    reasoning: str


# ============================================================================
# CHAT MODELS
# ============================================================================


class ChatRequest(BaseModel):
    """Request model for chat interaction."""

    message: str = Field(..., min_length=1, description="User message")
    context: dict | None = Field(
        default=None,
        description="Current board context",
    )


class ChatResponse(BaseModel):
    """Response model for chat interaction."""

    action: Literal["create", "update", "move", "search", "summarize", "decompose", "none"]
    params: dict = Field(default_factory=dict)
    response: str


# ============================================================================
# SEARCH MODELS
# ============================================================================


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")


class SearchResult(BaseModel):
    """Single search result."""

    id: str
    title: str
    description: str
    score: float = Field(..., ge=0.0, le=1.0)
    explanation: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search."""

    results: list[SearchResult]
    query: str


# ============================================================================
# DAILY SUMMARY MODELS
# ============================================================================


class TicketSummary(BaseModel):
    """Minimal ticket info for summary."""

    id: str
    title: str
    status: str
    priority: Optional[str] = None
    due_date: Optional[str] = None


class DailySummaryResponse(BaseModel):
    """Response model for daily summary."""

    greeting: str
    focus_today: list[str] = Field(..., max_length=3)
    blockers: list[str]
    quick_wins: list[str]


# ============================================================================
# AUTOMATION RULE MODELS
# ============================================================================


class ParseRuleRequest(BaseModel):
    """Request model for parsing natural language automation rules."""

    natural_language: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language description of the automation rule",
    )
    board_context: dict | None = Field(
        default=None,
        description="Board context (columns, labels, etc.)",
    )


class ParseRuleResponse(BaseModel):
    """Response model for parsed automation rule."""

    rule_name: str = Field(..., max_length=50)
    trigger_type: Literal[
        "ticket_created",
        "ticket_moved",
        "ticket_updated",
        "label_added",
        "label_removed",
        "due_date_approaching",
        "priority_changed",
    ]
    trigger_config: dict = Field(default_factory=dict)
    action_type: Literal[
        "move_ticket",
        "set_priority",
        "add_label",
        "remove_label",
        "set_due_date",
        "notify",
        "auto_triage",
    ]
    action_config: dict = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str


# ============================================================================
# ERROR MODELS
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    details: dict = Field(default_factory=dict)
