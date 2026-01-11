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


# ============================================================================
# RULE PARSER MODULE (Natural Language Automation)
# ============================================================================


class ParseAutomationRule(dspy.Signature):
    """Parse a natural language automation rule into structured trigger/action pairs.

    Examples of natural language rules:
    - "When a ticket is moved to Done, add the 'completed' label"
    - "When a new ticket is created with 'bug' in the title, set priority to high"
    - "When a ticket's priority is changed to critical, notify me"
    - "When a ticket is due within 2 days, add the 'urgent' label"

    Trigger types:
    - ticket_created: A new ticket is created
    - ticket_moved: A ticket is moved to a different column
    - ticket_updated: A ticket's fields are updated
    - label_added: A label is added to a ticket
    - label_removed: A label is removed from a ticket
    - due_date_approaching: A ticket's due date is approaching (within N days)
    - priority_changed: A ticket's priority is changed

    Action types:
    - move_ticket: Move the ticket to a specific column
    - set_priority: Set the ticket's priority
    - add_label: Add a label to the ticket
    - remove_label: Remove a label from the ticket
    - set_due_date: Set or modify the due date
    - notify: Send a notification
    - auto_triage: Run AI triage on the ticket
    """

    natural_language: str = dspy.InputField(
        desc="Natural language description of the automation rule"
    )
    board_context: dict = dspy.InputField(
        desc="Board context including available columns, labels, and example tickets"
    )

    rule_name: str = dspy.OutputField(
        desc="Short, descriptive name for the rule (max 50 chars)"
    )
    trigger_type: Literal[
        "ticket_created",
        "ticket_moved",
        "ticket_updated",
        "label_added",
        "label_removed",
        "due_date_approaching",
        "priority_changed",
    ] = dspy.OutputField(desc="Type of event that triggers the rule")
    trigger_config: dict = dspy.OutputField(
        desc="Configuration for the trigger (e.g., {column_name: 'Done'} for ticket_moved, {days_before: 2} for due_date_approaching)"
    )
    action_type: Literal[
        "move_ticket",
        "set_priority",
        "add_label",
        "remove_label",
        "set_due_date",
        "notify",
        "auto_triage",
    ] = dspy.OutputField(desc="Type of action to perform")
    action_config: dict = dspy.OutputField(
        desc="Configuration for the action (e.g., {label_name: 'completed'} for add_label, {priority: 'high'} for set_priority)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence score from 0.0 to 1.0 that the rule was parsed correctly"
    )
    explanation: str = dspy.OutputField(
        desc="Brief explanation of how the rule was interpreted"
    )


class RuleParserModule(dspy.Module):
    """Module for parsing natural language automation rules."""

    def __init__(self):
        super().__init__()
        self.parse = dspy.ChainOfThought(ParseAutomationRule)

    def forward(self, natural_language: str, board_context: dict | None = None):
        """Parse a natural language rule into structured format.

        Args:
            natural_language: User's natural language rule description
            board_context: Optional context about the board (columns, labels, etc.)

        Returns:
            Parsed rule with trigger type, trigger config, action type, action config
        """
        result = self.parse(
            natural_language=natural_language,
            board_context=board_context or {},
        )
        return result
