"""Context Manager - High-level orchestration for context management.

The ContextManager is the main entry point for the context system.
It coordinates the ContextBuilder, ChromaDB sync, and provides
a simple interface for the API routes.
"""

import logging
from typing import Any, Optional
from dataclasses import dataclass

from .builder import ContextBuilder, BuiltContext, OperationType
from .cache import ContextCache, get_global_cache
from .token_budget import TokenBudgetManager

logger = logging.getLogger(__name__)


@dataclass
class SyncStatus:
    """Status of ChromaDB sync with SQLite."""
    is_synced: bool = False
    last_sync_at: Optional[str] = None
    tickets_in_chroma: int = 0
    tickets_in_sqlite: int = 0
    missing_in_chroma: int = 0
    orphaned_in_chroma: int = 0


class ContextManager:
    """High-level context management for Kanban AI.

    The ContextManager:
    1. Provides a simple interface for API routes
    2. Manages ChromaDB sync with SQLite
    3. Coordinates context building across operations
    4. Handles cache invalidation

    Usage in routes:
        context_manager = ContextManager(chroma_manager)

        # For triage
        context = context_manager.get_triage_context(ticket, board_data)
        result = triage_module(
            title=ticket["title"],
            description=ticket["description"],
            existing_labels=context.get_existing_labels(),
        )

        # For analyze
        context = context_manager.get_analyze_context(ticket, board_data)
        result = analyzer(
            ticket_title=ticket["title"],
            ticket_description=ticket["description"],
            similar_tickets=context.get_similar_tickets_json(),
        )
    """

    def __init__(
        self,
        chroma_manager: Optional[Any] = None,
        cache: Optional[ContextCache] = None,
    ):
        """Initialize the context manager.

        Args:
            chroma_manager: ChromaDB manager instance
            cache: Optional custom cache
        """
        self.chroma = chroma_manager
        self.cache = cache or get_global_cache()
        self.token_manager = TokenBudgetManager()
        self.builder = ContextBuilder(
            chroma_manager=chroma_manager,
            token_budget_manager=self.token_manager,
            cache=self.cache,
        )
        self._sync_status = SyncStatus()

    # =========================================================================
    # SYNC MANAGEMENT
    # =========================================================================

    async def sync_tickets_to_chroma(
        self,
        tickets: list[dict[str, Any]],
        force_full_sync: bool = False,
    ) -> SyncStatus:
        """Sync tickets from SQLite to ChromaDB.

        This should be called:
        - On startup (full sync)
        - When tickets are created/updated/deleted (incremental)
        - Periodically as a background task

        Args:
            tickets: List of ticket dictionaries from SQLite
            force_full_sync: If True, clear ChromaDB and re-sync all

        Returns:
            SyncStatus with sync results
        """
        if not self.chroma:
            logger.warning("ChromaDB not available, skipping sync")
            return self._sync_status

        try:
            if force_full_sync:
                logger.info("Starting full ChromaDB sync...")
                self.chroma.clear_all()

            # Get existing IDs in ChromaDB
            existing_ids = set()
            try:
                stats = self.chroma.get_stats()
                existing_count = stats.get("total_documents", 0)
                logger.debug(f"ChromaDB has {existing_count} documents")
            except Exception:
                existing_count = 0

            # Sync each ticket
            synced_count = 0
            for ticket in tickets:
                ticket_id = ticket.get("id")
                if not ticket_id:
                    continue

                try:
                    # Prepare metadata
                    metadata = {
                        "status": ticket.get("status", ""),
                        "priority": ticket.get("priority", ""),
                        "column_id": ticket.get("column_id", ""),
                    }

                    # Handle labels (ChromaDB metadata must be primitive types)
                    labels = ticket.get("labels", [])
                    if isinstance(labels, list):
                        metadata["labels_str"] = ",".join(labels)

                    self.chroma.add_ticket(
                        ticket_id=ticket_id,
                        title=ticket.get("title", ""),
                        description=ticket.get("description", ""),
                        metadata=metadata,
                    )
                    synced_count += 1

                except Exception as e:
                    logger.error(f"Failed to sync ticket {ticket_id}: {e}")

            # Update sync status
            import datetime
            self._sync_status = SyncStatus(
                is_synced=True,
                last_sync_at=datetime.datetime.now().isoformat(),
                tickets_in_chroma=synced_count,
                tickets_in_sqlite=len(tickets),
                missing_in_chroma=len(tickets) - synced_count,
            )

            logger.info(f"Synced {synced_count}/{len(tickets)} tickets to ChromaDB")

            # Invalidate relevant caches
            self.cache.invalidate_pattern("similar_tickets:")

            return self._sync_status

        except Exception as e:
            logger.error(f"ChromaDB sync failed: {e}")
            self._sync_status.is_synced = False
            return self._sync_status

    async def sync_single_ticket(
        self,
        ticket: dict[str, Any],
        action: str = "upsert",  # "upsert" or "delete"
    ) -> bool:
        """Sync a single ticket to/from ChromaDB.

        Args:
            ticket: Ticket data
            action: "upsert" to add/update, "delete" to remove

        Returns:
            True if successful
        """
        if not self.chroma:
            return False

        ticket_id = ticket.get("id")
        if not ticket_id:
            return False

        try:
            if action == "delete":
                self.chroma.remove_ticket(ticket_id)
                logger.debug(f"Removed ticket {ticket_id} from ChromaDB")
            else:
                metadata = {
                    "status": ticket.get("status", ""),
                    "priority": ticket.get("priority", ""),
                    "column_id": ticket.get("column_id", ""),
                }
                labels = ticket.get("labels", [])
                if isinstance(labels, list):
                    metadata["labels_str"] = ",".join(labels)

                self.chroma.add_ticket(
                    ticket_id=ticket_id,
                    title=ticket.get("title", ""),
                    description=ticket.get("description", ""),
                    metadata=metadata,
                )
                logger.debug(f"Upserted ticket {ticket_id} to ChromaDB")

            # Invalidate cache for queries that might include this ticket
            self.cache.invalidate_pattern("similar_tickets:")

            return True

        except Exception as e:
            logger.error(f"Failed to sync ticket {ticket_id}: {e}")
            return False

    def get_sync_status(self) -> SyncStatus:
        """Get the current sync status."""
        return self._sync_status

    # =========================================================================
    # CONTEXT RETRIEVAL FOR OPERATIONS
    # =========================================================================

    def get_triage_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Get context for triage operation.

        Args:
            ticket: Ticket to triage
            board_data: Board data with labels, columns, etc.

        Returns:
            BuiltContext with relevant information
        """
        return self.builder.build_triage_context(ticket, board_data)

    def get_decompose_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Get context for decomposition operation.

        Args:
            ticket: Ticket to decompose
            board_data: Board data

        Returns:
            BuiltContext with relevant information
        """
        return self.builder.build_decompose_context(ticket, board_data)

    def get_chat_context(
        self,
        message: str,
        board_data: Optional[dict[str, Any]] = None,
        conversation_history: Optional[list[dict]] = None,
        current_ticket: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Get context for chat operation.

        Args:
            message: User's message
            board_data: Board data
            conversation_history: Previous turns
            current_ticket: Currently selected ticket

        Returns:
            BuiltContext with relevant information
        """
        return self.builder.build_chat_context(
            message=message,
            board_data=board_data,
            conversation_history=conversation_history,
            current_ticket=current_ticket,
        )

    def get_daily_summary_context(
        self,
        in_progress: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
        due_soon: list[dict[str, Any]],
        recently_completed: Optional[list[dict[str, Any]]] = None,
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Get context for daily summary operation.

        Args:
            in_progress: Tickets in progress
            blocked: Blocked tickets
            due_soon: Tickets due soon
            recently_completed: Recently completed tickets
            board_data: Board data

        Returns:
            BuiltContext with relevant information
        """
        return self.builder.build_daily_summary_context(
            in_progress=in_progress,
            blocked=blocked,
            due_soon=due_soon,
            recently_completed=recently_completed,
            board_data=board_data,
        )

    def get_analyze_context(
        self,
        ticket: dict[str, Any],
        board_data: Optional[dict[str, Any]] = None,
    ) -> BuiltContext:
        """Get context for multi-hop analysis operation.

        Args:
            ticket: Ticket to analyze
            board_data: Board data

        Returns:
            BuiltContext with relevant information
        """
        return self.builder.build_analyze_context(ticket, board_data)

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    def invalidate_board_cache(self, board_id: str) -> int:
        """Invalidate all cached data for a board.

        Call when board structure changes.

        Args:
            board_id: Board ID

        Returns:
            Number of entries invalidated
        """
        return self.cache.invalidate_board(board_id)

    def clear_all_cache(self) -> None:
        """Clear all cached context data."""
        self.cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


# Singleton instance for global access
_context_manager: Optional[ContextManager] = None


def get_context_manager(chroma_manager: Optional[Any] = None) -> ContextManager:
    """Get or create the global ContextManager instance.

    Args:
        chroma_manager: ChromaDB manager (only used on first call)

    Returns:
        ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager(chroma_manager=chroma_manager)
    return _context_manager


def init_context_manager(chroma_manager: Any) -> ContextManager:
    """Initialize the global ContextManager with a ChromaDB manager.

    Call this during application startup.

    Args:
        chroma_manager: ChromaDB manager instance

    Returns:
        Initialized ContextManager
    """
    global _context_manager
    _context_manager = ContextManager(chroma_manager=chroma_manager)
    return _context_manager
