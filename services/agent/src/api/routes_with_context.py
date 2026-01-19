"""FastAPI routes with Context Management System integration.

This file shows how to integrate the ContextManager with the existing routes.
Copy the relevant changes to routes.py when ready.

Key changes:
1. DailySummary receives ACTUAL ticket lists from frontend
2. MultiHopAnalyzer gets REAL similar tickets from ChromaDB
3. All operations benefit from layered context
4. Expensive retrievals are cached
"""

from typing import Any, Optional
import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from ..agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
)
from ..agent.multihop import MultiHopTicketAnalyzer
from ..db.chroma import ChromaManager
from ..context import ContextManager, get_context_manager, init_context_manager
from .models import (
    TriageRequest,
    TriageResponse,
    DecomposeRequest,
    DecomposeResponse,
    ChatRequest,
    ChatResponse,
    DailySummaryResponse,
    AnalyzeRequest,
    AnalyzeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# Timeout constants
TRIAGE_TIMEOUT = 12
DECOMPOSE_TIMEOUT = 12
CHAT_TIMEOUT = 12
DAILY_SUMMARY_TIMEOUT = 10
ANALYZE_TIMEOUT = 60


# ============================================================================
# NEW REQUEST MODELS (with context support)
# ============================================================================


class TicketData(BaseModel):
    """Ticket data for context."""
    id: str
    title: str
    description: str = ""
    status: str = ""
    priority: str = "medium"
    labels: list[str] = Field(default_factory=list)
    due_date: Optional[str] = None
    column_id: str = ""


class BoardContext(BaseModel):
    """Board context data."""
    board_id: str = "default"
    board_name: str = "Kanban Board"
    columns: list[dict[str, Any]] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    total_tickets: int = 0


class TriageRequestWithContext(TriageRequest):
    """Extended triage request with board context."""
    board_context: Optional[BoardContext] = None


class DecomposeRequestWithContext(DecomposeRequest):
    """Extended decompose request with board context."""
    board_context: Optional[BoardContext] = None


class DailySummaryRequest(BaseModel):
    """Request model for daily summary WITH actual ticket data."""
    in_progress: list[TicketData] = Field(default_factory=list)
    blocked: list[TicketData] = Field(default_factory=list)
    due_soon: list[TicketData] = Field(default_factory=list)
    recently_completed: list[TicketData] = Field(default_factory=list)
    board_context: Optional[BoardContext] = None


class AnalyzeRequestWithContext(AnalyzeRequest):
    """Extended analyze request with board context."""
    board_context: Optional[BoardContext] = None


class SyncTicketsRequest(BaseModel):
    """Request model for syncing tickets to ChromaDB."""
    tickets: list[TicketData]
    force_full_sync: bool = False


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_chroma_manager() -> ChromaManager:
    """Get ChromaDB manager instance."""
    return ChromaManager()


def get_ctx_manager(
    chroma: ChromaManager = Depends(get_chroma_manager),
) -> ContextManager:
    """Get ContextManager instance with ChromaDB."""
    return get_context_manager(chroma)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def run_with_timeout(coro, timeout_seconds: int, operation_name: str):
    """Run a coroutine with a timeout."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout_seconds}s")
        raise HTTPException(
            status_code=504,
            detail=f"{operation_name} timed out after {timeout_seconds} seconds.",
        )


def run_sync_with_timeout(func, timeout_seconds: int, operation_name: str):
    """Run a synchronous function in a thread pool with timeout."""
    async def wrapper():
        return await asyncio.to_thread(func)
    return run_with_timeout(wrapper(), timeout_seconds, operation_name)


def extract_value(obj: Any) -> Any:
    """Extract value from DSPy prediction object."""
    if obj is None:
        return None
    if callable(obj):
        return str(obj)
    if isinstance(obj, list):
        return [extract_value(item) for item in obj]
    if isinstance(obj, dict):
        return {k: extract_value(v) for k, v in obj.items()}
    return obj


# ============================================================================
# SYNC ENDPOINT (new)
# ============================================================================


@router.post(
    "/sync-tickets",
    summary="Sync tickets to ChromaDB",
    description="Sync ticket data from frontend/SQLite to ChromaDB for semantic search",
)
async def sync_tickets(
    request: SyncTicketsRequest,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> dict[str, Any]:
    """Sync tickets to ChromaDB.

    This endpoint should be called:
    - On app startup (with all tickets)
    - When tickets are created/updated/deleted
    - Periodically as a background sync

    Args:
        request: Tickets to sync

    Returns:
        Sync status
    """
    try:
        tickets = [t.model_dump() for t in request.tickets]
        status = await ctx_manager.sync_tickets_to_chroma(
            tickets=tickets,
            force_full_sync=request.force_full_sync,
        )

        return {
            "success": status.is_synced,
            "synced_count": status.tickets_in_chroma,
            "total_count": status.tickets_in_sqlite,
            "last_sync": status.last_sync_at,
        }

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


# ============================================================================
# TRIAGE ENDPOINT (updated with context)
# ============================================================================


@router.post(
    "/triage",
    response_model=TriageResponse,
    summary="Auto-triage a ticket with context",
)
async def triage_ticket(
    request: TriageRequestWithContext,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> TriageResponse:
    """Auto-triage a ticket using context-aware processing.

    The context manager:
    1. Retrieves similar tickets from ChromaDB
    2. Gets all existing labels for consistency
    3. Provides board context for better decisions
    """
    try:
        logger.info(f"Triaging ticket: {request.ticket_id}")

        # Build ticket data
        ticket = {
            "id": request.ticket_id,
            "title": request.title,
            "description": request.description,
        }

        # Build board context
        board_data = None
        if request.board_context:
            board_data = request.board_context.model_dump()
        elif request.existing_labels:
            board_data = {"labels": request.existing_labels}

        # Get context from ContextManager
        context = ctx_manager.get_triage_context(ticket, board_data)

        # Use context-enhanced labels (combines provided + retrieved)
        existing_labels = context.get_existing_labels()
        if request.existing_labels:
            # Merge and dedupe
            existing_labels = list(set(existing_labels + request.existing_labels))

        triage_module = TriageModule()

        def run_triage():
            return triage_module(
                title=request.title,
                description=request.description,
                existing_labels=existing_labels,
            )

        result = await run_sync_with_timeout(run_triage, TRIAGE_TIMEOUT, "Triage")

        # Extract and validate
        priority = extract_value(result.priority)
        labels_raw = extract_value(result.labels)
        labels = labels_raw if isinstance(labels_raw, list) else [labels_raw]
        labels = [str(l) for l in labels[:3]]
        effort = extract_value(result.effort_estimate)
        reasoning = extract_value(result.reasoning)

        return TriageResponse(
            priority=priority,
            labels=labels,
            effort=effort,
            reasoning=reasoning,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Triage failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Triage failed: {str(e)}")


# ============================================================================
# DECOMPOSE ENDPOINT (updated with context)
# ============================================================================


@router.post(
    "/decompose",
    response_model=DecomposeResponse,
    summary="Decompose a task with context",
)
async def decompose_task(
    request: DecomposeRequestWithContext,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> DecomposeResponse:
    """Decompose a task using context-aware processing.

    The context manager provides:
    1. Similar tasks for reference patterns
    2. Board workflow for context
    3. Related tickets for dependency hints
    """
    try:
        logger.info(f"Decomposing task: {request.ticket_id}")

        ticket = {
            "id": request.ticket_id,
            "title": request.title,
            "description": request.description,
        }

        board_data = None
        if request.board_context:
            board_data = request.board_context.model_dump()

        # Get rich context
        context = ctx_manager.get_decompose_context(ticket, board_data)

        # Build context string for decomposition
        context_string = context.get_decompose_context()

        # Override with explicit context if provided
        if request.context:
            context_string = f"{request.context}\n\n{context_string}"

        from ..agent.modules import DecomposeModule
        decompose_module = DecomposeModule()

        def run_decompose():
            return decompose_module(
                title=request.title,
                description=request.description,
                context=context_string,
            )

        result = await run_sync_with_timeout(run_decompose, DECOMPOSE_TIMEOUT, "Decompose")

        # Extract and normalize
        raw_subtasks = extract_value(result.subtasks)
        raw_dependencies = extract_value(result.dependencies)
        reasoning = extract_value(result.reasoning)

        def normalize_effort(effort: Any) -> str:
            effort_map = {
                "xs": "xs", "extra-small": "xs",
                "s": "s", "small": "s",
                "m": "m", "medium": "m",
                "l": "l", "large": "l",
                "xl": "xl", "extra-large": "xl",
            }
            return effort_map.get(str(effort).lower(), "m")

        subtasks = []
        if raw_subtasks:
            for subtask in raw_subtasks:
                if isinstance(subtask, dict):
                    normalized = {**subtask}
                    normalized["effort"] = normalize_effort(normalized.get("effort", "m"))
                    subtasks.append(normalized)
                else:
                    subtasks.append({
                        "title": str(subtask),
                        "description": "",
                        "effort": "m",
                    })

        dependencies = []
        if raw_dependencies:
            for dep in raw_dependencies:
                if isinstance(dep, (list, tuple)) and len(dep) == 2:
                    dependencies.append((int(dep[0]), int(dep[1])))

        return DecomposeResponse(
            subtasks=subtasks,
            dependencies=dependencies,
            reasoning=reasoning,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decomposition failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Decomposition failed: {str(e)}")


# ============================================================================
# DAILY SUMMARY ENDPOINT (FIXED - now receives actual tickets)
# ============================================================================


@router.post(
    "/daily-summary",
    response_model=DailySummaryResponse,
    summary="Get daily summary with actual ticket data",
    description="Generate a personalized daily summary using REAL ticket data",
)
async def get_daily_summary(
    request: DailySummaryRequest,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> DailySummaryResponse:
    """Generate daily summary using ACTUAL ticket data.

    IMPORTANT: This endpoint now receives real ticket data from the frontend,
    fixing the previous issue where empty lists were passed.

    The frontend should:
    1. Query tickets by status (in_progress, blocked, etc.)
    2. Send them in the request body
    3. Receive a meaningful summary

    Args:
        request: Daily summary request with categorized tickets

    Returns:
        Daily summary with focus areas, blockers, and quick wins
    """
    try:
        logger.info("Generating daily summary with real ticket data")

        # Convert Pydantic models to dicts
        in_progress = [t.model_dump() for t in request.in_progress]
        blocked = [t.model_dump() for t in request.blocked]
        due_soon = [t.model_dump() for t in request.due_soon]
        recently_completed = [t.model_dump() for t in request.recently_completed]

        # Log what we received (for debugging)
        logger.debug(
            f"Received: {len(in_progress)} in_progress, "
            f"{len(blocked)} blocked, {len(due_soon)} due_soon, "
            f"{len(recently_completed)} recently_completed"
        )

        # Build context (optional board data)
        board_data = None
        if request.board_context:
            board_data = request.board_context.model_dump()

        # Get context from manager (adds time context, etc.)
        context = ctx_manager.get_daily_summary_context(
            in_progress=in_progress,
            blocked=blocked,
            due_soon=due_soon,
            recently_completed=recently_completed,
            board_data=board_data,
        )

        # Format tickets for DSPy module
        def format_ticket(t: dict) -> dict:
            """Format ticket for summary module."""
            return {
                "id": t.get("id", "")[:8],
                "title": t.get("title", "Untitled"),
                "priority": t.get("priority", "medium"),
                "due_date": t.get("due_date"),
            }

        formatted_in_progress = [format_ticket(t) for t in in_progress]
        formatted_blocked = [format_ticket(t) for t in blocked]
        formatted_due_soon = [format_ticket(t) for t in due_soon]
        formatted_completed = [format_ticket(t) for t in recently_completed]

        summary_module = DailySummaryModule()

        def run_summary():
            return summary_module(
                in_progress=formatted_in_progress,
                blocked=formatted_blocked,
                due_soon=formatted_due_soon,
                recently_completed=formatted_completed,
            )

        result = await run_sync_with_timeout(run_summary, DAILY_SUMMARY_TIMEOUT, "Daily summary")

        # Extract values
        greeting = extract_value(result.greeting)
        focus_today = extract_value(result.focus_today)
        blockers = extract_value(result.blockers)
        quick_wins = extract_value(result.quick_wins)

        return DailySummaryResponse(
            greeting=greeting,
            focus_today=focus_today[:3] if focus_today else [],
            blockers=blockers or [],
            quick_wins=quick_wins or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Daily summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Daily summary failed: {str(e)}")


# ============================================================================
# ANALYZE ENDPOINT (FIXED - now uses ChromaDB for similar tickets)
# ============================================================================


@router.post(
    "/agent/analyze",
    response_model=AnalyzeResponse,
    summary="Multi-hop ticket analysis with real context",
    description="Analyze a ticket using multi-hop reasoning with REAL similar tickets from ChromaDB",
)
async def analyze_ticket(
    request: AnalyzeRequestWithContext,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> AnalyzeResponse:
    """Analyze a ticket using multi-hop reasoning with REAL similar tickets.

    IMPORTANT: This endpoint now retrieves actual similar tickets from ChromaDB,
    fixing the previous hardcoded `similar_tickets="[]"` issue.

    The context manager:
    1. Searches ChromaDB for semantically similar tickets
    2. Retrieves their metadata (status, priority, labels)
    3. Provides rich context for multi-hop analysis
    """
    try:
        logger.info(f"Analyzing ticket: {request.title[:50]}...")

        ticket = {
            "title": request.title,
            "description": request.description,
        }

        board_data = None
        if request.board_context:
            board_data = request.board_context.model_dump()

        # Get context with REAL similar tickets from ChromaDB
        context = ctx_manager.get_analyze_context(ticket, board_data)

        # Get similar tickets as JSON for the multi-hop analyzer
        similar_tickets_json = context.get_similar_tickets_json()

        logger.debug(f"Found similar tickets: {similar_tickets_json[:200]}...")

        analyzer = MultiHopTicketAnalyzer()

        def run_analyze():
            return analyzer(
                ticket_title=request.title,
                ticket_description=request.description,
                similar_tickets=similar_tickets_json,  # NOW REAL DATA!
            )

        result = await run_sync_with_timeout(run_analyze, ANALYZE_TIMEOUT, "Analyze")

        return AnalyzeResponse(
            context_summary=extract_value(result.get("context_summary", "")),
            key_themes=extract_value(result.get("key_themes", [])),
            patterns=extract_value(result.get("patterns", [])),
            dependencies=extract_value(result.get("dependencies", "")),
            insights=extract_value(result.get("insights", "")),
            recommendations=extract_value(result.get("recommendations", "")),
            complexity=extract_value(result.get("complexity", "medium")),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analyze failed: {str(e)}")


# ============================================================================
# CHAT ENDPOINT (updated with context)
# ============================================================================


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with agent using rich context",
)
async def chat_with_agent(
    request: ChatRequest,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> ChatResponse:
    """Chat with the agent using rich, layered context.

    The context manager provides:
    1. Board-level context (columns, labels, conventions)
    2. Similar tickets based on the query
    3. Conversation history for continuity
    """
    try:
        logger.info(f"Chat message: {request.message[:50]}...")

        # Build context
        context = ctx_manager.get_chat_context(
            message=request.message,
            board_data=request.context,
            conversation_history=request.context.get("conversation_history") if request.context else None,
        )

        # Get enriched context dict
        enriched_context = context.get_board_context_dict()

        # Merge with provided context
        if request.context:
            enriched_context.update(request.context)

        action_decider = ActionDeciderModule()

        def run_chat():
            return action_decider(
                user_message=request.message,
                current_context=enriched_context,
            )

        result = await run_sync_with_timeout(run_chat, CHAT_TIMEOUT, "Chat")

        action = extract_value(result.action)
        raw_params = extract_value(result.params)
        response = extract_value(result.response)
        params = raw_params if isinstance(raw_params, dict) else {}

        return ChatResponse(
            action=action,
            params=params,
            response=response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS (new)
# ============================================================================


@router.post(
    "/context/invalidate-cache",
    summary="Invalidate context cache",
)
async def invalidate_cache(
    board_id: Optional[str] = Query(None, description="Board ID to invalidate"),
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> dict[str, Any]:
    """Invalidate context cache.

    Use this when:
    - Board structure changes (columns, labels)
    - Many tickets are updated at once
    - You need fresh context

    Args:
        board_id: Optional board ID to invalidate (all if not specified)

    Returns:
        Cache invalidation stats
    """
    if board_id:
        count = ctx_manager.invalidate_board_cache(board_id)
        return {"invalidated": count, "board_id": board_id}
    else:
        ctx_manager.clear_all_cache()
        return {"invalidated": "all"}


@router.get(
    "/context/cache-stats",
    summary="Get cache statistics",
)
async def get_cache_stats(
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> dict[str, Any]:
    """Get cache statistics."""
    return ctx_manager.get_cache_stats()


@router.get(
    "/context/sync-status",
    summary="Get ChromaDB sync status",
)
async def get_sync_status(
    ctx_manager: ContextManager = Depends(get_ctx_manager),
) -> dict[str, Any]:
    """Get ChromaDB sync status."""
    status = ctx_manager.get_sync_status()
    return {
        "is_synced": status.is_synced,
        "last_sync_at": status.last_sync_at,
        "tickets_in_chroma": status.tickets_in_chroma,
        "tickets_in_sqlite": status.tickets_in_sqlite,
    }
