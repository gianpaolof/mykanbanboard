"""Unit tests for the multi-hop reasoning module (src/agent/multihop.py).

Tests cover:
- MultiHopTicketAnalyzer.forward()  – all three hops, assertion paths, JSON parse branch
- MultiHopTicketAnalyzer.analyze()  – convenience wrapper
- Module-level dspy.Assert shim
"""

import json
from unittest.mock import MagicMock, patch

import dspy
import pytest

from src.agent.multihop import (
    AnalyzeContext,
    ExtractPatterns,
    GenerateInsights,
    MultiHopTicketAnalyzer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prediction(**kwargs):
    """Build a minimal DSPy-like Prediction object."""
    pred = MagicMock()
    for k, v in kwargs.items():
        setattr(pred, k, v)
    return pred


def _make_hop1(**overrides):
    defaults = {
        "context_summary": "Summary of the ticket with relevant context",
        "key_themes": "authentication,security,browser",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_hop2(**overrides):
    defaults = {
        "patterns": '["Pattern A", "Pattern B"]',
        "dependencies": "Depends on auth service",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


def _make_hop3(**overrides):
    defaults = {
        "insights": "Key insight about the ticket",
        "recommendations": "Use existing auth library",
        "estimated_complexity": "medium",
    }
    defaults.update(overrides)
    return _make_prediction(**defaults)


# ---------------------------------------------------------------------------
# Signature class existence tests
# ---------------------------------------------------------------------------


class TestSignatureClasses:
    """Verify DSPy Signature classes are importable and have expected fields."""

    def test_analyze_context_signature_exists(self):
        assert issubclass(AnalyzeContext, dspy.Signature)

    def test_extract_patterns_signature_exists(self):
        assert issubclass(ExtractPatterns, dspy.Signature)

    def test_generate_insights_signature_exists(self):
        assert issubclass(GenerateInsights, dspy.Signature)


# ---------------------------------------------------------------------------
# dspy.Assert shim tests (module-level)
# ---------------------------------------------------------------------------


class TestDSpyAssertShim:
    """The module patches dspy.Assert if absent; verify the shim works."""

    def test_assert_passes_on_true(self):
        dspy.Assert(True, "Should not raise")

    def test_assert_raises_on_false(self):
        with pytest.raises(AssertionError, match="shim message"):
            dspy.Assert(False, "shim message")


# ---------------------------------------------------------------------------
# MultiHopTicketAnalyzer – constructor
# ---------------------------------------------------------------------------


class TestMultiHopTicketAnalyzerInit:
    def test_creates_three_hops(self):
        analyzer = MultiHopTicketAnalyzer()
        assert hasattr(analyzer, "hop1")
        assert hasattr(analyzer, "hop2")
        assert hasattr(analyzer, "hop3")


# ---------------------------------------------------------------------------
# MultiHopTicketAnalyzer.forward()
# ---------------------------------------------------------------------------


class TestMultiHopForward:
    """Tests for the three-hop forward pass."""

    @pytest.fixture
    def analyzer(self):
        return MultiHopTicketAnalyzer()

    def _patch_hops(self, analyzer, hop1=None, hop2=None, hop3=None):
        """Replace the three ChainOfThought hops with mocks."""
        analyzer.hop1 = MagicMock(return_value=hop1 or _make_hop1())
        analyzer.hop2 = MagicMock(return_value=hop2 or _make_hop2())
        analyzer.hop3 = MagicMock(return_value=hop3 or _make_hop3())

    def test_forward_returns_expected_keys(self, analyzer):
        self._patch_hops(analyzer)
        result = analyzer.forward(
            ticket_title="Fix login bug",
            ticket_description="Users cannot log in via Safari",
        )
        expected_keys = {
            "context_summary", "key_themes", "patterns",
            "dependencies", "insights", "recommendations", "complexity",
        }
        assert expected_keys == set(result.keys())

    def test_forward_passes_inputs_to_hop1(self, analyzer):
        self._patch_hops(analyzer)
        analyzer.forward(
            ticket_title="My title",
            ticket_description="My description",
            similar_tickets='[{"id": "1"}]',
        )
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["ticket_title"] == "My title"
        assert call_kwargs["ticket_description"] == "My description"
        assert call_kwargs["similar_tickets"] == '[{"id": "1"}]'

    def test_forward_passes_hop1_outputs_to_hop2(self, analyzer):
        hop1 = _make_hop1(context_summary="Context ABC", key_themes="theme1,theme2")
        self._patch_hops(analyzer, hop1=hop1)
        analyzer.forward(ticket_title="T", ticket_description="D")
        call_kwargs = analyzer.hop2.call_args[1]
        assert call_kwargs["context_summary"] == "Context ABC"
        assert call_kwargs["key_themes"] == "theme1,theme2"

    def test_forward_passes_hop2_outputs_to_hop3(self, analyzer):
        hop2 = _make_hop2(patterns='["P1"]', dependencies="dep A")
        self._patch_hops(analyzer, hop2=hop2)
        analyzer.forward(ticket_title="T", ticket_description="D")
        call_kwargs = analyzer.hop3.call_args[1]
        assert call_kwargs["patterns"] == '["P1"]'
        assert call_kwargs["dependencies"] == "dep A"

    def test_forward_original_ticket_combined_in_hop3(self, analyzer):
        self._patch_hops(analyzer)
        analyzer.forward(ticket_title="Login Bug", ticket_description="Cannot log in")
        call_kwargs = analyzer.hop3.call_args[1]
        assert call_kwargs["original_ticket"] == "Login Bug: Cannot log in"

    def test_forward_key_themes_split(self, analyzer):
        hop1 = _make_hop1(key_themes="auth,security,browser")
        self._patch_hops(analyzer, hop1=hop1)
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["key_themes"] == ["auth", "security", "browser"]

    def test_forward_empty_key_themes(self, analyzer):
        hop1 = _make_hop1(key_themes="")
        self._patch_hops(analyzer, hop1=hop1)
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["key_themes"] == []

    def test_forward_patterns_valid_json_list(self, analyzer):
        hop2 = _make_hop2(patterns='["P1", "P2", "P3"]')
        self._patch_hops(analyzer, hop2=hop2)
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["patterns"] == ["P1", "P2", "P3"]

    def test_forward_patterns_invalid_json_falls_back_to_string(self, analyzer):
        hop2 = _make_hop2(patterns="not-json-at-all")
        self._patch_hops(analyzer, hop2=hop2)
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["patterns"] == ["not-json-at-all"]

    def test_forward_complexity_propagated(self, analyzer):
        hop3 = _make_hop3(estimated_complexity="high")
        self._patch_hops(analyzer, hop3=hop3)
        result = analyzer.forward(ticket_title="T", ticket_description="D")
        assert result["complexity"] == "high"

    def test_forward_default_similar_tickets(self, analyzer):
        """Calling forward without similar_tickets should default to '[]'."""
        self._patch_hops(analyzer)
        analyzer.forward(ticket_title="T", ticket_description="D")
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["similar_tickets"] == "[]"

    def test_forward_context_summary_assertion_fails(self, analyzer):
        """If hop1 context_summary is too short, dspy.Assert raises."""
        hop1 = _make_hop1(context_summary="short")  # < 10 chars
        self._patch_hops(analyzer, hop1=hop1)
        with pytest.raises(AssertionError, match="Context summary must be at least 10"):
            analyzer.forward(ticket_title="T", ticket_description="D")

    def test_forward_patterns_assertion_fails(self, analyzer):
        """If hop2 patterns is < 2 chars, dspy.Assert raises."""
        hop2 = _make_hop2(patterns="x")  # < 2 chars
        self._patch_hops(analyzer, hop2=hop2)
        with pytest.raises(AssertionError, match="Must identify at least some patterns"):
            analyzer.forward(ticket_title="T", ticket_description="D")

    def test_forward_invalid_complexity_assertion_fails(self, analyzer):
        """If hop3 complexity is not low/medium/high, dspy.Assert raises."""
        hop3 = _make_hop3(estimated_complexity="extreme")
        self._patch_hops(analyzer, hop3=hop3)
        with pytest.raises(AssertionError, match="Complexity must be low/medium/high"):
            analyzer.forward(ticket_title="T", ticket_description="D")

    def test_forward_all_valid_complexity_values(self, analyzer):
        for complexity in ("low", "medium", "high"):
            hop3 = _make_hop3(estimated_complexity=complexity)
            self._patch_hops(analyzer, hop3=hop3)
            result = analyzer.forward(ticket_title="T", ticket_description="D")
            assert result["complexity"] == complexity


# ---------------------------------------------------------------------------
# MultiHopTicketAnalyzer.analyze() convenience wrapper
# ---------------------------------------------------------------------------


class TestMultiHopAnalyze:
    """Tests for the analyze() convenience method."""

    @pytest.fixture
    def analyzer(self):
        a = MultiHopTicketAnalyzer()
        a.hop1 = MagicMock(return_value=_make_hop1())
        a.hop2 = MagicMock(return_value=_make_hop2())
        a.hop3 = MagicMock(return_value=_make_hop3())
        return a

    def test_analyze_passes_title_and_description(self, analyzer):
        ticket = {"title": "My title", "description": "My description"}
        analyzer.analyze(ticket)
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["ticket_title"] == "My title"
        assert call_kwargs["ticket_description"] == "My description"

    def test_analyze_serializes_similar_tickets(self, analyzer):
        ticket = {"title": "T", "description": "D"}
        similar = [{"id": "s1", "title": "Similar"}]
        analyzer.analyze(ticket, similar_tickets=similar)
        call_kwargs = analyzer.hop1.call_args[1]
        parsed = json.loads(call_kwargs["similar_tickets"])
        assert parsed == similar

    def test_analyze_defaults_to_empty_similar_tickets(self, analyzer):
        ticket = {"title": "T", "description": "D"}
        analyzer.analyze(ticket)
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["similar_tickets"] == "[]"

    def test_analyze_missing_title_defaults_to_empty_string(self, analyzer):
        ticket = {"description": "Only description"}
        analyzer.analyze(ticket)
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["ticket_title"] == ""

    def test_analyze_missing_description_defaults_to_empty_string(self, analyzer):
        ticket = {"title": "Only title"}
        # context_summary is long enough to pass assertion
        analyzer.analyze(ticket)
        call_kwargs = analyzer.hop1.call_args[1]
        assert call_kwargs["ticket_description"] == ""

    def test_analyze_returns_dict_with_expected_keys(self, analyzer):
        ticket = {"title": "T", "description": "D"}
        result = analyzer.analyze(ticket)
        assert "context_summary" in result
        assert "patterns" in result
        assert "complexity" in result
