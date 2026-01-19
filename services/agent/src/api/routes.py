"""FastAPI routes for Kanban AI agent.

Integrates the Context Management System for:
- Rich, layered context (Global, Relevant, Operation)
- ChromaDB semantic search for similar tickets
- Token budget management
- Caching for expensive operations
"""

from typing import Any, Optional
import logging
import asyncio
from functools import wraps
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
    RuleParserModule,
)
from ..agent.judge import TicketQualityJudge
from ..agent.multihop import MultiHopTicketAnalyzer
from ..agent.analytics import analytics
from ..agent.suggester import suggester
from ..db.chroma import ChromaManager
from ..context import ContextManager, get_context_manager
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
    JudgeRequest,
    JudgeResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    ErrorResponse,
    SuggestionsRequest,
    SuggestionsResponse,
    Suggestion,
)


# ============================================================================
# EXTENDED REQUEST MODELS (with context support)
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


def get_ctx_manager(
    chroma: ChromaManager = Depends(get_chroma_manager),
) -> ContextManager:
    """Get ContextManager instance with ChromaDB."""
    return get_context_manager(chroma)


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
# DAILY SUMMARY ENDPOINT (FIXED - now receives actual ticket data)
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

    Raises:
        HTTPException: If summary generation fails
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


# ============================================================================
# JUDGE ENDPOINT
# ============================================================================

JUDGE_TIMEOUT = 15


@router.post(
    "/agent/judge",
    response_model=JudgeResponse,
    summary="Judge ticket quality",
    description="Evaluate ticket quality using LLM-as-Judge pattern",
)
async def judge_ticket(request: JudgeRequest) -> JudgeResponse:
    """Judge the quality of a ticket.

    Args:
        request: Judge request with ticket details

    Returns:
        Quality scores and feedback

    Raises:
        HTTPException: If judging fails
    """
    try:
        logger.info(f"Judging ticket: {request.title[:50]}...")

        judge = TicketQualityJudge()

        # Run DSPy module with timeout
        def run_judge():
            return judge(
                ticket_title=request.title,
                ticket_description=request.description,
                priority=request.priority,
                effort=request.effort,
                labels=",".join(request.labels)
            )

        result = await run_sync_with_timeout(run_judge, JUDGE_TIMEOUT, "Judge")

        # Extract values
        clarity = int(extract_value(result.clarity_score))
        completeness = int(extract_value(result.completeness_score))
        actionability = int(extract_value(result.actionability_score))
        feedback = extract_value(result.feedback)

        return JudgeResponse(
            clarity_score=clarity,
            completeness_score=completeness,
            actionability_score=actionability,
            feedback=feedback,
            overall_score=(clarity + completeness + actionability) / 3
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Judge failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Judge failed: {str(e)}",
        )


# ============================================================================
# ANALYZE ENDPOINT (FIXED - now uses ChromaDB for similar tickets)
# ============================================================================

ANALYZE_TIMEOUT = 60


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

    Args:
        request: Analyze request with ticket details

    Returns:
        Analysis with context, patterns, insights, recommendations

    Raises:
        HTTPException: If analysis fails
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

        # Run multi-hop analysis with extended timeout
        def run_analyze():
            return analyzer(
                ticket_title=request.title,
                ticket_description=request.description,
                similar_tickets=similar_tickets_json,  # NOW REAL DATA from ChromaDB!
            )

        result = await run_sync_with_timeout(run_analyze, ANALYZE_TIMEOUT, "Analyze")

        # Extract values
        return AnalyzeResponse(
            context_summary=extract_value(result.get("context_summary", "")),
            key_themes=extract_value(result.get("key_themes", [])),
            patterns=extract_value(result.get("patterns", [])),
            dependencies=extract_value(result.get("dependencies", "")),
            insights=extract_value(result.get("insights", "")),
            recommendations=extract_value(result.get("recommendations", "")),
            complexity=extract_value(result.get("complexity", "medium"))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analyze failed: {str(e)}",
        )


# ============================================================================
# STATS ENDPOINT
# ============================================================================


@router.get(
    "/agent/stats",
    summary="Get agent statistics",
    description="Get aggregated statistics for agent calls",
)
async def get_agent_stats(
    period: str = Query("day", pattern="^(hour|day|week)$")
) -> dict:
    """Get agent statistics for a time period.

    Args:
        period: Time period - "hour", "day", or "week"

    Returns:
        Statistics including total_calls, avg_latency_ms, success_rate, total_tokens
    """
    try:
        stats = analytics.get_stats(period=period)
        return {
            **stats,
            "period": period,
        }
    except Exception as e:
        logger.error(f"Stats failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Stats failed: {str(e)}",
        )


@router.get(
    "/agent/stats/modules",
    summary="Get per-module statistics",
    description="Get statistics broken down by module",
)
async def get_module_stats(
    period: str = Query("day", pattern="^(hour|day|week)$")
) -> dict:
    """Get statistics broken down by module.

    Args:
        period: Time period - "hour", "day", or "week"

    Returns:
        Per-module statistics
    """
    try:
        modules = analytics.get_module_breakdown(period=period)
        return {
            "modules": modules,
            "period": period,
        }
    except Exception as e:
        logger.error(f"Module stats failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Module stats failed: {str(e)}",
        )


@router.get(
    "/agent/stats/hourly",
    summary="Get hourly breakdown",
    description="Get statistics broken down by hour",
)
async def get_hourly_stats(
    hours: int = Query(24, ge=1, le=168)
) -> dict:
    """Get hourly statistics breakdown.

    Args:
        hours: Number of hours to look back (max 168 = 1 week)

    Returns:
        Hourly statistics
    """
    try:
        hourly = analytics.get_hourly_breakdown(hours=hours)
        return {
            "hourly": hourly,
            "hours_requested": hours,
        }
    except Exception as e:
        logger.error(f"Hourly stats failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Hourly stats failed: {str(e)}",
        )


@router.get(
    "/agent/stats/errors",
    summary="Get recent errors",
    description="Get recent failed agent calls",
)
async def get_recent_errors(
    limit: int = Query(10, ge=1, le=100)
) -> dict:
    """Get recent failed calls.

    Args:
        limit: Maximum number of errors to return

    Returns:
        Recent error details
    """
    try:
        errors = analytics.get_recent_errors(limit=limit)
        return {
            "errors": errors,
            "count": len(errors),
        }
    except Exception as e:
        logger.error(f"Error stats failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error stats failed: {str(e)}",
        )


# ============================================================================
# SUGGESTIONS ENDPOINT
# ============================================================================


@router.post(
    "/agent/suggestions",
    response_model=SuggestionsResponse,
    summary="Get proactive suggestions",
    description="Get proactive suggestions for improving the board",
)
async def get_suggestions(
    request: SuggestionsRequest,
    deep: bool = Query(False, description="Use LLM for deeper analysis"),
) -> SuggestionsResponse:
    """Get proactive suggestions for the board.

    Args:
        request: Board state with columns and tickets
        deep: If True, use LLM for deeper analysis (slower)

    Returns:
        List of prioritized suggestions
    """
    try:
        # Convert Pydantic models to dicts
        columns = [col.model_dump() for col in request.columns]
        tickets = [ticket.model_dump() for ticket in request.tickets]

        if deep:
            # Use LLM-based analysis (slower but more insightful)
            raw_suggestions = suggester.get_suggestions(
                columns=columns,
                tickets=tickets,
            )
        else:
            # Use rule-based quick analysis
            raw_suggestions = suggester.quick_analysis(
                tickets=tickets,
                columns=columns,
            )

        # Convert to response model
        suggestions = [
            Suggestion(
                type=s.get("type", "stale_ticket"),
                message=s.get("message", ""),
                action=s.get("action", ""),
                priority=s.get("priority", "medium"),
                ticket_id=s.get("ticket_id"),
                column_id=s.get("column_id"),
            )
            for s in raw_suggestions
        ]

        return SuggestionsResponse(suggestions=suggestions)

    except Exception as e:
        logger.error(f"Suggestions failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Suggestions failed: {str(e)}",
        )


# ============================================================================
# SYNC ENDPOINT (for ChromaDB sync)
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
# CACHE MANAGEMENT ENDPOINTS
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
