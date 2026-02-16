"""Multi-hop reasoning module for complex ticket analysis."""

import json
import dspy

# Compatibility shim for dspy.Assert (removed in DSPy 3.x)
if not hasattr(dspy, 'Assert'):
    def _dspy_assert(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)
    dspy.Assert = _dspy_assert


class AnalyzeContext(dspy.Signature):
    """Analyze context from similar tickets (Hop 1)."""

    ticket_title: str = dspy.InputField(desc="Title of the ticket to analyze")
    ticket_description: str = dspy.InputField(desc="Description of the ticket")
    similar_tickets: str = dspy.InputField(desc="JSON list of similar tickets")

    context_summary: str = dspy.OutputField(desc="Summary of relevant context from similar tickets")
    key_themes: str = dspy.OutputField(desc="Comma-separated key themes identified")


class ExtractPatterns(dspy.Signature):
    """Extract patterns from analyzed context (Hop 2)."""

    context_summary: str = dspy.InputField(desc="Summary from previous analysis")
    key_themes: str = dspy.InputField(desc="Key themes identified")

    patterns: str = dspy.OutputField(desc="Identified patterns as JSON list")
    dependencies: str = dspy.OutputField(desc="Potential dependencies or blockers")


class GenerateInsights(dspy.Signature):
    """Generate actionable insights (Hop 3)."""

    patterns: str = dspy.InputField(desc="Patterns from analysis")
    dependencies: str = dspy.InputField(desc="Dependencies identified")
    original_ticket: str = dspy.InputField(desc="Original ticket title and description")

    insights: str = dspy.OutputField(desc="Key insights as bullet points")
    recommendations: str = dspy.OutputField(desc="Recommended actions")
    estimated_complexity: str = dspy.OutputField(desc="low/medium/high complexity estimate")


class MultiHopTicketAnalyzer(dspy.Module):
    """Multi-hop reasoning module for deep ticket analysis.

    Performs 3 hops:
    1. Analyze context from similar tickets
    2. Extract patterns and dependencies
    3. Generate actionable insights
    """

    def __init__(self):
        super().__init__()
        self.hop1 = dspy.ChainOfThought(AnalyzeContext)
        self.hop2 = dspy.ChainOfThought(ExtractPatterns)
        self.hop3 = dspy.ChainOfThought(GenerateInsights)

    def forward(
        self,
        ticket_title: str,
        ticket_description: str,
        similar_tickets: str = "[]"
    ) -> dict:
        """Analyze a ticket using multi-hop reasoning.

        Args:
            ticket_title: Title of the ticket
            ticket_description: Description of the ticket
            similar_tickets: JSON string of similar tickets

        Returns:
            Dict with context_summary, patterns, insights, recommendations, complexity
        """
        # Hop 1: Analyze context
        ctx = self.hop1(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            similar_tickets=similar_tickets
        )

        # Validate hop 1
        dspy.Assert(
            len(ctx.context_summary) >= 10,
            "Context summary must be at least 10 characters"
        )

        # Hop 2: Extract patterns
        patterns = self.hop2(
            context_summary=ctx.context_summary,
            key_themes=ctx.key_themes
        )

        # Validate hop 2
        dspy.Assert(
            len(patterns.patterns) >= 2,
            "Must identify at least some patterns"
        )

        # Hop 3: Generate insights
        insights = self.hop3(
            patterns=patterns.patterns,
            dependencies=patterns.dependencies,
            original_ticket=f"{ticket_title}: {ticket_description}"
        )

        # Validate hop 3
        dspy.Assert(
            insights.estimated_complexity in ["low", "medium", "high"],
            f"Complexity must be low/medium/high, got: {insights.estimated_complexity}"
        )

        # Parse patterns to list
        try:
            patterns_list = json.loads(patterns.patterns)
        except json.JSONDecodeError:
            patterns_list = [patterns.patterns]

        return {
            "context_summary": ctx.context_summary,
            "key_themes": ctx.key_themes.split(",") if ctx.key_themes else [],
            "patterns": patterns_list,
            "dependencies": patterns.dependencies,
            "insights": insights.insights,
            "recommendations": insights.recommendations,
            "complexity": insights.estimated_complexity
        }

    def analyze(self, ticket: dict, similar_tickets: list[dict] | None = None) -> dict:
        """Convenience method to analyze a ticket dict.

        Args:
            ticket: Dict with title and description
            similar_tickets: Optional list of similar ticket dicts

        Returns:
            Analysis results
        """
        return self.forward(
            ticket_title=ticket.get("title", ""),
            ticket_description=ticket.get("description", ""),
            similar_tickets=json.dumps(similar_tickets or [])
        )
