"""LLM-as-Judge module for evaluating ticket quality."""

import dspy


class JudgeTicketQuality(dspy.Signature):
    """Evaluate the quality of a Kanban ticket.

    Score each dimension from 0-10:
    - Clarity: How clear and understandable is the ticket?
    - Completeness: Does it have all necessary information?
    - Actionability: Can someone act on this immediately?
    """

    ticket_title: str = dspy.InputField(desc="Title of the ticket")
    ticket_description: str = dspy.InputField(desc="Description of the ticket")
    priority: str = dspy.InputField(desc="Assigned priority")
    effort: str = dspy.InputField(desc="Effort estimate")
    labels: str = dspy.InputField(desc="Comma-separated labels")

    clarity_score: int = dspy.OutputField(desc="Clarity score 0-10")
    completeness_score: int = dspy.OutputField(desc="Completeness score 0-10")
    actionability_score: int = dspy.OutputField(desc="Actionability score 0-10")
    feedback: str = dspy.OutputField(desc="Improvement suggestions")


class TicketQualityJudge(dspy.Module):
    """Module for judging ticket quality using LLM-as-Judge pattern."""

    def __init__(self):
        super().__init__()
        self.judge = dspy.ChainOfThought(JudgeTicketQuality)

    def forward(
        self,
        ticket_title: str,
        ticket_description: str,
        priority: str,
        effort: str,
        labels: str
    ):
        """Evaluate a ticket's quality.

        Args:
            ticket_title: Title of the ticket
            ticket_description: Description of the ticket
            priority: Assigned priority level
            effort: Effort estimate (xs/s/m/l/xl)
            labels: Comma-separated labels

        Returns:
            Quality scores and feedback
        """
        result = self.judge(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            priority=priority,
            effort=effort,
            labels=labels
        )

        # Validate scores are in range
        dspy.Assert(
            0 <= int(result.clarity_score) <= 10,
            f"Clarity score must be 0-10, got {result.clarity_score}"
        )
        dspy.Assert(
            0 <= int(result.completeness_score) <= 10,
            f"Completeness score must be 0-10, got {result.completeness_score}"
        )
        dspy.Assert(
            0 <= int(result.actionability_score) <= 10,
            f"Actionability score must be 0-10, got {result.actionability_score}"
        )

        # Soft constraint for feedback quality
        dspy.Suggest(
            len(result.feedback) >= 20,
            "Feedback should be detailed enough to be actionable"
        )

        return result

    def evaluate_ticket(self, ticket: dict) -> dict:
        """Convenience method to evaluate a ticket dict.

        Args:
            ticket: Dict with title, description, priority, effort, labels

        Returns:
            Dict with scores and feedback
        """
        result = self.forward(
            ticket_title=ticket.get("title", ""),
            ticket_description=ticket.get("description", ""),
            priority=ticket.get("priority", "medium"),
            effort=ticket.get("effort", "m"),
            labels=",".join(ticket.get("labels", []))
        )

        return {
            "clarity_score": int(result.clarity_score),
            "completeness_score": int(result.completeness_score),
            "actionability_score": int(result.actionability_score),
            "feedback": result.feedback,
            "overall_score": (
                int(result.clarity_score) +
                int(result.completeness_score) +
                int(result.actionability_score)
            ) / 3
        }
