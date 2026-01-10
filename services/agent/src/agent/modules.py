"""DSPy modules for Kanban AI agent capabilities."""

from typing import Literal
import dspy


# ============================================================================
# TRIAGE MODULE
# ============================================================================


class TriageTicket(dspy.Signature):
    """Analyze a ticket and assign appropriate metadata.

    Priority criteria:
    - critical: Blocks production/users, requires immediate fix
    - high: Important, significant impact, within 1-2 days
    - medium: Standard, can be planned normally
    - low: Nice-to-have, can wait

    Effort criteria:
    - xs: < 1 hour, quick fix
    - s: 1-4 hours, half day
    - m: 1-2 days, standard task
    - l: 3-5 days, complex feature
    - xl: > 1 week, epic
    """

    title: str = dspy.InputField(desc="Ticket title")
    description: str = dspy.InputField(desc="Ticket description")
    existing_labels: list[str] = dspy.InputField(
        desc="Labels already used in the board for consistency"
    )

    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField(
        desc="Priority level based on urgency and impact"
    )
    labels: list[str] = dspy.OutputField(
        desc="List of max 3 relevant labels, prefer existing ones"
    )
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField(
        desc="Estimated effort to complete"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of the choices made"
    )


class TriageModule(dspy.Module):
    """Module for automatic ticket categorization and triage."""

    def __init__(self):
        super().__init__()
        self.triage = dspy.ChainOfThought(TriageTicket)

    def forward(self, title: str, description: str, existing_labels: list[str]):
        """Triage a ticket and return metadata.

        Args:
            title: Ticket title
            description: Ticket description
            existing_labels: Labels already in use

        Returns:
            Triage result with priority, labels, effort, and reasoning
        """
        result = self.triage(
            title=title,
            description=description,
            existing_labels=existing_labels,
        )
        return result


# ============================================================================
# DECOMPOSE MODULE
# ============================================================================


class DecomposeTask(dspy.Signature):
    """Decompose a task into atomic, actionable subtasks.

    Each subtask should be:
    - Completable in a single work session
    - Verifiable (clear done criteria)
    - As independent as possible

    Output 3-7 subtasks for typical tasks.
    """

    title: str = dspy.InputField(desc="Task title")
    description: str = dspy.InputField(desc="Detailed task description")
    context: str = dspy.InputField(
        desc="Board context (other tickets, labels, etc.)"
    )

    subtasks: list[dict] = dspy.OutputField(
        desc="List of subtasks with {title, description, effort}"
    )
    dependencies: list[tuple[int, int]] = dspy.OutputField(
        desc="List of dependency pairs (subtask_index, depends_on_index)"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of the decomposition strategy"
    )


class DecomposeModule(dspy.Module):
    """Module for breaking down complex tasks into subtasks."""

    def __init__(self):
        super().__init__()
        self.decompose = dspy.ChainOfThought(DecomposeTask)

    def forward(self, title: str, description: str, context: str = ""):
        """Decompose a task into subtasks.

        Args:
            title: Task title
            description: Task description
            context: Additional context from the board

        Returns:
            Decomposition with subtasks, dependencies, and reasoning
        """
        result = self.decompose(
            title=title,
            description=description,
            context=context or "No additional context",
        )
        return result


# ============================================================================
# DAILY SUMMARY MODULE
# ============================================================================


class DailySummary(dspy.Signature):
    """Generate a personalized daily summary with priorities.

    Analyze current work state and provide actionable insights:
    - What to focus on today
    - Blockers to address
    - Quick wins to capture
    """

    in_progress: list[dict] = dspy.InputField(
        desc="Tickets currently in progress"
    )
    blocked: list[dict] = dspy.InputField(
        desc="Tickets that are blocked"
    )
    due_soon: list[dict] = dspy.InputField(
        desc="Tickets with approaching deadlines"
    )
    recently_completed: list[dict] = dspy.InputField(
        desc="Recently completed tickets for context"
    )

    greeting: str = dspy.OutputField(
        desc="Personalized greeting based on time and work state"
    )
    focus_today: list[str] = dspy.OutputField(
        desc="Top 3 priorities to focus on today"
    )
    blockers: list[str] = dspy.OutputField(
        desc="Blockers that need attention"
    )
    quick_wins: list[str] = dspy.OutputField(
        desc="Quick wins that can be completed today"
    )


class DailySummaryModule(dspy.Module):
    """Module for generating daily work summaries."""

    def __init__(self):
        super().__init__()
        self.summarize = dspy.ChainOfThought(DailySummary)

    def forward(
        self,
        in_progress: list[dict],
        blocked: list[dict],
        due_soon: list[dict],
        recently_completed: list[dict] | None = None,
    ):
        """Generate a daily summary.

        Args:
            in_progress: Tickets in progress
            blocked: Blocked tickets
            due_soon: Tickets due soon
            recently_completed: Recently completed tickets

        Returns:
            Daily summary with greeting, focus areas, blockers, and wins
        """
        result = self.summarize(
            in_progress=in_progress,
            blocked=blocked,
            due_soon=due_soon,
            recently_completed=recently_completed or [],
        )
        return result


# ============================================================================
# ACTION DECIDER MODULE (Chat Interface)
# ============================================================================


class ActionDecider(dspy.Signature):
    """Decide which action to execute based on user message.

    Actions:
    - create: Create a new ticket
    - update: Update existing ticket metadata
    - move: Move ticket to different status
    - search: Search for tickets
    - summarize: Generate summary of work
    - decompose: Break down a task
    - none: Conversational response without action
    """

    user_message: str = dspy.InputField(
        desc="User's natural language message"
    )
    current_context: dict = dspy.InputField(
        desc="Current board context (tickets, view, filters)"
    )

    action: Literal[
        "create",
        "update",
        "move",
        "search",
        "summarize",
        "decompose",
        "none",
    ] = dspy.OutputField(desc="Action to perform")
    params: dict = dspy.OutputField(
        desc="Parameters for the action (structure depends on action type)"
    )
    response: str = dspy.OutputField(
        desc="Natural language response to user"
    )


class ActionDeciderModule(dspy.Module):
    """Module for chat interface and action decision."""

    def __init__(self):
        super().__init__()
        self.decide = dspy.ChainOfThought(ActionDecider)

    def forward(self, user_message: str, current_context: dict):
        """Decide action based on user message.

        Args:
            user_message: User's message
            current_context: Current board state

        Returns:
            Action decision with action type, params, and response
        """
        result = self.decide(
            user_message=user_message,
            current_context=current_context,
        )
        return result
