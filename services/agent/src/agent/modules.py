"""DSPy modules for Kanban AI agent capabilities."""

from typing import Literal
import dspy


# ============================================================================
# COMPATIBILITY SHIM FOR DSPY.ASSERT (removed in DSPy 3.x)
# ============================================================================

def _dspy_assert(condition: bool, message: str) -> None:
    """Compatibility shim for dspy.Assert which was removed in DSPy 3.x.

    Args:
        condition: Condition to check
        message: Error message if condition is False

    Raises:
        AssertionError: If condition is False
    """
    if not condition:
        raise AssertionError(message)

# Monkey-patch dspy.Assert if it doesn't exist
if not hasattr(dspy, 'Assert'):
    dspy.Assert = _dspy_assert

# Monkey-patch dspy.Suggest (was soft constraint, now just logs)
if not hasattr(dspy, 'Suggest'):
    import logging
    logger = logging.getLogger(__name__)
    def _dspy_suggest(condition: bool, message: str) -> None:
        """Compatibility shim for dspy.Suggest - logs warning instead of failing."""
        if not condition:
            logger.warning(f"Suggestion: {message}")
    dspy.Suggest = _dspy_suggest


# ============================================================================
# VALID VALUES (used for assertions)
# ============================================================================

VALID_PRIORITIES = ("low", "medium", "high", "critical")
VALID_EFFORTS = ("xs", "s", "m", "l", "xl")
VALID_ACTIONS = ("create", "update", "move", "search", "summarize", "decompose", "none")
VALID_TRIGGER_TYPES = (
    "ticket_created",
    "ticket_moved",
    "ticket_updated",
    "label_added",
    "label_removed",
    "due_date_approaching",
    "priority_changed",
)
VALID_ACTION_TYPES = (
    "move_ticket",
    "set_priority",
    "add_label",
    "remove_label",
    "set_due_date",
    "notify",
    "auto_triage",
)


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

        # Normalize labels to list if needed
        if not isinstance(result.labels, list):
            if isinstance(result.labels, str):
                # Split comma-separated string or wrap single label
                result.labels = [label.strip() for label in result.labels.split(',') if label.strip()]
            elif result.labels is None:
                result.labels = []
            else:
                result.labels = [str(result.labels)]

        # Hard constraints - will retry automatically if failed
        dspy.Assert(
            result.priority in VALID_PRIORITIES,
            f"Priority '{result.priority}' is invalid. Must be one of: {VALID_PRIORITIES}",
        )
        dspy.Assert(
            result.effort_estimate in VALID_EFFORTS,
            f"Effort '{result.effort_estimate}' is invalid. Must be one of: {VALID_EFFORTS}",
        )

        # Soft constraints - will log warning but continue
        dspy.Suggest(
            len(result.labels) <= 3,
            f"Too many labels ({len(result.labels)}). Prefer max 3 labels for clarity.",
        )
        dspy.Suggest(
            len(result.reasoning) >= 20,
            "Reasoning should be more detailed to explain the triage decision.",
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


# ============================================================================
# BEST-OF-N DECOMPOSE MODULE
# ============================================================================


def score_decomposition(subtasks: list[dict]) -> float:
    """Score a decomposition result for quality.

    Scoring criteria:
    - +2 points for each subtask with title and description
    - +1 point if effort is valid (xs/s/m/l/xl)
    - -1 point for subtasks too vague (title < 10 chars)
    - -2 points if > 7 subtasks (too granular)

    Args:
        subtasks: List of subtask dictionaries

    Returns:
        Quality score (higher is better)
    """
    score = 0.0

    for task in subtasks:
        # +2 for having both title and description
        if task.get("title") and task.get("description"):
            score += 2.0
        elif task.get("title"):
            score += 1.0  # Partial credit for title only

        # +1 for valid effort estimate
        if task.get("effort") in VALID_EFFORTS:
            score += 1.0

        # -1 for vague titles
        if len(task.get("title", "")) < 10:
            score -= 1.0

    # -2 for too many subtasks
    if len(subtasks) > 7:
        score -= 2.0

    # Bonus for optimal range (3-5 subtasks)
    if 3 <= len(subtasks) <= 5:
        score += 1.0

    return score


class BestOfNDecompose(dspy.Module):
    """Module that generates N decomposition candidates and selects the best.

    Uses a reward function to score each candidate decomposition
    and returns the highest-scoring result.
    """

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.n_candidates = n_candidates
        self.decompose = dspy.ChainOfThought(DecomposeTask)

    def forward(self, title: str, description: str, context: str = ""):
        """Generate multiple decompositions and return the best one.

        Args:
            title: Task title
            description: Task description
            context: Additional board context

        Returns:
            Best decomposition result with subtasks, dependencies, reasoning, and score
        """
        candidates = []

        for _ in range(self.n_candidates):
            try:
                result = self.decompose(
                    title=title,
                    description=description,
                    context=context or "No additional context",
                )

                # Extract subtasks from result
                subtasks = result.subtasks if isinstance(result.subtasks, list) else []

                # Validate subtasks
                valid_subtasks = []
                for subtask in subtasks:
                    if isinstance(subtask, dict) and subtask.get("title"):
                        valid_subtasks.append(subtask)

                if valid_subtasks:
                    score = score_decomposition(valid_subtasks)
                    candidates.append({
                        "score": score,
                        "result": result,
                        "subtasks": valid_subtasks,
                        "dependencies": result.dependencies if hasattr(result, "dependencies") else [],
                        "reasoning": result.reasoning if hasattr(result, "reasoning") else "",
                    })
            except Exception:
                # Skip failed decomposition attempts
                continue

        # Return best candidate or raise error if none succeeded
        if not candidates:
            dspy.Assert(False, "All decomposition attempts failed")

        best = max(candidates, key=lambda x: x["score"])

        # Validate the best result
        dspy.Assert(
            len(best["subtasks"]) >= 2,
            f"Best decomposition has too few subtasks ({len(best['subtasks'])})",
        )

        return {
            "subtasks": best["subtasks"],
            "dependencies": best["dependencies"],
            "reasoning": best["reasoning"],
            "score": best["score"],
            "candidates_evaluated": len(candidates),
        }

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

        # Hard constraints
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

        # Validate each subtask structure
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

        # Validate dependencies
        dspy.Assert(
            isinstance(result.dependencies, list),
            "Dependencies must be a list of tuples",
        )

        # Soft constraints
        dspy.Suggest(
            3 <= len(result.subtasks) <= 7,
            f"Optimal subtask count is 3-7, got {len(result.subtasks)}",
        )
        dspy.Suggest(
            len(result.reasoning) >= 30,
            "Reasoning should explain the decomposition strategy in more detail.",
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

        # Hard constraints
        dspy.Assert(
            isinstance(result.focus_today, list),
            "focus_today must be a list of strings",
        )
        dspy.Assert(
            len(result.focus_today) <= 3,
            f"focus_today must have max 3 items, got {len(result.focus_today)}",
        )
        dspy.Assert(
            isinstance(result.blockers, list),
            "blockers must be a list of strings",
        )
        dspy.Assert(
            isinstance(result.quick_wins, list),
            "quick_wins must be a list of strings",
        )
        dspy.Assert(
            len(result.greeting) >= 5,
            "Greeting must be at least 5 characters",
        )

        # Soft constraints
        dspy.Suggest(
            len(result.focus_today) >= 1,
            "Should provide at least 1 focus area for today",
        )
        dspy.Suggest(
            len(result.greeting) <= 100,
            "Greeting should be concise (under 100 chars)",
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
    board_context: dict = dspy.InputField(
        desc="Board metadata (board_id, board_name, columns, labels)"
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

    def forward(self, user_message: str, current_context: dict, board_context: dict | None = None):
        """Decide action based on user message.

        Args:
            user_message: User's message
            current_context: Current board state
            board_context: Board metadata (board_id, columns, labels)

        Returns:
            Action decision with action type, params, and response
        """
        result = self.decide(
            user_message=user_message,
            current_context=current_context,
            board_context=board_context or {},
        )

        # Hard constraints
        dspy.Assert(
            result.action in VALID_ACTIONS,
            f"Action '{result.action}' is invalid. Must be one of: {VALID_ACTIONS}",
        )
        dspy.Assert(
            isinstance(result.params, dict),
            "Action params must be a dictionary",
        )
        dspy.Assert(
            len(result.response) >= 5,
            "Response must be at least 5 characters",
        )

        # Validate params based on action type
        if result.action == "create":
            dspy.Assert(
                "title" in result.params,
                "Create action requires 'title' in params",
            )
        elif result.action == "move":
            dspy.Assert(
                "ticket_id" in result.params or "column" in result.params,
                "Move action requires 'ticket_id' or 'column' in params",
            )

        # Soft constraints
        dspy.Suggest(
            len(result.response) <= 500,
            "Response should be concise (under 500 chars)",
        )

        # Inject board_id into create action params if available
        if result.action == "create" and board_context:
            if "board_id" in board_context and "board_id" not in result.params:
                result.params["board_id"] = board_context["board_id"]

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

        # Hard constraints
        dspy.Assert(
            result.trigger_type in VALID_TRIGGER_TYPES,
            f"Trigger type '{result.trigger_type}' is invalid. Must be one of: {VALID_TRIGGER_TYPES}",
        )
        dspy.Assert(
            result.action_type in VALID_ACTION_TYPES,
            f"Action type '{result.action_type}' is invalid. Must be one of: {VALID_ACTION_TYPES}",
        )
        dspy.Assert(
            isinstance(result.trigger_config, dict),
            "Trigger config must be a dictionary",
        )
        dspy.Assert(
            isinstance(result.action_config, dict),
            "Action config must be a dictionary",
        )
        dspy.Assert(
            len(result.rule_name) <= 50,
            f"Rule name too long ({len(result.rule_name)} chars). Maximum is 50.",
        )

        # Validate confidence is a valid float
        try:
            confidence = float(result.confidence)
            dspy.Assert(
                0.0 <= confidence <= 1.0,
                f"Confidence {confidence} must be between 0.0 and 1.0",
            )
        except (TypeError, ValueError):
            dspy.Assert(
                False,
                f"Confidence must be a number, got: {result.confidence}",
            )

        # Validate action config based on action type
        if result.action_type == "set_priority":
            priority = result.action_config.get("priority")
            dspy.Assert(
                priority is None or priority in VALID_PRIORITIES,
                f"Invalid priority '{priority}' in action config",
            )
        elif result.action_type in ("add_label", "remove_label"):
            dspy.Assert(
                "label_name" in result.action_config or "label" in result.action_config,
                f"{result.action_type} requires 'label_name' or 'label' in action_config",
            )

        # Soft constraints
        dspy.Suggest(
            float(result.confidence) >= 0.7,
            f"Low confidence ({result.confidence}). Consider asking for clarification.",
        )
        dspy.Suggest(
            len(result.explanation) >= 20,
            "Explanation should be more detailed.",
        )

        return result
