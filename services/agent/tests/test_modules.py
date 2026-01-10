"""Tests for DSPy agent modules."""

import pytest
from src.agent.modules import (
    TriageModule,
    DecomposeModule,
    DailySummaryModule,
    ActionDeciderModule,
)


class TestTriageModule:
    """Tests for TriageModule."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_triage_urgent_bug(self):
        """Test triaging an urgent bug."""
        module = TriageModule()
        result = module(
            title="URGENT: Production server down",
            description="Main API is not responding, users cannot access the application",
            existing_labels=["bug", "urgent", "infra", "backend"],
        )

        # Should detect high/critical priority
        assert result.priority in ["high", "critical"]

        # Should include relevant labels
        assert isinstance(result.labels, list)
        assert len(result.labels) <= 3

        # Should provide reasoning
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_triage_feature_request(self):
        """Test triaging a feature request."""
        module = TriageModule()
        result = module(
            title="Add dark mode support",
            description="Users have requested a dark mode theme option",
            existing_labels=["feature", "ui", "enhancement"],
        )

        # Feature requests typically lower priority
        assert result.priority in ["low", "medium"]

        # Should have appropriate effort estimate
        assert result.effort_estimate in ["xs", "s", "m", "l", "xl"]


class TestDecomposeModule:
    """Tests for DecomposeModule."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_decompose_complex_task(self):
        """Test decomposing a complex task."""
        module = DecomposeModule()
        result = module(
            title="Build OAuth authentication",
            description="Implement complete OAuth flow with Google and GitHub providers",
            context="FastAPI backend, PostgreSQL database, React frontend",
        )

        # Should generate multiple subtasks
        assert isinstance(result.subtasks, list)
        assert len(result.subtasks) >= 3

        # Each subtask should have required fields
        for subtask in result.subtasks:
            assert "title" in subtask
            assert "description" in subtask
            assert "effort" in subtask

        # Should include dependencies if relevant
        assert isinstance(result.dependencies, list)

        # Should provide reasoning
        assert isinstance(result.reasoning, str)


class TestDailySummaryModule:
    """Tests for DailySummaryModule."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_daily_summary_with_tasks(self):
        """Test generating daily summary."""
        module = DailySummaryModule()
        result = module(
            in_progress=[
                {"id": "1", "title": "Fix login bug", "priority": "high"},
                {"id": "2", "title": "Update documentation", "priority": "low"},
            ],
            blocked=[
                {"id": "3", "title": "Deploy to prod", "reason": "Waiting for approval"},
            ],
            due_soon=[
                {"id": "4", "title": "Quarterly review", "due_date": "2024-01-15"},
            ],
            recently_completed=[
                {"id": "5", "title": "Add dark mode", "completed_at": "2024-01-10"},
            ],
        )

        # Should provide greeting
        assert isinstance(result.greeting, str)
        assert len(result.greeting) > 0

        # Should suggest focus areas
        assert isinstance(result.focus_today, list)
        assert len(result.focus_today) <= 3

        # Should identify blockers
        assert isinstance(result.blockers, list)

        # Should suggest quick wins
        assert isinstance(result.quick_wins, list)


class TestActionDeciderModule:
    """Tests for ActionDeciderModule."""

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_action_decider_create_intent(self):
        """Test detecting create ticket intent."""
        module = ActionDeciderModule()
        result = module(
            user_message="Create a ticket for fixing the login bug",
            current_context={"current_view": "board", "tickets": []},
        )

        # Should detect create action
        assert result.action == "create"

        # Should extract params
        assert isinstance(result.params, dict)

        # Should provide response
        assert isinstance(result.response, str)

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_action_decider_search_intent(self):
        """Test detecting search intent."""
        module = ActionDeciderModule()
        result = module(
            user_message="Find all tickets related to authentication",
            current_context={"current_view": "list", "tickets": []},
        )

        # Should detect search action
        assert result.action == "search"

        # Should have search query in params
        assert isinstance(result.params, dict)

    @pytest.mark.skip(reason="Requires valid API key and LLM setup")
    def test_action_decider_conversational(self):
        """Test conversational response without action."""
        module = ActionDeciderModule()
        result = module(
            user_message="How are you?",
            current_context={"current_view": "board", "tickets": []},
        )

        # Should detect no action needed
        assert result.action == "none"

        # Should still provide friendly response
        assert isinstance(result.response, str)
        assert len(result.response) > 0
