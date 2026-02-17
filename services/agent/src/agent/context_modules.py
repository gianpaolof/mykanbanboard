"""Context-Aware DSPy modules for Kanban AI.

These modules integrate with the Context Management System to provide
richer, more accurate AI responses by leveraging:
- Project context (tech stack, conventions)
- Similar tickets from ChromaDB
- Board-level context (labels, columns, workflow)
- Token budget management

Usage:
    from context_modules import ContextAwareTriageModule
    from context import ContextManager

    ctx_manager = ContextManager(chroma)
    triage = ContextAwareTriageModule(ctx_manager)

    result = triage(
        ticket_id="abc123",
        title="Fix login bug",
        description="Users can't log in...",
        project_context={"tech_stack": ["React", "FastAPI"]},
    )
"""

from typing import Literal, Optional, Any
import dspy
import json

from .modules import (
    VALID_PRIORITIES,
    VALID_EFFORTS,
    VALID_ACTIONS,
)

# ============================================================================
# COMPATIBILITY SHIM FOR DSPY.ASSERT (removed in DSPy 3.x)
# ============================================================================

def _dspy_assert(condition: bool, message: str) -> None:
    """Compatibility shim for dspy.Assert."""
    if not condition:
        raise AssertionError(message)

if not hasattr(dspy, 'Assert'):
    dspy.Assert = _dspy_assert

# ============================================================================
# CONTEXT-AWARE TRIAGE SIGNATURE
# ============================================================================


class ContextAwareTriageSignature(dspy.Signature):
    """Triage a ticket with full project and semantic context.

    You have access to:
    - Project context: tech stack, conventions, priority rules
    - Similar tickets: how similar issues were triaged before
    - Existing labels: use these for consistency

    Priority criteria:
    - critical: Blocks production/users, security issues, data loss
    - high: Important feature, significant impact, needed soon
    - medium: Standard work, can be planned normally
    - low: Nice-to-have, improvements, can wait

    Effort criteria (for a single developer):
    - xs: < 1 hour, quick fix or config change
    - s: 1-4 hours, half day task
    - m: 1-2 days, standard feature
    - l: 3-5 days, complex feature
    - xl: > 1 week, epic or major refactor
    """

    # Primary inputs
    title: str = dspy.InputField(desc="Ticket title")
    description: str = dspy.InputField(desc="Ticket description")

    # Context inputs
    project_context: str = dspy.InputField(
        desc="Project tech stack, conventions, and priority rules"
    )
    similar_tickets: str = dspy.InputField(
        desc="JSON array of similar tickets with their priority/labels/effort"
    )
    existing_labels: list[str] = dspy.InputField(
        desc="Labels already used in the board for consistency"
    )

    # Outputs
    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField(
        desc="Priority based on project rules and similar ticket patterns"
    )
    labels: list[str] = dspy.OutputField(
        desc="1-3 relevant labels, prefer existing ones, match project conventions"
    )
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField(
        desc="Effort estimate based on similar ticket patterns"
    )
    reasoning: str = dspy.OutputField(
        desc="Explain how context influenced the decision"
    )


class ContextAwareTriageModule(dspy.Module):
    """Context-aware triage module that uses the full context system.

    This module:
    1. Accepts project context (tech stack, conventions)
    2. Uses similar tickets from ChromaDB for consistency
    3. Applies project-specific priority rules
    4. Maintains label consistency with existing labels
    """

    def __init__(self, context_manager: Optional[Any] = None):
        """Initialize the context-aware triage module.

        Args:
            context_manager: ContextManager instance for context retrieval
        """
        super().__init__()
        self.ctx_mgr = context_manager
        self.triage = dspy.ChainOfThought(ContextAwareTriageSignature)

    def forward(
        self,
        ticket_id: str,
        title: str,
        description: str,
        project_context: Optional[dict[str, Any]] = None,
        existing_labels: Optional[list[str]] = None,
    ):
        """Triage a ticket with full context awareness.

        Args:
            ticket_id: Unique ticket identifier
            title: Ticket title
            description: Ticket description
            project_context: Optional project context dict
            existing_labels: Optional list of existing labels

        Returns:
            Triage result with priority, labels, effort, and reasoning
        """
        # Build context using the context manager if available
        similar_tickets_json = "[]"
        all_labels = existing_labels or []

        if self.ctx_mgr:
            ticket = {
                "id": ticket_id,
                "title": title,
                "description": description,
            }
            board_data = {"labels": all_labels}

            context = self.ctx_mgr.get_triage_context(ticket, board_data)
            similar_tickets_json = context.get_similar_tickets_json()

            # Merge labels from context
            context_labels = context.get_existing_labels()
            if context_labels:
                all_labels = list(set(all_labels + context_labels))

        # Format project context as string
        project_context_str = ""
        if project_context:
            parts = []
            if project_context.get("tech_stack"):
                parts.append(f"Tech stack: {', '.join(project_context['tech_stack'])}")
            if project_context.get("conventions"):
                parts.append(f"Conventions: {project_context['conventions']}")
            if project_context.get("priority_rules"):
                parts.append(f"Priority rules: {json.dumps(project_context['priority_rules'])}")
            project_context_str = "\n".join(parts)
        else:
            project_context_str = "No specific project context provided."

        # Run triage with context
        result = self.triage(
            title=title,
            description=description,
            project_context=project_context_str,
            similar_tickets=similar_tickets_json,
            existing_labels=all_labels,
        )

        # Normalize labels to list if needed
        if not isinstance(result.labels, list):
            if isinstance(result.labels, str):
                result.labels = [label.strip() for label in result.labels.split(',') if label.strip()]
            elif result.labels is None:
                result.labels = []
            else:
                result.labels = [str(result.labels)]

        # Validate outputs
        dspy.Assert(
            result.priority in VALID_PRIORITIES,
            f"Priority '{result.priority}' is invalid. Must be one of: {VALID_PRIORITIES}",
        )
        dspy.Assert(
            result.effort_estimate in VALID_EFFORTS,
            f"Effort '{result.effort_estimate}' is invalid. Must be one of: {VALID_EFFORTS}",
        )

        # Soft constraints
        dspy.Suggest(
            len(result.labels) <= 3,
            f"Too many labels ({len(result.labels)}). Prefer max 3 labels.",
        )
        dspy.Suggest(
            len(result.reasoning) >= 30,
            "Reasoning should explain how context influenced the decision.",
        )

        return result


# ============================================================================
# CONTEXT-AWARE DECOMPOSE SIGNATURE
# ============================================================================


class ContextAwareDecomposeSignature(dspy.Signature):
    """Decompose a task with project and workflow context.

    You have access to:
    - Project context: tech stack, architecture patterns
    - Similar tasks: how similar work was decomposed
    - Board workflow: columns representing work stages

    Create subtasks that:
    - Are completable in a single work session
    - Have clear done criteria
    - Follow the project's tech stack and patterns
    - Can be assigned to the appropriate workflow stage
    """

    # Primary inputs
    title: str = dspy.InputField(desc="Task title to decompose")
    description: str = dspy.InputField(desc="Detailed task description")

    # Context inputs
    project_context: str = dspy.InputField(
        desc="Project tech stack and architecture patterns"
    )
    similar_tasks: str = dspy.InputField(
        desc="JSON array of similar tasks and their decomposition patterns"
    )
    workflow_stages: str = dspy.InputField(
        desc="Board workflow stages (columns) for context"
    )

    # Outputs
    subtasks: list[dict] = dspy.OutputField(
        desc="List of subtasks with {title, description, effort, suggested_stage}"
    )
    dependencies: list[tuple[int, int]] = dspy.OutputField(
        desc="Dependencies between subtasks as (index, depends_on_index) pairs"
    )
    reasoning: str = dspy.OutputField(
        desc="Explain the decomposition strategy based on context"
    )


class ContextAwareDecomposeModule(dspy.Module):
    """Context-aware decomposition module.

    This module:
    1. Uses project tech stack to suggest appropriate subtasks
    2. Learns from similar task decomposition patterns
    3. Suggests workflow stages for each subtask
    4. Creates dependencies based on project patterns
    """

    def __init__(self, context_manager: Optional[Any] = None):
        """Initialize the context-aware decompose module.

        Args:
            context_manager: ContextManager instance
        """
        super().__init__()
        self.ctx_mgr = context_manager
        self.decompose = dspy.ChainOfThought(ContextAwareDecomposeSignature)

    def forward(
        self,
        ticket_id: str,
        title: str,
        description: str,
        project_context: Optional[dict[str, Any]] = None,
        board_data: Optional[dict[str, Any]] = None,
    ):
        """Decompose a task with context awareness.

        Args:
            ticket_id: Ticket identifier
            title: Task title
            description: Task description
            project_context: Project context dict
            board_data: Board data with columns, labels

        Returns:
            Decomposition with subtasks, dependencies, and reasoning
        """
        # Get context
        similar_tasks_json = "[]"
        workflow_stages = "To Do -> In Progress -> Done"

        if self.ctx_mgr:
            ticket = {
                "id": ticket_id,
                "title": title,
                "description": description,
            }
            context = self.ctx_mgr.get_decompose_context(ticket, board_data)
            similar_tasks_json = context.get_similar_tickets_json()

            # Get workflow from global context
            if context.global_context and context.global_context.columns:
                columns = [c.get("name", "") for c in context.global_context.columns]
                workflow_stages = " -> ".join(columns)

        # Format project context
        project_context_str = ""
        if project_context:
            parts = []
            if project_context.get("tech_stack"):
                parts.append(f"Tech stack: {', '.join(project_context['tech_stack'])}")
            if project_context.get("architecture"):
                parts.append(f"Architecture: {project_context['architecture']}")
            project_context_str = "\n".join(parts)
        else:
            project_context_str = "No specific project context provided."

        # Run decomposition
        result = self.decompose(
            title=title,
            description=description,
            project_context=project_context_str,
            similar_tasks=similar_tasks_json,
            workflow_stages=workflow_stages,
        )

        # Validate
        dspy.Assert(
            isinstance(result.subtasks, list),
            "Subtasks must be a list",
        )
        dspy.Assert(
            len(result.subtasks) >= 2,
            f"Must generate at least 2 subtasks, got {len(result.subtasks)}",
        )
        dspy.Assert(
            len(result.subtasks) <= 10,
            f"Too many subtasks ({len(result.subtasks)}). Maximum is 10.",
        )

        # Validate each subtask
        for i, subtask in enumerate(result.subtasks):
            dspy.Assert(
                isinstance(subtask, dict) and "title" in subtask,
                f"Subtask {i} must be a dict with at least a 'title' key",
            )
            if "effort" in subtask:
                dspy.Assert(
                    subtask["effort"] in VALID_EFFORTS,
                    f"Subtask {i} effort '{subtask.get('effort')}' is invalid",
                )

        dspy.Assert(
            isinstance(result.dependencies, list),
            "Dependencies must be a list of tuples",
        )

        # Soft constraints
        dspy.Suggest(
            3 <= len(result.subtasks) <= 7,
            f"Optimal subtask count is 3-7, got {len(result.subtasks)}",
        )

        return result


# ============================================================================
# DYNAMIC MULTI-HOP ANALYZER
# ============================================================================


class InitialAnalysisSignature(dspy.Signature):
    """First hop: gather initial context and identify key themes."""

    ticket_title: str = dspy.InputField(desc="Ticket title")
    ticket_description: str = dspy.InputField(desc="Ticket description")
    similar_tickets: str = dspy.InputField(desc="JSON of similar tickets")

    context_summary: str = dspy.OutputField(
        desc="Summary of the ticket in context of similar work"
    )
    key_themes: list[str] = dspy.OutputField(
        desc="Key themes/concepts in this ticket"
    )
    follow_up_queries: list[str] = dspy.OutputField(
        desc="Queries to search for more specific context"
    )


class DeepAnalysisSignature(dspy.Signature):
    """Second hop: deep analysis with retrieved context."""

    ticket_title: str = dspy.InputField(desc="Ticket title")
    ticket_description: str = dspy.InputField(desc="Ticket description")
    initial_analysis: str = dspy.InputField(desc="Summary from first hop")
    additional_context: str = dspy.InputField(desc="Additional retrieved context")

    dependencies: str = dspy.OutputField(
        desc="Identified dependencies on other work"
    )
    complexity: Literal["low", "medium", "high", "critical"] = dspy.OutputField(
        desc="Complexity assessment"
    )
    risks: list[str] = dspy.OutputField(
        desc="Potential risks or blockers"
    )


class ActionableInsightsSignature(dspy.Signature):
    """Third hop: actionable insights and recommendations."""

    ticket_title: str = dspy.InputField(desc="Ticket title")
    context_summary: str = dspy.InputField(desc="Context from previous hops")
    dependencies: str = dspy.InputField(desc="Identified dependencies")
    complexity: str = dspy.InputField(desc="Complexity level")
    risks: list[str] = dspy.InputField(desc="Identified risks")

    priority_recommendation: Literal["low", "medium", "high", "critical"] = dspy.OutputField(
        desc="Recommended priority based on analysis"
    )
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField(
        desc="Effort estimate based on complexity"
    )
    recommendations: list[str] = dspy.OutputField(
        desc="Actionable recommendations for this ticket"
    )
    insights: str = dspy.OutputField(
        desc="Key insights from the analysis"
    )


class DynamicMultiHopAnalyzer(dspy.Module):
    """Multi-hop analyzer with dynamic retrieval at each hop.

    Unlike the static multi-hop analyzer, this module:
    1. HOP 1: Initial analysis + generates follow-up queries
    2. RETRIEVAL: Executes follow-up queries against ChromaDB
    3. HOP 2: Deep analysis with additional context
    4. HOP 3: Actionable insights and recommendations

    This allows the AI to "think" about what additional context it needs
    and retrieve it dynamically.
    """

    def __init__(self, context_manager: Optional[Any] = None):
        """Initialize the multi-hop analyzer.

        Args:
            context_manager: ContextManager for dynamic retrieval
        """
        super().__init__()
        self.ctx_mgr = context_manager
        self.initial_analysis = dspy.ChainOfThought(InitialAnalysisSignature)
        self.deep_analysis = dspy.ChainOfThought(DeepAnalysisSignature)
        self.insights = dspy.ChainOfThought(ActionableInsightsSignature)

    def _retrieve_additional_context(self, queries: list[str]) -> str:
        """Execute follow-up queries to retrieve additional context.

        Args:
            queries: List of search queries

        Returns:
            Combined context from all queries
        """
        if not self.ctx_mgr or not self.ctx_mgr.chroma:
            return "No additional context available."

        results = []
        for query in queries[:3]:  # Limit to 3 queries
            try:
                search_results = self.ctx_mgr.chroma.search(query, limit=3)
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "score": result.get("score", 0),
                        "query": query,
                    })
            except Exception:
                continue

        if not results:
            return "No additional context found."

        # Format results
        formatted = ["Additional context from follow-up queries:"]
        for r in results[:5]:  # Top 5 results
            formatted.append(f"- [{r['query']}] {r['title']} (score: {r['score']:.2f})")

        return "\n".join(formatted)

    def forward(
        self,
        ticket_title: str,
        ticket_description: str,
        similar_tickets: str = "[]",
        project_context: Optional[dict[str, Any]] = None,
    ):
        """Analyze a ticket using multi-hop reasoning with dynamic retrieval.

        Args:
            ticket_title: Ticket title
            ticket_description: Ticket description
            similar_tickets: JSON string of similar tickets
            project_context: Optional project context

        Returns:
            Full analysis with context, dependencies, insights, recommendations
        """
        # HOP 1: Initial analysis
        hop1 = self.initial_analysis(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            similar_tickets=similar_tickets,
        )

        # DYNAMIC RETRIEVAL: Execute follow-up queries
        follow_up_queries = hop1.follow_up_queries if isinstance(hop1.follow_up_queries, list) else []
        additional_context = self._retrieve_additional_context(follow_up_queries)

        # HOP 2: Deep analysis with additional context
        hop2 = self.deep_analysis(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            initial_analysis=hop1.context_summary,
            additional_context=additional_context,
        )

        # HOP 3: Actionable insights
        hop3 = self.insights(
            ticket_title=ticket_title,
            context_summary=hop1.context_summary,
            dependencies=hop2.dependencies,
            complexity=hop2.complexity,
            risks=hop2.risks if isinstance(hop2.risks, list) else [],
        )

        # Validate outputs
        dspy.Assert(
            hop3.priority_recommendation in VALID_PRIORITIES,
            f"Invalid priority: {hop3.priority_recommendation}",
        )
        dspy.Assert(
            hop3.effort_estimate in VALID_EFFORTS,
            f"Invalid effort: {hop3.effort_estimate}",
        )

        return {
            "context_summary": hop1.context_summary,
            "key_themes": hop1.key_themes if isinstance(hop1.key_themes, list) else [],
            "patterns": [],  # From hop1 analysis
            "dependencies": hop2.dependencies,
            "complexity": hop2.complexity,
            "risks": hop2.risks if isinstance(hop2.risks, list) else [],
            "insights": hop3.insights,
            "recommendations": hop3.recommendations if isinstance(hop3.recommendations, list) else [],
            "priority_recommendation": hop3.priority_recommendation,
            "effort_estimate": hop3.effort_estimate,
            "hops_completed": 3,
            "follow_up_queries_used": len(follow_up_queries),
        }
