"""FastAPI routes for Kanban AI agent."""

from typing import Any
import logging
import asyncio
from functools import wraps
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
    RuleParserModule,
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
    ParseRuleRequest,
    ParseRuleResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# Timeout constants (in seconds)
TRIAGE_TIMEOUT = 12
DECOMPOSE_TIMEOUT = 12
CHAT_TIMEOUT = 12
DAILY_SUMMARY_TIMEOUT = 10


async def run_with_timeout(coro, timeout_seconds: int, operation_name: str):
    """Run a coroutine with a timeout.

    Args:
        coro: The coroutine to run
        timeout_seconds: Maximum time to wait
        operation_name: Name of the operation for error messages

    Returns:
        The result of the coroutine

    Raises:
        HTTPException: If the operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.error(f"{operation_name} timed out after {timeout_seconds}s")
        raise HTTPException(
            status_code=504,
            detail=f"{operation_name} timed out after {timeout_seconds} seconds. Please try again.",
        )


def run_sync_with_timeout(func, timeout_seconds: int, operation_name: str):
    """Run a synchronous function in a thread pool with timeout.

    Args:
        func: The function to call (will be wrapped in to_thread)
        timeout_seconds: Maximum time to wait
        operation_name: Name of the operation for error messages

    Returns:
        The result of the function

    Raises:
        HTTPException: If the operation times out
    """
    async def wrapper():
        return await asyncio.to_thread(func)

    return run_with_timeout(wrapper(), timeout_seconds, operation_name)


def extract_value(obj: Any) -> Any:
    """Extract value from DSPy prediction object.

    DSPy returns Prediction objects where attributes might be
    bound methods or actual values. This helper extracts the actual value.
    """
    if obj is None:
        return None
    # If it's a bound method, it's wrong - return as string
    if callable(obj):
        return str(obj)
    # If it's a list, extract each item
    if isinstance(obj, list):
        return [extract_value(item) for item in obj]
    # If it's a dict, extract each value
    if isinstance(obj, dict):
        return {k: extract_value(v) for k, v in obj.items()}
    return obj


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

        # Run DSPy module with timeout
        def run_triage():
            return triage_module(
                title=request.title,
                description=request.description,
                existing_labels=request.existing_labels,
            )

        result = await run_sync_with_timeout(run_triage, TRIAGE_TIMEOUT, "Triage")

        # Extract values from DSPy prediction object and ensure labels is a list
        priority = extract_value(result.priority)
        labels_raw = extract_value(result.labels)
        labels = labels_raw if isinstance(labels_raw, list) else [labels_raw]
        labels = [str(l) for l in labels[:3]]  # Ensure strings and limit to 3
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

        # Run DSPy module with timeout
        def run_decompose():
            return decompose_module(
                title=request.title,
                description=request.description,
                context=request.context or "",
            )

        result = await run_sync_with_timeout(run_decompose, DECOMPOSE_TIMEOUT, "Decompose")

        # Extract values from DSPy prediction
        raw_subtasks = extract_value(result.subtasks)
        raw_dependencies = extract_value(result.dependencies)
        reasoning = extract_value(result.reasoning)

        # Map effort values from various formats to valid xs/s/m/l/xl
        def normalize_effort(effort: Any) -> str:
            effort_map = {
                "xs": "xs", "extra-small": "xs", "1": "xs", 1: "xs",
                "s": "s", "small": "s", "2": "s", 2: "s",
                "m": "m", "medium": "m", "3": "m", 3: "m",
                "l": "l", "large": "l", "4": "l", 4: "l",
                "xl": "xl", "extra-large": "xl", "5": "xl", 5: "xl",
            }
            return effort_map.get(effort, effort_map.get(str(effort).lower(), "m"))

        # Parse subtasks
        subtasks = []
        if raw_subtasks:
            for subtask in raw_subtasks:
                if isinstance(subtask, dict):
                    # Normalize effort field
                    normalized = {**subtask}
                    if "effort" in normalized:
                        normalized["effort"] = normalize_effort(normalized["effort"])
                    else:
                        normalized["effort"] = "m"
                    subtasks.append(normalized)
                else:
                    # Handle string or other formats
                    subtasks.append({
                        "title": str(subtask),
                        "description": "",
                        "effort": "m",
                    })

        # Parse dependencies
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

        # Run DSPy module with timeout
        def run_chat():
            return action_decider(
                user_message=request.message,
                current_context=request.context or {},
            )

        result = await run_sync_with_timeout(run_chat, CHAT_TIMEOUT, "Chat")

        # Extract values from DSPy prediction
        action = extract_value(result.action)
        raw_params = extract_value(result.params)
        response = extract_value(result.response)

        # Parse params
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

        # Run DSPy module with timeout
        def run_summary():
            return summary_module(
                in_progress=[],
                blocked=[],
                due_soon=[],
                recently_completed=[],
            )

        result = await run_sync_with_timeout(run_summary, DAILY_SUMMARY_TIMEOUT, "Daily summary")

        # Extract values from DSPy prediction
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
        raise HTTPException(
            status_code=500,
            detail=f"Daily summary failed: {str(e)}",
        )


# ============================================================================
# PARSE AUTOMATION RULE ENDPOINT
# ============================================================================

PARSE_RULE_TIMEOUT = 15


@router.post(
    "/parse-rule",
    response_model=ParseRuleResponse,
    summary="Parse automation rule",
    description="Parse a natural language automation rule into structured trigger/action configuration",
)
async def parse_automation_rule(request: ParseRuleRequest) -> ParseRuleResponse:
    """Parse a natural language automation rule.

    Args:
        request: Parse rule request with natural language and optional context

    Returns:
        Parsed rule with trigger type, trigger config, action type, action config

    Raises:
        HTTPException: If parsing fails
    """
    try:
        logger.info(f"Parsing rule: {request.natural_language[:50]}...")

        rule_parser = RuleParserModule()

        # Run DSPy module with timeout
        def run_parse():
            return rule_parser(
                natural_language=request.natural_language,
                board_context=request.board_context or {},
            )

        result = await run_sync_with_timeout(run_parse, PARSE_RULE_TIMEOUT, "Parse rule")

        # Extract values from DSPy prediction
        rule_name = extract_value(result.rule_name)
        trigger_type = extract_value(result.trigger_type)
        trigger_config = extract_value(result.trigger_config)
        action_type = extract_value(result.action_type)
        action_config = extract_value(result.action_config)
        confidence = extract_value(result.confidence)
        explanation = extract_value(result.explanation)

        # Ensure configs are dicts
        if not isinstance(trigger_config, dict):
            trigger_config = {}
        if not isinstance(action_config, dict):
            action_config = {}

        # Ensure confidence is a float
        try:
            confidence = float(confidence) if confidence else 0.5
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5

        return ParseRuleResponse(
            rule_name=str(rule_name)[:50] if rule_name else "Unnamed Rule",
            trigger_type=trigger_type,
            trigger_config=trigger_config,
            action_type=action_type,
            action_config=action_config,
            confidence=confidence,
            explanation=str(explanation) if explanation else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse rule failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Parse rule failed: {str(e)}",
        )
