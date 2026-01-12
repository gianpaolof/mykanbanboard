"""ReAct agent for Kanban AI."""
import dspy
from .tools import search_tickets, create_ticket, update_ticket, web_search, get_board_context


class KanbanReActAgent(dspy.Module):
    """ReAct agent that can reason and use tools to help with Kanban tasks."""

    def __init__(self, max_iters: int = 5):
        super().__init__()
        self.react = dspy.ReAct(
            signature="question, board_context -> answer",
            tools=[search_tickets, create_ticket, update_ticket, web_search],
            max_iters=max_iters
        )

    def forward(self, question: str) -> dict:
        """Process a question using ReAct reasoning.

        Args:
            question: User question in natural language

        Returns:
            Dict with answer and trajectory
        """
        context = get_board_context()
        result = self.react(question=question, board_context=str(context))
        return {
            "answer": result.answer,
            "trajectory": getattr(result, "trajectory", [])
        }
