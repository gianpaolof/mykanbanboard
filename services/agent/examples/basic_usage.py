"""Basic usage examples for Kanban AI agent modules.

This script demonstrates how to use each DSPy module independently.
"""

import os
from dotenv import load_dotenv
import dspy

from src.agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
)
from src.db.chroma import ChromaManager

# Load environment variables
load_dotenv()


def setup_dspy():
    """Initialize DSPy with Claude."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    lm = dspy.LM(
        model="anthropic/claude-sonnet-4-20250514",
        api_key=api_key,
        temperature=0.7,
        max_tokens=2048,
    )
    dspy.configure(lm=lm)
    print("✓ DSPy configured with Claude")


def example_triage():
    """Example: Auto-triage a ticket."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Auto-Triage")
    print("="*60)

    module = TriageModule()

    # Example 1: Urgent bug
    result = module(
        title="Production API returning 500 errors",
        description="Users are getting 500 errors when trying to access /api/users endpoint",
        existing_labels=["bug", "backend", "api", "urgent", "performance"],
    )

    print(f"\nTicket: 'Production API returning 500 errors'")
    print(f"Priority: {result.priority}")
    print(f"Labels: {', '.join(result.labels)}")
    print(f"Effort: {result.effort_estimate}")
    print(f"Reasoning: {result.reasoning}")

    # Example 2: Feature request
    print("\n" + "-"*60)

    result = module(
        title="Add dark mode to settings",
        description="Users want ability to switch between light and dark theme",
        existing_labels=["feature", "ui", "enhancement", "design"],
    )

    print(f"\nTicket: 'Add dark mode to settings'")
    print(f"Priority: {result.priority}")
    print(f"Labels: {', '.join(result.labels)}")
    print(f"Effort: {result.effort_estimate}")
    print(f"Reasoning: {result.reasoning}")


def example_decompose():
    """Example: Decompose a complex task."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Task Decomposition")
    print("="*60)

    module = DecomposeModule()

    result = module(
        title="Build complete authentication system",
        description="""
        Implement a full authentication system with:
        - Email/password login
        - OAuth (Google, GitHub)
        - Password reset flow
        - Email verification
        - JWT token management
        """,
        context="FastAPI backend, React frontend, PostgreSQL database",
    )

    print(f"\nTask: 'Build complete authentication system'")
    print(f"\nSubtasks ({len(result.subtasks)}):")
    for i, subtask in enumerate(result.subtasks, 1):
        print(f"\n{i}. {subtask['title']} [{subtask['effort']}]")
        print(f"   {subtask['description']}")

    if result.dependencies:
        print(f"\nDependencies: {result.dependencies}")

    print(f"\nStrategy: {result.reasoning}")


def example_daily_summary():
    """Example: Generate daily summary."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Daily Summary")
    print("="*60)

    module = DailySummaryModule()

    result = module(
        in_progress=[
            {
                "id": "1",
                "title": "Fix login bug on Safari",
                "priority": "high",
                "effort": "s",
            },
            {
                "id": "2",
                "title": "Update API documentation",
                "priority": "medium",
                "effort": "m",
            },
        ],
        blocked=[
            {
                "id": "3",
                "title": "Deploy v2.0 to production",
                "reason": "Waiting for QA approval",
                "priority": "critical",
            },
        ],
        due_soon=[
            {
                "id": "4",
                "title": "Q1 performance review",
                "due_date": "2024-01-15",
                "priority": "high",
            },
        ],
        recently_completed=[
            {
                "id": "5",
                "title": "Add dark mode support",
                "completed_at": "2024-01-10",
            },
        ],
    )

    print(f"\n{result.greeting}\n")

    print("🎯 Focus Today:")
    for i, focus in enumerate(result.focus_today, 1):
        print(f"   {i}. {focus}")

    if result.blockers:
        print("\n🚫 Blockers:")
        for blocker in result.blockers:
            print(f"   • {blocker}")

    if result.quick_wins:
        print("\n✨ Quick Wins:")
        for win in result.quick_wins:
            print(f"   • {win}")


def example_chat():
    """Example: Chat interaction with action detection."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Chat Interface")
    print("="*60)

    module = ActionDeciderModule()

    test_messages = [
        "Create a ticket to fix the login bug",
        "What should I focus on today?",
        "Find all tickets related to authentication",
        "Move ticket #123 to done",
    ]

    context = {
        "current_view": "board",
        "tickets": [
            {"id": "123", "title": "Fix login", "status": "in_progress"},
            {"id": "124", "title": "Add OAuth", "status": "todo"},
        ],
    }

    for message in test_messages:
        print(f"\n💬 User: {message}")

        result = module(
            user_message=message,
            current_context=context,
        )

        print(f"🤖 Action: {result.action}")
        if result.params:
            print(f"   Params: {result.params}")
        print(f"   Response: {result.response}")


def example_semantic_search():
    """Example: Semantic search with ChromaDB."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Semantic Search")
    print("="*60)

    # Initialize ChromaDB
    chroma = ChromaManager()

    # Add some sample tickets
    sample_tickets = [
        {
            "id": "ticket-1",
            "title": "Fix authentication bug in Safari",
            "description": "Users cannot login when using Safari browser",
            "metadata": {"priority": "high", "labels": ["bug", "auth"]},
        },
        {
            "id": "ticket-2",
            "title": "Add OAuth support for Google",
            "description": "Implement Google OAuth authentication flow",
            "metadata": {"priority": "medium", "labels": ["feature", "auth"]},
        },
        {
            "id": "ticket-3",
            "title": "Optimize database queries",
            "description": "Slow performance on user listing page",
            "metadata": {"priority": "high", "labels": ["performance", "backend"]},
        },
        {
            "id": "ticket-4",
            "title": "Update login page design",
            "description": "Redesign login page to match new brand guidelines",
            "metadata": {"priority": "low", "labels": ["design", "ui"]},
        },
    ]

    print("\nIndexing tickets...")
    for ticket in sample_tickets:
        chroma.add_ticket(
            ticket_id=ticket["id"],
            title=ticket["title"],
            description=ticket["description"],
            metadata=ticket["metadata"],
        )

    print(f"✓ Indexed {len(sample_tickets)} tickets\n")

    # Search examples
    queries = [
        "authentication login issues",
        "performance problems",
        "design and UI",
    ]

    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        results = chroma.search(query, limit=2)

        for i, result in enumerate(results, 1):
            print(f"\n   {i}. {result['title']} (score: {result['score']:.2f})")
            print(f"      {result['description'][:60]}...")

    # Cleanup
    print("\n\nCleaning up test data...")
    chroma.clear_all()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Kanban AI Agent - Basic Usage Examples")
    print("="*60)

    try:
        # Setup DSPy
        setup_dspy()

        # Run examples
        example_triage()
        example_decompose()
        example_daily_summary()
        example_chat()

        # Note: Semantic search requires OpenAI API key
        if os.getenv("OPENAI_API_KEY"):
            example_semantic_search()
        else:
            print("\n" + "="*60)
            print("EXAMPLE 5: Semantic Search")
            print("="*60)
            print("\n⚠️  Skipped: OPENAI_API_KEY not found")
            print("Set OPENAI_API_KEY in .env to enable semantic search")

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
