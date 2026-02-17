"""Unit tests for context-aware DSPy modules (src/agent/context_modules.py).

Tests cover:
- ContextAwareTriageModule.forward()      – with and without context_manager
- ContextAwareDecomposeModule.forward()   – with and without context_manager
- DynamicMultiHopAnalyzer._retrieve_additional_context()
- DynamicMultiHopAnalyzer.forward()
- Labels normalisation branches
- Validation assertion paths
- Workflow stages extraction from columns
"""

import json
from unittest.mock import MagicMock, patch

import dspy
import pytest

from src.agent.context_modules import (
    ContextAwareDecomposeModule,
    ContextAwareTriageModule,
    DynamicMultiHopAnalyzer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_prediction(**kwargs):
    """Return a minimal object whose attributes mirror DSPy Prediction."""
    pred = MagicMock()
    for k, v in kwargs.items():
        setattr(pred, k, v)
    return pred


def _make_triage_prediction(**overrides):
    defaults = {
        "priority": "high",
        "labels": ["bug", "auth"],
        "effort_estimate": "m",
        "reasoning": "Reasoning long enough to pass soft constraint validation here",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_decompose_prediction(**overrides):
    defaults = {
        "subtasks": [
            {"title": "Subtask 1", "effort": "s"},
            {"title": "Subtask 2", "effort": "m"},
            {"title": "Subtask 3", "effort": "l"},
        ],
        "dependencies": [(1, 0)],
        "reasoning": "Decomposition reasoning",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_hop1_prediction(**overrides):
    defaults = {
        "context_summary": "Summary of initial analysis",
        "key_themes": ["auth", "security"],
        "follow_up_queries": ["authentication patterns", "security best practices"],
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_hop2_prediction(**overrides):
    defaults = {
        "dependencies": "Depends on auth service",
        "complexity": "medium",
        "risks": ["Risk A", "Risk B"],
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_hop3_prediction(**overrides):
    defaults = {
        "priority_recommendation": "high",
        "effort_estimate": "m",
        "recommendations": ["Use OAuth library", "Add rate limiting"],
        "insights": "Key insight from analysis",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


# ---------------------------------------------------------------------------
# ContextAwareTriageModule
# ---------------------------------------------------------------------------


class TestContextAwareTriageModule:
    """Tests for ContextAwareTriageModule.forward()."""

    @pytest.fixture
    def module(self):
        m = ContextAwareTriageModule(context_manager=None)
        m.triage = MagicMock(return_value=_make_triage_prediction())
        return m

    def test_forward_returns_prediction(self, module):
        result = module.forward(
            ticket_id="t1",
            title="Fix login bug",
            description="Users cannot log in",
        )
        assert result is not None
        assert result.priority == "high"

    def test_forward_without_context_manager(self, module):
        """When ctx_mgr is None, similar_tickets_json should be '[]'."""
        module.forward(
            ticket_id="t1",
            title="Title",
            description="Desc",
        )
        call_kwargs = module.triage.call_args[1]
        assert call_kwargs["similar_tickets"] == "[]"

    def test_forward_with_project_context_tech_stack(self, module):
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            project_context={"tech_stack": ["Python", "FastAPI"]},
        )
        call_kwargs = module.triage.call_args[1]
        assert "Python, FastAPI" in call_kwargs["project_context"]

    def test_forward_with_project_context_conventions(self, module):
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            project_context={"conventions": "Use conventional commits"},
        )
        call_kwargs = module.triage.call_args[1]
        assert "conventional commits" in call_kwargs["project_context"]

    def test_forward_with_project_context_priority_rules(self, module):
        rules = ["bug = high priority"]
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            project_context={"priority_rules": rules},
        )
        call_kwargs = module.triage.call_args[1]
        assert "priority" in call_kwargs["project_context"].lower()

    def test_forward_no_project_context_uses_default_string(self, module):
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.triage.call_args[1]
        assert call_kwargs["project_context"] == "No specific project context provided."

    def test_forward_with_existing_labels(self, module):
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            existing_labels=["bug", "frontend"],
        )
        call_kwargs = module.triage.call_args[1]
        assert "bug" in call_kwargs["existing_labels"]
        assert "frontend" in call_kwargs["existing_labels"]

    def test_forward_labels_already_list(self, module):
        """Labels returned as list should pass through unchanged."""
        module.triage.return_value = _make_triage_prediction(labels=["bug", "auth"])
        result = module.forward(ticket_id="t1", title="T", description="D")
        assert isinstance(result.labels, list)
        assert result.labels == ["bug", "auth"]

    def test_forward_labels_as_string_normalised(self, module):
        """Labels returned as comma-separated string should be split."""
        module.triage.return_value = _make_triage_prediction(labels="bug, auth, backend")
        result = module.forward(ticket_id="t1", title="T", description="D")
        assert result.labels == ["bug", "auth", "backend"]

    def test_forward_labels_as_none_normalised(self, module):
        """Labels returned as None should be normalised to empty list."""
        module.triage.return_value = _make_triage_prediction(labels=None)
        result = module.forward(ticket_id="t1", title="T", description="D")
        assert result.labels == []

    def test_forward_labels_as_other_type_normalised(self, module):
        """Labels as non-string/non-list should be wrapped in a list."""
        module.triage.return_value = _make_triage_prediction(labels=42)
        result = module.forward(ticket_id="t1", title="T", description="D")
        assert result.labels == ["42"]

    def test_forward_invalid_priority_raises(self, module):
        module.triage.return_value = _make_triage_prediction(priority="urgent")
        with pytest.raises(AssertionError, match="Priority"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_invalid_effort_raises(self, module):
        module.triage.return_value = _make_triage_prediction(effort_estimate="huge")
        with pytest.raises(AssertionError, match="Effort"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_with_context_manager(self, module):
        """When ctx_mgr is set, similar tickets come from it."""
        mock_ctx = MagicMock()
        mock_context = MagicMock()
        mock_context.get_similar_tickets_json.return_value = '[{"id": "s1"}]'
        mock_context.get_existing_labels.return_value = ["feature", "ux"]
        mock_ctx.get_triage_context.return_value = mock_context

        module.ctx_mgr = mock_ctx
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            existing_labels=["bug"],
        )
        call_kwargs = module.triage.call_args[1]
        assert call_kwargs["similar_tickets"] == '[{"id": "s1"}]'
        # merged labels from both existing and context
        assert "feature" in call_kwargs["existing_labels"]
        assert "bug" in call_kwargs["existing_labels"]

    def test_forward_context_manager_no_labels(self, module):
        """ctx_mgr returning no labels should not crash."""
        mock_ctx = MagicMock()
        mock_context = MagicMock()
        mock_context.get_similar_tickets_json.return_value = "[]"
        mock_context.get_existing_labels.return_value = []
        mock_ctx.get_triage_context.return_value = mock_context

        module.ctx_mgr = mock_ctx
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.triage.call_args[1]
        assert call_kwargs["similar_tickets"] == "[]"


# ---------------------------------------------------------------------------
# ContextAwareDecomposeModule
# ---------------------------------------------------------------------------


class TestContextAwareDecomposeModule:
    """Tests for ContextAwareDecomposeModule.forward()."""

    @pytest.fixture
    def module(self):
        m = ContextAwareDecomposeModule(context_manager=None)
        m.decompose = MagicMock(return_value=_make_decompose_prediction())
        return m

    def test_forward_returns_prediction(self, module):
        result = module.forward(
            ticket_id="t1",
            title="Build auth system",
            description="Implement OAuth",
        )
        assert result is not None
        assert len(result.subtasks) == 3

    def test_forward_default_workflow_stages(self, module):
        """Without ctx_mgr the default workflow string is used."""
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.decompose.call_args[1]
        assert "To Do" in call_kwargs["workflow_stages"]

    def test_forward_with_project_context_tech_stack(self, module):
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            project_context={"tech_stack": ["React", "TypeScript"]},
        )
        call_kwargs = module.decompose.call_args[1]
        assert "React, TypeScript" in call_kwargs["project_context"]

    def test_forward_with_project_context_architecture(self, module):
        module.forward(
            ticket_id="t1",
            title="T",
            description="D",
            project_context={"architecture": "microservices"},
        )
        call_kwargs = module.decompose.call_args[1]
        assert "microservices" in call_kwargs["project_context"]

    def test_forward_no_project_context(self, module):
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.decompose.call_args[1]
        assert call_kwargs["project_context"] == "No specific project context provided."

    def test_forward_assert_subtasks_is_list(self, module):
        module.decompose.return_value = _make_decompose_prediction(subtasks="not-a-list")
        with pytest.raises(AssertionError, match="Subtasks must be a list"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_assert_minimum_two_subtasks(self, module):
        module.decompose.return_value = _make_decompose_prediction(
            subtasks=[{"title": "Only one"}]
        )
        with pytest.raises(AssertionError, match="at least 2 subtasks"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_assert_maximum_ten_subtasks(self, module):
        many = [{"title": f"Sub {i}", "effort": "s"} for i in range(11)]
        module.decompose.return_value = _make_decompose_prediction(subtasks=many)
        with pytest.raises(AssertionError, match="Too many subtasks"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_assert_subtask_has_title(self, module):
        module.decompose.return_value = _make_decompose_prediction(
            subtasks=[{"no_title_key": "x"}, {"title": "OK"}]
        )
        with pytest.raises(AssertionError, match="must be a dict with at least a 'title' key"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_assert_subtask_invalid_effort(self, module):
        module.decompose.return_value = _make_decompose_prediction(
            subtasks=[
                {"title": "Sub 1", "effort": "invalid"},
                {"title": "Sub 2", "effort": "s"},
            ]
        )
        with pytest.raises(AssertionError, match="effort .* is invalid"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_assert_dependencies_is_list(self, module):
        module.decompose.return_value = _make_decompose_prediction(dependencies="bad")
        with pytest.raises(AssertionError, match="Dependencies must be a list"):
            module.forward(ticket_id="t1", title="T", description="D")

    def test_forward_subtask_without_effort_key_is_ok(self, module):
        """A subtask dict without 'effort' key should NOT trigger effort assertion."""
        module.decompose.return_value = _make_decompose_prediction(
            subtasks=[
                {"title": "Sub 1"},
                {"title": "Sub 2"},
            ]
        )
        result = module.forward(ticket_id="t1", title="T", description="D")
        assert len(result.subtasks) == 2

    def test_forward_with_context_manager_sets_similar_tasks(self, module):
        mock_ctx = MagicMock()
        mock_context = MagicMock()
        mock_context.get_similar_tickets_json.return_value = '[{"id": "s1"}]'
        mock_context.global_context = None
        mock_ctx.get_decompose_context.return_value = mock_context

        module.ctx_mgr = mock_ctx
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.decompose.call_args[1]
        assert call_kwargs["similar_tasks"] == '[{"id": "s1"}]'

    def test_forward_workflow_stages_from_columns(self, module):
        """Columns in global_context should be used to build workflow_stages."""
        mock_ctx = MagicMock()
        mock_context = MagicMock()
        mock_context.get_similar_tickets_json.return_value = "[]"
        mock_context.global_context = MagicMock()
        mock_context.global_context.columns = [
            {"name": "Backlog"},
            {"name": "In Progress"},
            {"name": "Done"},
        ]
        mock_ctx.get_decompose_context.return_value = mock_context

        module.ctx_mgr = mock_ctx
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.decompose.call_args[1]
        assert "Backlog" in call_kwargs["workflow_stages"]
        assert "In Progress" in call_kwargs["workflow_stages"]
        assert "Done" in call_kwargs["workflow_stages"]

    def test_forward_empty_columns_falls_back_to_default(self, module):
        """Columns list that evaluates to falsy uses default workflow string."""
        mock_ctx = MagicMock()
        mock_context = MagicMock()
        mock_context.get_similar_tickets_json.return_value = "[]"
        mock_context.global_context = MagicMock()
        mock_context.global_context.columns = []
        mock_ctx.get_decompose_context.return_value = mock_context

        module.ctx_mgr = mock_ctx
        module.forward(ticket_id="t1", title="T", description="D")
        call_kwargs = module.decompose.call_args[1]
        assert "To Do" in call_kwargs["workflow_stages"]


# ---------------------------------------------------------------------------
# DynamicMultiHopAnalyzer
# ---------------------------------------------------------------------------


class TestDynamicMultiHopAnalyzer:
    """Tests for DynamicMultiHopAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        a = DynamicMultiHopAnalyzer(context_manager=None)
        a.initial_analysis = MagicMock(return_value=_make_hop1_prediction())
        a.deep_analysis = MagicMock(return_value=_make_hop2_prediction())
        a.insights = MagicMock(return_value=_make_hop3_prediction())
        return a

    # -- _retrieve_additional_context --

    def test_retrieve_no_ctx_mgr_returns_message(self, analyzer):
        result = analyzer._retrieve_additional_context(["query1", "query2"])
        assert result == "No additional context available."

    def test_retrieve_ctx_mgr_no_chroma_returns_message(self, analyzer):
        mock_ctx = MagicMock()
        mock_ctx.chroma = None
        analyzer.ctx_mgr = mock_ctx
        result = analyzer._retrieve_additional_context(["q"])
        assert result == "No additional context available."

    def test_retrieve_ctx_mgr_with_results(self, analyzer):
        mock_chroma = MagicMock()
        mock_chroma.search.return_value = [
            {"title": "Auth ticket", "score": 0.9},
            {"title": "Security fix", "score": 0.75},
        ]
        mock_ctx = MagicMock()
        mock_ctx.chroma = mock_chroma
        analyzer.ctx_mgr = mock_ctx

        result = analyzer._retrieve_additional_context(["auth patterns"])
        assert "Auth ticket" in result
        assert "auth patterns" in result

    def test_retrieve_limits_to_three_queries(self, analyzer):
        mock_chroma = MagicMock()
        mock_chroma.search.return_value = [{"title": "T", "score": 0.5}]
        mock_ctx = MagicMock()
        mock_ctx.chroma = mock_chroma
        analyzer.ctx_mgr = mock_ctx

        analyzer._retrieve_additional_context(["q1", "q2", "q3", "q4", "q5"])
        # Should only have been called 3 times
        assert mock_chroma.search.call_count == 3

    def test_retrieve_handles_search_exception(self, analyzer):
        """Exceptions during search are caught and continue."""
        mock_chroma = MagicMock()
        mock_chroma.search.side_effect = Exception("DB error")
        mock_ctx = MagicMock()
        mock_ctx.chroma = mock_chroma
        analyzer.ctx_mgr = mock_ctx

        result = analyzer._retrieve_additional_context(["q1"])
        assert result == "No additional context found."

    def test_retrieve_empty_search_results(self, analyzer):
        mock_chroma = MagicMock()
        mock_chroma.search.return_value = []
        mock_ctx = MagicMock()
        mock_ctx.chroma = mock_chroma
        analyzer.ctx_mgr = mock_ctx

        result = analyzer._retrieve_additional_context(["q1"])
        assert result == "No additional context found."

    # -- forward --

    def test_forward_returns_expected_keys(self, analyzer):
        result = analyzer.forward(
            ticket_title="Fix login bug",
            ticket_description="Safari cannot log in",
        )
        expected = {
            "context_summary", "key_themes", "patterns", "dependencies",
            "complexity", "risks", "insights", "recommendations",
            "priority_recommendation", "effort_estimate",
            "hops_completed", "follow_up_queries_used",
        }
        assert expected == set(result.keys())

    def test_forward_hops_completed_is_three(self, analyzer):
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["hops_completed"] == 3

    def test_forward_follow_up_queries_counted(self, analyzer):
        analyzer.initial_analysis.return_value = _make_hop1_prediction(
            follow_up_queries=["q1", "q2"]
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["follow_up_queries_used"] == 2

    def test_forward_follow_up_queries_not_list_treated_as_empty(self, analyzer):
        analyzer.initial_analysis.return_value = _make_hop1_prediction(
            follow_up_queries="single string"
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["follow_up_queries_used"] == 0

    def test_forward_key_themes_as_list(self, analyzer):
        analyzer.initial_analysis.return_value = _make_hop1_prediction(
            key_themes=["auth", "security"]
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["key_themes"] == ["auth", "security"]

    def test_forward_key_themes_not_list_becomes_empty(self, analyzer):
        analyzer.initial_analysis.return_value = _make_hop1_prediction(
            key_themes="not a list"
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["key_themes"] == []

    def test_forward_risks_as_list(self, analyzer):
        analyzer.deep_analysis.return_value = _make_hop2_prediction(
            risks=["Risk A", "Risk B"]
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["risks"] == ["Risk A", "Risk B"]

    def test_forward_risks_not_list_becomes_empty(self, analyzer):
        analyzer.deep_analysis.return_value = _make_hop2_prediction(risks="not a list")
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["risks"] == []

    def test_forward_recommendations_as_list(self, analyzer):
        analyzer.insights.return_value = _make_hop3_prediction(
            recommendations=["Rec A", "Rec B"]
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["recommendations"] == ["Rec A", "Rec B"]

    def test_forward_recommendations_not_list_becomes_empty(self, analyzer):
        analyzer.insights.return_value = _make_hop3_prediction(
            recommendations="not a list"
        )
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["recommendations"] == []

    def test_forward_invalid_priority_raises(self, analyzer):
        analyzer.insights.return_value = _make_hop3_prediction(
            priority_recommendation="urgent"
        )
        with pytest.raises(AssertionError, match="Invalid priority"):
            analyzer.forward(ticket_title="T", ticket_description="D")

    def test_forward_invalid_effort_raises(self, analyzer):
        analyzer.insights.return_value = _make_hop3_prediction(effort_estimate="huge")
        with pytest.raises(AssertionError, match="Invalid effort"):
            analyzer.forward(ticket_title="T", ticket_description="D")

    def test_forward_all_valid_priorities(self, analyzer):
        for priority in ("low", "medium", "high", "critical"):
            analyzer.insights.return_value = _make_hop3_prediction(
                priority_recommendation=priority
            )
            result = analyzer.forward(ticket_title="T", ticket_description="D")
            assert result["priority_recommendation"] == priority

    def test_forward_all_valid_efforts(self, analyzer):
        for effort in ("xs", "s", "m", "l", "xl"):
            analyzer.insights.return_value = _make_hop3_prediction(effort_estimate=effort)
            result = analyzer.forward(ticket_title="T", ticket_description="D")
            assert result["effort_estimate"] == effort

    def test_forward_passes_hop1_summary_to_hop2(self, analyzer):
        analyzer.initial_analysis.return_value = _make_hop1_prediction(
            context_summary="Hop 1 summary"
        )
        analyzer.forward(ticket_title="T", ticket_description="D")
        hop2_kwargs = analyzer.deep_analysis.call_args[1]
        assert hop2_kwargs["initial_analysis"] == "Hop 1 summary"

    def test_forward_passes_hop2_outputs_to_hop3(self, analyzer):
        analyzer.deep_analysis.return_value = _make_hop2_prediction(
            dependencies="dep X", complexity="high"
        )
        analyzer.forward(ticket_title="T", ticket_description="D")
        hop3_kwargs = analyzer.insights.call_args[1]
        assert hop3_kwargs["dependencies"] == "dep X"
        assert hop3_kwargs["complexity"] == "high"

    def test_forward_patterns_always_empty_list(self, analyzer):
        """The current implementation hard-codes patterns to []."""
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["patterns"] == []
