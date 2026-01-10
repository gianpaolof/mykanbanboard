"""FastAPI routes for Kanban AI agent."""

from typing import Any
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
)
from ..db.chroma import ChromaManager
from .models import (
    TriageRequest,
    TriageResponse,
    DecomposeRequest,
    DecomposeResponse,
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    DailySummaryResponse,
    TicketSummary,
    ErrorResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================


def get_chroma_manager() -> ChromaManager:
    """Get ChromaDB manager instance."""
    return ChromaManager()


# ============================================================================
# HEALTH CHECK
# ============================================================================


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status message
    """
    return {"status": "healthy", "service": "kanban-agent"}


# ============================================================================
# TRIAGE ENDPOINT
# ============================================================================


@router.post(
    "/triage",
    response_model=TriageResponse,
    summary="Auto-triage a ticket",
    description="Automatically assign priority, labels, and effort estimate to a ticket",
)
async def triage_ticket(request: TriageRequest) -> TriageResponse:
    """Auto-triage a ticket.

    Args:
        request: Triage request with ticket details

    Returns:
        Triage response with metadata

    Raises:
        HTTPException: If triage fails
    """
    try:
        logger.info(f"Triaging ticket: {request.ticket_id}")

        triage_module = TriageModule()
        result = triage_module(
            title=request.title,
            description=request.description,
            existing_labels=request.existing_labels,
        )

        # Ensure labels is a list and limit to 3
        labels = result.labels if isinstance(result.labels, list) else [result.labels]
        labels = labels[:3]

        return TriageResponse(
            priority=result.priority,
            labels=labels,
            effort=result.effort_estimate,
            reasoning=result.reasoning,
        )

    except Exception as e:
        logger.error(f"Triage failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Triage failed: {str(e)}",
        )


# ============================================================================
# DECOMPOSE ENDPOINT
# ============================================================================


@router.post(
    "/decompose",
    response_model=DecomposeResponse,
    summary="Decompose a task",
    description="Break down a complex task into actionable subtasks",
)
async def decompose_task(request: DecomposeRequest) -> DecomposeResponse:
    """Decompose a task into subtasks.

    Args:
        request: Decomposition request

    Returns:
        Decomposition response with subtasks

    Raises:
        HTTPException: If decomposition fails
    """
    try:
        logger.info(f"Decomposing task: {request.ticket_id}")

        decompose_module = DecomposeModule()
        result = decompose_module(
            title=request.title,
            description=request.description,
            context=request.context or "",
        )

        # Parse subtasks
        subtasks = []
        for subtask in result.subtasks:
            if isinstance(subtask, dict):
                subtasks.append(subtask)
            else:
                # Handle string or other formats
                subtasks.append({
                    "title": str(subtask),
                    "description": "",
                    "effort": "m",
                })

        # Parse dependencies
        dependencies = []
        if result.dependencies:
            for dep in result.dependencies:
                if isinstance(dep, (list, tuple)) and len(dep) == 2:
                    dependencies.append((int(dep[0]), int(dep[1])))

        return DecomposeResponse(
            subtasks=subtasks,
            dependencies=dependencies,
            reasoning=result.reasoning,
        )

    except Exception as e:
        logger.error(f"Decomposition failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Decomposition failed: {str(e)}",
        )


# ============================================================================
# CHAT ENDPOINT
# ============================================================================


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with agent",
    description="Send a message to the agent and get an action decision",
)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    """Chat with the agent.

    Args:
        request: Chat request with message and context

    Returns:
        Chat response with action and natural language response

    Raises:
        HTTPException: If chat fails
    """
    try:
        logger.info(f"Chat message: {request.message[:50]}...")

        action_decider = ActionDeciderModule()
        result = action_decider(
            user_message=request.message,
            current_context=request.context,
        )

        # Parse params
        params = result.params if isinstance(result.params, dict) else {}

        return ChatResponse(
            action=result.action,
            params=params,
            response=result.response,
        )

    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}",
        )


# ============================================================================
# SEARCH ENDPOINT
# ============================================================================


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Search for tickets using semantic similarity",
)
async def search_tickets(
    request: SearchRequest,
    chroma: ChromaManager = Depends(get_chroma_manager),
) -> SearchResponse:
    """Search for tickets using semantic similarity.

    Args:
        request: Search request with query
        chroma: ChromaDB manager

    Returns:
        Search results

    Raises:
        HTTPException: If search fails
    """
    try:
        logger.info(f"Searching for: {request.query}")

        results = chroma.search(query=request.query, limit=request.limit)

        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=result["id"],
                    title=result.get("title", ""),
                    description=result.get("description", ""),
                    score=result.get("score", 0.0),
                    explanation=result.get("explanation"),
                )
            )

        return SearchResponse(
            results=search_results,
            query=request.query,
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


# ============================================================================
# DAILY SUMMARY ENDPOINT
# ============================================================================


@router.get(
    "/daily-summary",
    response_model=DailySummaryResponse,
    summary="Get daily summary",
    description="Generate a personalized daily work summary",
)
async def get_daily_summary() -> DailySummaryResponse:
    """Get daily summary.

    This is a placeholder that will be enhanced with actual ticket data
    from the frontend via the context parameter.

    Returns:
        Daily summary with focus areas

    Raises:
        HTTPException: If summary generation fails
    """
    try:
        logger.info("Generating daily summary")

        # Placeholder data - will be replaced with real ticket data
        summary_module = DailySummaryModule()
        result = summary_module(
            in_progress=[],
            blocked=[],
            due_soon=[],
            recently_completed=[],
        )

        return DailySummaryResponse(
            greeting=result.greeting,
            focus_today=result.focus_today[:3],
            blockers=result.blockers,
            quick_wins=result.quick_wins,
        )

    except Exception as e:
        logger.error(f"Daily summary failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Daily summary failed: {str(e)}",
        )


# ============================================================================
# ERROR HANDLER
# ============================================================================


@router.exception_handler(Exception)
async def generic_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Handle generic exceptions.

    Args:
        request: Request object
        exc: Exception

    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message=str(exc),
            details={},
        ).model_dump(),
    )
