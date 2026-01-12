"""Proactive suggestion module for Kanban board optimization."""

import json
from typing import Literal
import dspy


class AnalyzeBoardState(dspy.Signature):
    """Analyze Kanban board state and suggest improvements.

    Analyze the current board state and identify potential issues:
    - Stale tickets (same status > 7 days)
    - Overloaded columns (> 10 tickets)
    - Missing labels (tickets without categorization)
    - Similar tickets (potential duplicates)
    - Effort mismatches (large effort tickets completed quickly)

    Output actionable suggestions to improve workflow.
    """

    board_state: str = dspy.InputField(
        desc="JSON board state with columns, tickets, and metadata"
    )

    suggestions: str = dspy.OutputField(
        desc="JSON array of suggestions: [{type, message, action, priority}]"
    )


class ProactiveSuggester(dspy.Module):
    """Module for generating proactive board improvement suggestions.

    Analyzes the board state and identifies:
    - Stale tickets that need attention
    - Overloaded columns that may indicate bottlenecks
    - Tickets missing labels or metadata
    - Potentially duplicate tickets
    - Effort estimation issues

    Returns up to 5 prioritized suggestions.
    """

    SUGGESTION_TYPES = (
        "stale_ticket",
        "overloaded_column",
        "missing_labels",
        "similar_tickets",
        "effort_mismatch",
        "blocked_ticket",
        "priority_imbalance",
    )

    PRIORITIES = ("low", "medium", "high")

    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(AnalyzeBoardState)

    def forward(self, board_state: dict) -> list[dict]:
        """Generate suggestions from board state.

        Args:
            board_state: Dictionary containing board configuration and tickets

        Returns:
            List of suggestion dictionaries with type, message, action, priority
        """
        # Serialize board state for LLM
        state_json = json.dumps(board_state, default=str)

        # Run analysis
        result = self.analyzer(board_state=state_json)

        # Parse suggestions from JSON output
        try:
            suggestions = json.loads(result.suggestions)
            if not isinstance(suggestions, list):
                suggestions = [suggestions] if suggestions else []
        except json.JSONDecodeError:
            # Try to extract suggestions from text
            suggestions = self._parse_text_suggestions(result.suggestions)

        # Validate and normalize suggestions
        validated = []
        for suggestion in suggestions[:5]:  # Max 5 suggestions
            if isinstance(suggestion, dict):
                validated.append(self._normalize_suggestion(suggestion))

        # Sort by priority (high first)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        validated.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))

        return validated

    def _normalize_suggestion(self, suggestion: dict) -> dict:
        """Normalize a suggestion to ensure consistent structure.

        Args:
            suggestion: Raw suggestion dict

        Returns:
            Normalized suggestion with type, message, action, priority
        """
        # Normalize type
        stype = suggestion.get("type", "").lower().replace(" ", "_")
        if stype not in self.SUGGESTION_TYPES:
            stype = "stale_ticket"  # Default type

        # Normalize priority
        priority = suggestion.get("priority", "medium").lower()
        if priority not in self.PRIORITIES:
            priority = "medium"

        return {
            "type": stype,
            "message": str(suggestion.get("message", "Review this item")),
            "action": str(suggestion.get("action", "")),
            "priority": priority,
            "ticket_id": suggestion.get("ticket_id"),
            "column_id": suggestion.get("column_id"),
        }

    def _parse_text_suggestions(self, text: str) -> list[dict]:
        """Parse suggestions from plain text output.

        Args:
            text: Text output from LLM

        Returns:
            List of suggestion dicts
        """
        suggestions = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Try to extract type and message
            for stype in self.SUGGESTION_TYPES:
                if stype.replace("_", " ") in line.lower():
                    suggestions.append({
                        "type": stype,
                        "message": line,
                        "action": "",
                        "priority": "medium",
                    })
                    break
            else:
                # Generic suggestion
                if len(line) > 10:
                    suggestions.append({
                        "type": "stale_ticket",
                        "message": line,
                        "action": "",
                        "priority": "low",
                    })

        return suggestions[:5]

    def get_suggestions(
        self,
        columns: list[dict],
        tickets: list[dict],
        recent_activity: list[dict] | None = None,
    ) -> list[dict]:
        """Convenience method to get suggestions from columns and tickets.

        Args:
            columns: List of column dictionaries with id, name, position
            tickets: List of ticket dictionaries with id, title, column_id, etc.
            recent_activity: Optional list of recent activity events

        Returns:
            List of prioritized suggestions
        """
        # Build board state summary
        tickets_per_column = {}
        for col in columns:
            col_id = col.get("id")
            tickets_per_column[col_id] = sum(
                1 for t in tickets if t.get("column_id") == col_id
            )

        # Count tickets without labels
        unlabeled = sum(1 for t in tickets if not t.get("labels"))

        # Count by priority
        priority_counts = {}
        for t in tickets:
            priority = t.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        board_state = {
            "columns": columns,
            "tickets": tickets,
            "ticket_count": len(tickets),
            "tickets_per_column": tickets_per_column,
            "unlabeled_count": unlabeled,
            "priority_distribution": priority_counts,
            "recent_activity": recent_activity or [],
        }

        return self.forward(board_state)

    def quick_analysis(self, tickets: list[dict], columns: list[dict]) -> list[dict]:
        """Quick rule-based analysis without LLM call.

        Useful for fast feedback or when LLM is unavailable.

        Args:
            tickets: List of ticket dicts
            columns: List of column dicts

        Returns:
            List of suggestions based on simple rules
        """
        suggestions = []

        # Check for overloaded columns (> 10 tickets)
        tickets_per_column = {}
        for col in columns:
            col_id = col.get("id")
            col_name = col.get("name", col_id)
            count = sum(1 for t in tickets if t.get("column_id") == col_id)
            tickets_per_column[col_id] = count

            if count > 10:
                suggestions.append({
                    "type": "overloaded_column",
                    "message": f"Column '{col_name}' has {count} tickets. Consider prioritizing or archiving.",
                    "action": f"Review tickets in {col_name}",
                    "priority": "high",
                    "column_id": col_id,
                })

        # Check for tickets without labels
        unlabeled = [t for t in tickets if not t.get("labels")]
        if len(unlabeled) > 3:
            suggestions.append({
                "type": "missing_labels",
                "message": f"{len(unlabeled)} tickets are missing labels. Add labels for better organization.",
                "action": "Add labels to unlabeled tickets",
                "priority": "medium",
            })

        # Check for high priority imbalance
        high_priority = sum(1 for t in tickets if t.get("priority") == "critical")
        if high_priority > 5:
            suggestions.append({
                "type": "priority_imbalance",
                "message": f"{high_priority} critical tickets. Consider if all truly need immediate attention.",
                "action": "Review critical ticket priorities",
                "priority": "high",
            })

        return suggestions[:5]


# Export for use in routes
suggester = ProactiveSuggester()
