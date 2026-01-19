"""Context layers for the layered context architecture.

Layer 1: Global Project Context (static, per-board)
Layer 2: Relevant Tickets Context (dynamic, via ChromaDB retrieval)
Layer 3: Current Operation Context (specific to the action)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum, auto


class ContextPriority(Enum):
    """Priority levels for context inclusion when budget is tight."""
    CRITICAL = auto()    # Must include, core to operation
    HIGH = auto()        # Very important, include if possible
    MEDIUM = auto()      # Helpful, include if space permits
    LOW = auto()         # Nice to have, can be dropped


@dataclass
class ContextLayer(ABC):
    """Base class for context layers.

    Each layer represents a different scope of context:
    - Global: Board-wide static information
    - Relevant: Dynamically retrieved similar/related tickets
    - Operation: Specific to the current action being performed
    """

    priority: ContextPriority = ContextPriority.MEDIUM
    estimated_tokens: int = 0

    @abstractmethod
    def to_string(self) -> str:
        """Convert the context layer to a string representation."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the context layer to a dictionary."""
        pass

    @abstractmethod
    def summarize(self, max_tokens: int) -> str:
        """Create a summarized version within token budget."""
        pass


@dataclass
class GlobalContext(ContextLayer):
    """Layer 1: Global Project Context.

    Contains static, board-wide information:
    - Board name and description
    - Available columns/statuses
    - All labels in use
    - Project conventions
    - Team workflow patterns
    """

    board_id: str = ""
    board_name: str = ""
    board_description: str = ""
    columns: list[dict[str, Any]] = field(default_factory=list)
    all_labels: list[str] = field(default_factory=list)
    workflow_description: str = ""
    conventions: dict[str, Any] = field(default_factory=dict)

    # Statistics for context
    total_tickets: int = 0
    tickets_by_status: dict[str, int] = field(default_factory=dict)
    tickets_by_priority: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        self.priority = ContextPriority.HIGH
        self._estimate_tokens()

    def _estimate_tokens(self) -> None:
        """Estimate token count for this context."""
        # Rough estimate: ~4 chars per token
        text = self.to_string()
        self.estimated_tokens = len(text) // 4

    def to_string(self) -> str:
        """Convert to prompt-friendly string."""
        parts = []

        if self.board_name:
            parts.append(f"Board: {self.board_name}")
        if self.board_description:
            parts.append(f"Description: {self.board_description}")

        if self.columns:
            column_names = [c.get("name", c.get("id", "")) for c in self.columns]
            parts.append(f"Columns: {' -> '.join(column_names)}")

        if self.all_labels:
            parts.append(f"Available labels: {', '.join(self.all_labels[:20])}")
            if len(self.all_labels) > 20:
                parts.append(f"  ... and {len(self.all_labels) - 20} more")

        if self.workflow_description:
            parts.append(f"Workflow: {self.workflow_description}")

        if self.total_tickets > 0:
            parts.append(f"Total tickets: {self.total_tickets}")
            if self.tickets_by_status:
                status_str = ", ".join(
                    f"{k}: {v}" for k, v in self.tickets_by_status.items()
                )
                parts.append(f"By status: {status_str}")

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "board_id": self.board_id,
            "board_name": self.board_name,
            "board_description": self.board_description,
            "columns": self.columns,
            "all_labels": self.all_labels,
            "workflow_description": self.workflow_description,
            "conventions": self.conventions,
            "total_tickets": self.total_tickets,
            "tickets_by_status": self.tickets_by_status,
            "tickets_by_priority": self.tickets_by_priority,
        }

    def summarize(self, max_tokens: int) -> str:
        """Create a summarized version within token budget."""
        max_chars = max_tokens * 4
        full_string = self.to_string()

        if len(full_string) <= max_chars:
            return full_string

        # Prioritize: board name, columns, labels (truncated)
        parts = []
        if self.board_name:
            parts.append(f"Board: {self.board_name}")
        if self.columns:
            column_names = [c.get("name", "") for c in self.columns[:5]]
            parts.append(f"Columns: {' -> '.join(column_names)}")
        if self.all_labels:
            parts.append(f"Labels: {', '.join(self.all_labels[:10])}")

        return "\n".join(parts)[:max_chars]


@dataclass
class RelevantTicketsContext(ContextLayer):
    """Layer 2: Relevant Tickets Context.

    Contains dynamically retrieved tickets from ChromaDB:
    - Semantically similar tickets to the current operation
    - Recently modified tickets in the same area
    - Tickets with shared labels/priority
    """

    similar_tickets: list[dict[str, Any]] = field(default_factory=list)
    related_by_labels: list[dict[str, Any]] = field(default_factory=list)
    recently_modified: list[dict[str, Any]] = field(default_factory=list)

    # Retrieval metadata
    query_used: str = ""
    similarity_threshold: float = 0.5
    max_tickets: int = 10

    def __post_init__(self):
        self.priority = ContextPriority.HIGH
        self._estimate_tokens()

    def _estimate_tokens(self) -> None:
        """Estimate token count for this context."""
        text = self.to_string()
        self.estimated_tokens = len(text) // 4

    def _format_ticket(self, ticket: dict[str, Any], include_description: bool = True) -> str:
        """Format a single ticket for context."""
        parts = [f"- [{ticket.get('id', 'N/A')[:8]}] {ticket.get('title', 'Untitled')}"]

        if ticket.get("status"):
            parts[0] += f" ({ticket['status']})"

        if ticket.get("priority"):
            parts[0] += f" [Priority: {ticket['priority']}]"

        if ticket.get("labels"):
            labels = ticket["labels"]
            if isinstance(labels, list):
                parts[0] += f" Labels: {', '.join(labels[:3])}"

        if include_description and ticket.get("description"):
            desc = ticket["description"][:200]
            if len(ticket.get("description", "")) > 200:
                desc += "..."
            parts.append(f"  {desc}")

        if ticket.get("score"):
            parts.append(f"  Relevance: {ticket['score']:.2f}")

        return "\n".join(parts)

    def to_string(self) -> str:
        """Convert to prompt-friendly string."""
        parts = []

        if self.similar_tickets:
            parts.append("## Similar Tickets")
            for ticket in self.similar_tickets[:5]:
                parts.append(self._format_ticket(ticket))

        if self.related_by_labels:
            parts.append("\n## Related by Labels")
            for ticket in self.related_by_labels[:3]:
                parts.append(self._format_ticket(ticket, include_description=False))

        if self.recently_modified:
            parts.append("\n## Recently Modified")
            for ticket in self.recently_modified[:3]:
                parts.append(self._format_ticket(ticket, include_description=False))

        if not parts:
            return "No related tickets found."

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "similar_tickets": self.similar_tickets,
            "related_by_labels": self.related_by_labels,
            "recently_modified": self.recently_modified,
            "query_used": self.query_used,
            "similarity_threshold": self.similarity_threshold,
        }

    def summarize(self, max_tokens: int) -> str:
        """Create a summarized version within token budget."""
        max_chars = max_tokens * 4

        # Only include most relevant similar tickets
        parts = []
        if self.similar_tickets:
            parts.append("Similar tickets:")
            for ticket in self.similar_tickets[:3]:
                title = ticket.get("title", "Untitled")[:50]
                parts.append(f"- {title}")

        result = "\n".join(parts)
        return result[:max_chars]

    def get_similar_tickets_json(self) -> str:
        """Get similar tickets as JSON string for DSPy modules."""
        import json

        tickets_for_json = []
        for ticket in self.similar_tickets:
            tickets_for_json.append({
                "id": ticket.get("id", ""),
                "title": ticket.get("title", ""),
                "description": ticket.get("description", "")[:300],
                "status": ticket.get("status", ""),
                "priority": ticket.get("priority", ""),
                "labels": ticket.get("labels", []),
            })

        return json.dumps(tickets_for_json, ensure_ascii=False)


@dataclass
class OperationContext(ContextLayer):
    """Layer 3: Current Operation Context.

    Contains information specific to the current action:
    - Operation type (triage, decompose, chat, etc.)
    - Target ticket details
    - User intent/request
    - Additional parameters
    """

    operation_type: str = ""
    target_ticket: Optional[dict[str, Any]] = None
    user_intent: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)

    # Operation-specific data
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    selected_tickets: list[dict[str, Any]] = field(default_factory=list)
    time_context: str = ""  # e.g., "morning standup", "end of sprint"

    def __post_init__(self):
        self.priority = ContextPriority.CRITICAL
        self._estimate_tokens()

    def _estimate_tokens(self) -> None:
        """Estimate token count for this context."""
        text = self.to_string()
        self.estimated_tokens = len(text) // 4

    def to_string(self) -> str:
        """Convert to prompt-friendly string."""
        parts = []

        if self.operation_type:
            parts.append(f"Operation: {self.operation_type}")

        if self.user_intent:
            parts.append(f"User intent: {self.user_intent}")

        if self.target_ticket:
            parts.append(f"Target ticket: {self.target_ticket.get('title', 'N/A')}")
            if self.target_ticket.get("description"):
                parts.append(f"Description: {self.target_ticket['description']}")

        if self.time_context:
            parts.append(f"Time context: {self.time_context}")

        if self.conversation_history:
            parts.append("Recent conversation:")
            for msg in self.conversation_history[-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")[:100]
                parts.append(f"  {role}: {content}")

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_type": self.operation_type,
            "target_ticket": self.target_ticket,
            "user_intent": self.user_intent,
            "parameters": self.parameters,
            "conversation_history": self.conversation_history,
            "selected_tickets": self.selected_tickets,
            "time_context": self.time_context,
        }

    def summarize(self, max_tokens: int) -> str:
        """Create a summarized version within token budget."""
        max_chars = max_tokens * 4

        parts = []
        if self.operation_type:
            parts.append(f"Operation: {self.operation_type}")
        if self.user_intent:
            parts.append(f"Intent: {self.user_intent[:100]}")
        if self.target_ticket:
            parts.append(f"Ticket: {self.target_ticket.get('title', 'N/A')[:50]}")

        return "\n".join(parts)[:max_chars]
