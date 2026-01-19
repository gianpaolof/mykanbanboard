"""Context Builder - Smart context construction for DSPy modules.

The ContextBuilder determines what context each DSPy module needs,
retrieves relevant tickets from ChromaDB, and builds compact context
strings within token limits.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Type
from enum import Enum, auto

from .layers import (
    ContextLayer,
    GlobalContext,
    RelevantTicketsContext,
    OperationContext,
)
from .token_budget import TokenBudgetManager, TokenBudget
from .cache import ContextCache, get_global_cache

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations that require context."""
    TRIAGE = auto()
    DECOMPOSE = auto()
    CHAT = auto()
    DAILY_SUMMARY = auto()
    ANALYZE = auto()
    SEARCH = auto()
    JUDGE = auto()
    PARSE_RULE = auto()


@dataclass
class ContextRequirements:
    """Defines what context a specific operation needs."""
    operation: OperationType
    needs_global_context: bool = True
    needs_similar_tickets: bool = True
    needs_label_context: bool = True
    similar_tickets_count: int = 5
    include_ticket_descriptions: bool = True
    include_conversation_history: bool = False
    max_conversation_turns: int = 3


# Context requirements per operation type
OPERATION_REQUIREMENTS: dict[OperationType, ContextRequirements] = {
    OperationType.TRIAGE: ContextRequirements(
        operation=OperationType.TRIAGE,
        needs_global_context=True,
        needs_similar_tickets=True,
        needs_label_context=True,
        similar_tickets_count=5,
        include_ticket_descriptions=True,
    ),
    OperationType.DECOMPOSE: ContextRequirements(
        operation=OperationType.DECOMPOSE,
        needs_global_context=True,
        needs_similar_tickets=True,
        needs_label_context=False,
        similar_tickets_count=3,
        include_ticket_descriptions=True,
    ),
    OperationType.CHAT: ContextRequirements(
        operation=OperationType.CHAT,
        needs_global_context=True,
        needs_similar_tickets=True,
        needs_label_context=True,
        similar_tickets_count=5,
        include_ticket_descriptions=True,
        include_conversation_history=True,
        max_conversation_turns=5,
    ),
    OperationType.DAILY_SUMMARY: ContextRequirements(
        operation=OperationType.DAILY_SUMMARY,
        needs_global_context=True,
        needs_similar_tickets=False,  # Uses direct ticket lists instead
        needs_label_context=False,
        similar_tickets_count=0,
        include_ticket_descriptions=True,
    ),
    OperationType.ANALYZE: ContextRequirements(
        operation=OperationType.ANALYZE,
        needs_global_context=True,
        needs_similar_tickets=True,
        needs_label_context=True,
        similar_tickets_count=10,  # More for deep analysis
        include_ticket_descriptions=True,
    ),
    OperationType.SEARCH: ContextRequirements(
        operation=OperationType.SEARCH,
        needs_global_context=False,
        needs_similar_tickets=False,
        needs_label_context=False,
        similar_tickets_count=0,
    ),
    OperationType.JUDGE: ContextRequirements(
        operation=OperationType.JUDGE,
        needs_global_context=True,
        needs_similar_tickets=True,
        needs_label_context=True,
        similar_tickets_count=3,
        include_ticket_descriptions=True,
    ),
    OperationType.PARSE_RULE: ContextRequirements(
        operation=OperationType.PARSE_RULE,
        needs_global_context=True,
        needs_similar_tickets=False,
        needs_label_context=True,
        similar_tickets_count=0,
    ),
}


@dataclass
class BuiltContext:
    """The final built context ready for use in DSPy modules."""
    global_context: Optional[GlobalContext] = None
    relevant_context: Optional[RelevantTicketsContext] = None
    operation_context: Optional[OperationContext] = None
    token_budget: Optional[TokenBudget] = None

    # Convenience accessors for common patterns
    def get_existing_labels(self) -> list[str]:
        """Get all existing labels for triage."""
        if self.global_context:
            return self.global_context.all_labels
        return []

    def get_similar_tickets_json(self) -> str:
        """Get similar tickets as JSON string for multi-hop analysis."""
        if self.relevant_context:
            return self.relevant_context.get_similar_tickets_json()
        return "[]"

    def get_board_context_dict(self) -> dict[str, Any]:
        """Get board context as dict for chat/rule parsing."""
        result = {}
        if self.global_context:
            result.update(self.global_context.to_dict())
        if self.relevant_context:
            result["similar_tickets"] = self.relevant_context.similar_tickets
        if self.operation_context:
            result["current_operation"] = self.operation_context.to_dict()
        return result

    def get_decompose_context(self) -> str:
        """Get context string for decomposition."""
        parts = []
        if self.global_context:
            parts.append(f"Board: {self.global_context.board_name}")
            if self.global_context.columns:
                columns = [c.get("name", "") for c in self.global_context.columns]
                parts.append(f"Workflow: {' -> '.join(columns)}")

        if self.relevant_context and self.relevant_context.similar_tickets:
            parts.append("\nSimilar tasks for reference:")
            for ticket in self.relevant_context.similar_tickets[:3]:
                parts.append(f"- {ticket.get('title', 'N/A')}")

        return "\n".join(parts) if parts else "No additional context available."

    def get_daily_summary_tickets(self) -> dict[str, list[dict]]:
        """Get categorized tickets for daily summary."""
        if not self.operation_context:
            return {
                "in_progress": [],
                "blocked": [],
                "due_soon": [],
                "recently_completed": [],
            }

        return {
            "in_progress": self.operation_context.parameters.get("in_progress", []),
            "blocked": self.operation_context.parameters.get("blocked", []),
            "due_soon": self.operation_context.parameters.get("due_soon", []),
            "recently_completed": self.operation_context.parameters.get("recently_completed", []),
        }

    def to_full_string(self) -> str:
        """Convert all context to a single string."""
        parts = []

        if self.global_context:
            parts.append("=== Board Context ===")
            parts.append(self.global_context.to_string())

        if self.relevant_context:
            parts.append("\n=== Related Tickets ===")
            parts.append(self.relevant_context.to_string())

        if self.operation_context:
            parts.append("\n=== Current Operation ===")
            parts.append(self.operation_context.to_string())

        return "\n".join(parts)


class ContextBuilder:
    """Builds context for DSPy modules.

    The builder:
    1. Determines what context is needed based on operation type
    2. Retrieves relevant tickets from ChromaDB
    3. Builds compact context strings within token limits
    4. Caches expensive retrievals
    """

    def __init__(
        self,
        chroma_manager: Optional[Any] = None,  # ChromaManager
        token_budget_manager: Optional[TokenBudgetManager] = None,
        cache: Optional[ContextCache] = None,
    ):
        """Initialize the context builder.

        Args:
            chroma_manager: ChromaDB manager for ticket retrieval
            token_budget_manager: Manager for token budget allocation
            cache: Cache for expensive operations
        """
        self.chroma = chroma_manager
        self.token_manager = token_budget_manager or TokenBudgetManager()
        self.cache = cache or get_global_cache()

    def build_context(
        self,
        operation: OperationType,
        target_ticket: Optional[dict[str, Any]] = None,
        board_data: Optional[dict[str, Any]] = None,
        additional_params: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context for a specific operation.

        Args:
            operation: Type of operation
            target_ticket: The ticket being operated on (if any)
            board_data: Board-level data (columns, labels, etc.)
            additional_params: Operation-specific parameters

        Returns:
            BuiltContext with all layers populated
        """
        requirements = OPERATION_REQUIREMENTS.get(
            operation,
            ContextRequirements(operation=operation)
        )

        board_data = board_data or {}
        additional_params = additional_params or {}

        # Build each layer based on requirements
        global_ctx = None
        relevant_ctx = None
        operation_ctx = None

        # Layer 1: Global Context
        if requirements.needs_global_context:
            global_ctx = self._build_global_context(board_data)

        # Layer 2: Relevant Tickets Context
        if requirements.needs_similar_tickets and target_ticket:
            relevant_ctx = self._build_relevant_context(
                target_ticket=target_ticket,
                limit=requirements.similar_tickets_count,
                include_descriptions=requirements.include_ticket_descriptions,
            )

        # Layer 3: Operation Context
        operation_ctx = self._build_operation_context(
            operation=operation,
            target_ticket=target_ticket,
            params=additional_params,
            requirements=requirements,
        )

        # Allocate token budget
        layers = {}
        if global_ctx:
            layers["global"] = global_ctx
        if relevant_ctx:
            layers["relevant"] = relevant_ctx
        if operation_ctx:
            layers["operation"] = operation_ctx

        token_budget = self.token_manager.allocate_budget(
            operation_type=operation.name.lower(),
            layers=layers,
        )

        # Apply budget constraints (truncate if needed)
        self._apply_budget_constraints(layers, token_budget)

        return BuiltContext(
            global_context=global_ctx,
            relevant_context=relevant_ctx,
            operation_context=operation_ctx,
            token_budget=token_budget,
        )

    def _build_global_context(
        self,
        board_data: dict[str, Any],
    ) -> GlobalContext:
        """Build the global context layer.

        Args:
            board_data: Board-level data

        Returns:
            GlobalContext instance
        """
        board_id = board_data.get("board_id", "default")

        # Try cache first
        cache_key = f"global_context:{board_id}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Global context cache hit for board {board_id}")
            return cached

        # Build fresh context
        context = GlobalContext(
            board_id=board_id,
            board_name=board_data.get("board_name", "Kanban Board"),
            board_description=board_data.get("description", ""),
            columns=board_data.get("columns", []),
            all_labels=board_data.get("labels", []),
            workflow_description=board_data.get("workflow", ""),
            conventions=board_data.get("conventions", {}),
            total_tickets=board_data.get("total_tickets", 0),
            tickets_by_status=board_data.get("tickets_by_status", {}),
            tickets_by_priority=board_data.get("tickets_by_priority", {}),
        )

        # Cache the result
        self.cache.set(cache_key, context, cache_type="global_context")

        return context

    def _build_relevant_context(
        self,
        target_ticket: dict[str, Any],
        limit: int = 5,
        include_descriptions: bool = True,
    ) -> RelevantTicketsContext:
        """Build the relevant tickets context layer.

        Args:
            target_ticket: The ticket to find similar tickets for
            limit: Maximum number of similar tickets
            include_descriptions: Whether to include ticket descriptions

        Returns:
            RelevantTicketsContext instance
        """
        title = target_ticket.get("title", "")
        description = target_ticket.get("description", "")
        query = f"{title} {description}".strip()

        if not query:
            return RelevantTicketsContext()

        # Try cache first
        cache_key = f"similar_tickets:{hash(query)}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Similar tickets cache hit")
            return cached

        # Retrieve from ChromaDB
        similar_tickets = []
        if self.chroma:
            try:
                results = self.chroma.search(query=query, limit=limit)
                for result in results:
                    ticket_data = {
                        "id": result.get("id", ""),
                        "title": result.get("title", ""),
                        "score": result.get("score", 0.0),
                    }
                    if include_descriptions:
                        ticket_data["description"] = result.get("description", "")

                    # Add metadata if available
                    metadata = result.get("metadata", {})
                    if metadata:
                        ticket_data["status"] = metadata.get("status", "")
                        ticket_data["priority"] = metadata.get("priority", "")
                        ticket_data["labels"] = metadata.get("labels", [])

                    similar_tickets.append(ticket_data)

                logger.debug(f"Found {len(similar_tickets)} similar tickets")

            except Exception as e:
                logger.warning(f"Failed to retrieve similar tickets: {e}")

        context = RelevantTicketsContext(
            similar_tickets=similar_tickets,
            query_used=query,
            max_tickets=limit,
        )

        # Cache the result
        self.cache.set(cache_key, context, cache_type="similar_tickets")

        return context

    def _build_operation_context(
        self,
        operation: OperationType,
        target_ticket: Optional[dict[str, Any]],
        params: dict[str, Any],
        requirements: ContextRequirements,
    ) -> OperationContext:
        """Build the operation context layer.

        Args:
            operation: Type of operation
            target_ticket: Target ticket if any
            params: Operation parameters
            requirements: Context requirements

        Returns:
            OperationContext instance
        """
        # Extract conversation history if needed
        conversation_history = []
        if requirements.include_conversation_history:
            history = params.get("conversation_history", [])
            conversation_history = history[-requirements.max_conversation_turns:]

        return OperationContext(
            operation_type=operation.name,
            target_ticket=target_ticket,
            user_intent=params.get("user_intent", ""),
            parameters=params,
            conversation_history=conversation_history,
            selected_tickets=params.get("selected_tickets", []),
            time_context=params.get("time_context", ""),
        )

    def _apply_budget_constraints(
        self,
        layers: dict[str, ContextLayer],
        budget: TokenBudget,
    ) -> None:
        """Apply token budget constraints to context layers.

        This method modifies layers in place to fit within budget.

        Args:
            layers: Dictionary of context layers
            budget: Token budget with allocations
        """
        for allocation in budget.allocations:
            if not allocation.was_truncated:
                continue

            layer = layers.get(allocation.layer_name)
            if layer is None:
                continue

            # Summarize the layer to fit budget
            logger.debug(
                f"Summarizing {allocation.layer_name} from "
                f"{allocation.requested_tokens} to {allocation.allocated_tokens} tokens"
            )
            # The summarize method will be called when converting to string

    # Convenience methods for specific operations

    def build_triage_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context specifically for triage operation.

        Args:
            ticket: Ticket to triage
            board_data: Board data with labels, etc.

        Returns:
            BuiltContext configured for triage
        """
        return self.build_context(
            operation=OperationType.TRIAGE,
            target_ticket=ticket,
            board_data=board_data,
        )

    def build_decompose_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context specifically for decomposition.

        Args:
            ticket: Ticket to decompose
            board_data: Board data

        Returns:
            BuiltContext configured for decomposition
        """
        return self.build_context(
            operation=OperationType.DECOMPOSE,
            target_ticket=ticket,
            board_data=board_data,
        )

    def build_chat_context(
        self,
        message: str,
        board_data: Optional[dict[str, Any]] = None,
        conversation_history: Optional[list[dict]] = None,
        current_ticket: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context specifically for chat interaction.

        Args:
            message: User's message
            board_data: Board data
            conversation_history: Previous conversation turns
            current_ticket: Currently selected ticket if any

        Returns:
            BuiltContext configured for chat
        """
        return self.build_context(
            operation=OperationType.CHAT,
            target_ticket=current_ticket,
            board_data=board_data,
            additional_params={
                "user_intent": message,
                "conversation_history": conversation_history or [],
            },
        )

    def build_daily_summary_context(
        self,
        in_progress: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        due_soon: list[dict[str, Any]],
        recently_completed: Optional[list[dict[str, Any]]] = None,
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context specifically for daily summary.

        Args:
            in_progress: Tickets currently in progress
            blocked: Blocked tickets
            due_soon: Tickets due soon
            recently_completed: Recently completed tickets
            board_data: Board data

        Returns:
            BuiltContext configured for daily summary
        """
        import datetime

        hour = datetime.datetime.now().hour
        if hour < 12:
            time_context = "morning"
        elif hour < 17:
            time_context = "afternoon"
        else:
            time_context = "evening"

        return self.build_context(
            operation=OperationType.DAILY_SUMMARY,
            target_ticket=None,
            board_data=board_data,
            additional_params={
                "in_progress": in_progress,
                "blocked": blocked,
                "due_soon": due_soon,
                "recently_completed": recently_completed or [],
                "time_context": time_context,
            },
        )

    def build_analyze_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Build context specifically for multi-hop analysis.

        Args:
            ticket: Ticket to analyze
            board_data: Board data

        Returns:
            BuiltContext configured for analysis
        """
        return self.build_context(
            operation=OperationType.ANALYZE,
            target_ticket=ticket,
            board_data=board_data,
        )

    def invalidate_board_cache(self, board_id: str) -> int:
        """Invalidate all cached context for a board.

        Call this when board structure changes (columns, labels, etc.).

        Args:
            board_id: Board ID to invalidate

        Returns:
            Number of cache entries invalidated
        """
        return self.cache.invalidate_board(board_id)
