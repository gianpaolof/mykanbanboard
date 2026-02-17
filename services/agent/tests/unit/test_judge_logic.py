"""Tests for TicketQualityJudge logic that does NOT require a real LLM.

Covers:
- evaluate_ticket() result structure and overall_score math (via mocked forward)
- DSPy Assert / Suggest compatibility shims in judge.py
- The _dspy_assert shim raises AssertionError on False
- Score clamping validation (0–10 range)
"""

import pytest
from unittest.mock import MagicMock, patch

import dspy

from src.agent.judge import TicketQualityJudge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_result(clarity: int = 7, completeness: int = 8, actionability: int = 6,
                      feedback: str = "Consider adding acceptance criteria.") -> MagicMock:
    """Create a mock DSPy prediction for judge output."""
    result = MagicMock()
    result.clarity_score = clarity
    result.completeness_score = completeness
    result.actionability_score = actionability
    result.feedback = feedback
    return result


# ---------------------------------------------------------------------------
# evaluate_ticket result structure
# ---------------------------------------------------------------------------


class TestEvaluateTicketStructure:
    """evaluate_ticket() returns a well-formed dict without a real LLM."""

    @pytest.fixture
    def judge_with_mock_forward(self) -> TicketQualityJudge:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        # We bypass __init__ so no ChainOfThought is wired up
        return judge

    def test_evaluate_ticket_returns_required_keys(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        mock_result = _make_mock_result(7, 8, 6)

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket(
                {"title": "Fix bug", "description": "desc", "priority": "high",
                 "effort": "m", "labels": ["bug"]}
            )

        for key in ("clarity_score", "completeness_score", "actionability_score",
                    "feedback", "overall_score"):
            assert key in result

    def test_overall_score_is_average_of_three(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        # clarity=6, completeness=9, actionability=3 → avg = (6+9+3)/3 = 6.0
        mock_result = _make_mock_result(clarity=6, completeness=9, actionability=3)

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket({"title": "T", "description": "D",
                                            "priority": "low", "effort": "s", "labels": []})

        assert result["overall_score"] == pytest.approx(6.0)

    def test_scores_cast_to_int(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        # Return string scores to test int coercion inside evaluate_ticket
        mock_result = _make_mock_result(clarity=8, completeness=7, actionability=5)
        mock_result.clarity_score = "8"
        mock_result.completeness_score = "7"
        mock_result.actionability_score = "5"

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket({"title": "T", "description": "D",
                                            "priority": "high", "effort": "m", "labels": []})

        assert isinstance(result["clarity_score"], int)
        assert isinstance(result["completeness_score"], int)
        assert isinstance(result["actionability_score"], int)

    def test_feedback_preserved(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        feedback_text = "Add acceptance criteria and steps to reproduce."
        mock_result = _make_mock_result(feedback=feedback_text)

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket({"title": "T", "description": "D",
                                            "priority": "medium", "effort": "l", "labels": []})

        assert result["feedback"] == feedback_text

    def test_evaluate_ticket_defaults_for_missing_fields(self) -> None:
        """evaluate_ticket() should use defaults when ticket fields are absent."""
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        mock_result = _make_mock_result(5, 5, 5)

        captured_kwargs: dict = {}

        def fake_forward(**kwargs):
            captured_kwargs.update(kwargs)
            return mock_result

        with patch.object(judge, "forward", side_effect=fake_forward):
            judge.evaluate_ticket({})  # empty ticket

        assert captured_kwargs["priority"] == "medium"  # default
        assert captured_kwargs["effort"] == "m"          # default
        assert captured_kwargs["labels"] == ""           # empty list → ""

    def test_evaluate_ticket_labels_joined_as_comma_separated(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        mock_result = _make_mock_result()
        captured: dict = {}

        def fake_forward(**kwargs):
            captured.update(kwargs)
            return mock_result

        with patch.object(judge, "forward", side_effect=fake_forward):
            judge.evaluate_ticket({"labels": ["bug", "auth", "backend"]})

        assert captured["labels"] == "bug,auth,backend"

    def test_perfect_scores_give_ten_overall(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        mock_result = _make_mock_result(clarity=10, completeness=10, actionability=10)

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket({"title": "T", "description": "D",
                                            "priority": "high", "effort": "s", "labels": []})

        assert result["overall_score"] == pytest.approx(10.0)

    def test_zero_scores_give_zero_overall(self) -> None:
        judge = TicketQualityJudge.__new__(TicketQualityJudge)
        mock_result = _make_mock_result(clarity=0, completeness=0, actionability=0,
                                        feedback="This ticket needs a lot of work to be useful.")

        with patch.object(judge, "forward", return_value=mock_result):
            result = judge.evaluate_ticket({"title": "T", "description": "D",
                                            "priority": "low", "effort": "xs", "labels": []})

        assert result["overall_score"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# DSPy Assert / Suggest compatibility shims
# ---------------------------------------------------------------------------


class TestDspyCompatShims:
    """The compatibility shims defined in judge.py work correctly."""

    def test_dspy_assert_does_not_raise_on_true(self) -> None:
        # If dspy.Assert is our shim, calling it with True should be fine
        dspy.Assert(True, "should not raise")

    def test_dspy_assert_raises_on_false(self) -> None:
        with pytest.raises(AssertionError, match="bad condition"):
            dspy.Assert(False, "bad condition")

    def test_dspy_suggest_does_not_raise(self) -> None:
        # dspy.Suggest with False should log, not raise
        if hasattr(dspy, "Suggest"):
            dspy.Suggest(False, "this is just a suggestion")  # should not raise

    def test_dspy_suggest_with_true_is_noop(self) -> None:
        if hasattr(dspy, "Suggest"):
            dspy.Suggest(True, "all good")


# ---------------------------------------------------------------------------
# forward() score validation path (via mocked ChainOfThought)
# ---------------------------------------------------------------------------


class TestJudgeScoreValidation:
    """Tests that forward() validates score ranges via dspy.Assert."""

    def test_forward_raises_on_out_of_range_clarity(self) -> None:
        judge = TicketQualityJudge()
        bad_result = _make_mock_result(clarity=11, completeness=5, actionability=5,
                                       feedback="Some feedback text here.")

        with patch.object(judge, "judge", return_value=bad_result):
            with pytest.raises((AssertionError, Exception)):
                judge.forward(
                    ticket_title="Test",
                    ticket_description="desc",
                    priority="medium",
                    effort="m",
                    labels="bug",
                )

    def test_forward_raises_on_negative_score(self) -> None:
        judge = TicketQualityJudge()
        bad_result = _make_mock_result(clarity=-1, completeness=5, actionability=5,
                                       feedback="Some feedback text here.")

        with patch.object(judge, "judge", return_value=bad_result):
            with pytest.raises((AssertionError, Exception)):
                judge.forward(
                    ticket_title="Test",
                    ticket_description="desc",
                    priority="medium",
                    effort="m",
                    labels="bug",
                )

    def test_forward_accepts_boundary_scores(self) -> None:
        judge = TicketQualityJudge()
        ok_result = _make_mock_result(clarity=0, completeness=10, actionability=5,
                                      feedback="Detailed feedback about improvements needed.")

        with patch.object(judge, "judge", return_value=ok_result):
            result = judge.forward(
                ticket_title="Test ticket",
                ticket_description="Description",
                priority="low",
                effort="xs",
                labels="",
            )
        assert result is ok_result
