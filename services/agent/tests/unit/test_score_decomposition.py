"""Tests for the score_decomposition scoring function in modules.py.

score_decomposition is a pure function (no LLM) that applies a rubric:
  +2 per subtask with both title and description
  +1 per subtask with title only
  +1 per subtask with a valid effort estimate (xs/s/m/l/xl)
  -1 per subtask with a title shorter than 10 characters
  -2 if total subtasks > 7
  +1 bonus if 3 <= len(subtasks) <= 5 (optimal range)
"""

import pytest

from src.agent.modules import score_decomposition


# ---------------------------------------------------------------------------
# Happy-path / normal operation
# ---------------------------------------------------------------------------


class TestScoreDecompositionNormal:
    """Normal operation: well-formed subtask lists."""

    def test_single_good_subtask(self) -> None:
        subtasks = [
            {"title": "Set up OAuth provider", "description": "Configure Authlib", "effort": "s"}
        ]
        # +2 (title+desc) +1 (valid effort) -0 (title > 9 chars)
        assert score_decomposition(subtasks) == 3.0

    def test_optimal_three_subtasks_all_valid(self) -> None:
        subtasks = [
            {"title": "Design database schema", "description": "ERD + migrations", "effort": "s"},
            {"title": "Implement REST endpoints", "description": "FastAPI routes", "effort": "m"},
            {"title": "Write unit tests", "description": "pytest + httpx", "effort": "s"},
        ]
        # Each: +2+1 = 3  →  9 total + 1 bonus (3 in range 3-5) = 10
        assert score_decomposition(subtasks) == 10.0

    def test_five_subtasks_gets_optimal_bonus(self) -> None:
        subtasks = [
            {"title": f"Subtask number {i}", "description": "desc", "effort": "m"}
            for i in range(5)
        ]
        # Each: +2+1 = 3 → 15, +1 bonus = 16
        assert score_decomposition(subtasks) == 16.0

    def test_returns_float(self) -> None:
        result = score_decomposition([])
        assert isinstance(result, float)

    def test_empty_list_scores_zero(self) -> None:
        assert score_decomposition([]) == 0.0

    def test_score_increases_with_quality(self) -> None:
        poor = [{"title": "Fix it", "description": "", "effort": "bad"}]
        good = [{"title": "Fix login bug on Safari", "description": "Detailed desc", "effort": "m"}]
        assert score_decomposition(good) > score_decomposition(poor)


# ---------------------------------------------------------------------------
# Individual scoring rules
# ---------------------------------------------------------------------------


class TestScoreDecompositionRules:
    """Each scoring rule tested in isolation."""

    def test_title_and_description_gives_two_points(self) -> None:
        subtasks = [{"title": "Long enough title here", "description": "some desc", "effort": None}]
        score = score_decomposition(subtasks)
        # +2 (title+desc), -0 (no valid effort), -0 (title ≥ 10)
        assert score == 2.0

    def test_title_only_gives_one_point(self) -> None:
        subtasks = [{"title": "Long enough title here", "description": "", "effort": None}]
        score = score_decomposition(subtasks)
        # description is falsy, so +1 (title only), no effort bonus, no vague penalty
        assert score == 1.0

    def test_valid_effort_gives_extra_point(self) -> None:
        for effort in ("xs", "s", "m", "l", "xl"):
            subtasks = [{"title": "Long enough title", "description": "desc", "effort": effort}]
            score = score_decomposition(subtasks)
            # +2 (title+desc) +1 (valid effort) = 3
            assert score == 3.0, f"Failed for effort={effort}"

    def test_invalid_effort_no_bonus(self) -> None:
        subtasks = [{"title": "Long enough title", "description": "desc", "effort": "huge"}]
        score = score_decomposition(subtasks)
        # +2 (title+desc), no effort bonus = 2
        assert score == 2.0

    def test_vague_title_penalised(self) -> None:
        subtasks = [{"title": "Fix", "description": "some desc", "effort": "m"}]
        # +2 (title+desc) +1 (effort) -1 (title < 10 chars) = 2
        assert score_decomposition(subtasks) == 2.0

    def test_nine_subtasks_no_too_many_penalty(self) -> None:
        subtasks = [
            {"title": f"Task number {i:02d}", "description": "desc", "effort": "m"}
            for i in range(7)
        ]
        # 7 subtasks: 7 * (2+1) = 21, no penalty (7 is not > 7), no optimal bonus
        assert score_decomposition(subtasks) == 21.0

    def test_eight_subtasks_incurs_penalty(self) -> None:
        subtasks = [
            {"title": f"Task number {i:02d}", "description": "desc", "effort": "m"}
            for i in range(8)
        ]
        # 8 * 3 = 24 - 2 (>7 penalty) = 22
        assert score_decomposition(subtasks) == 22.0

    def test_no_optimal_bonus_outside_range(self) -> None:
        # 2 subtasks: below optimal range (< 3)
        subtasks = [
            {"title": "Long enough title A", "description": "desc", "effort": "m"},
            {"title": "Long enough title B", "description": "desc", "effort": "m"},
        ]
        score = score_decomposition(subtasks)
        # 2 * 3 = 6, no bonus
        assert score == 6.0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestScoreDecompositionEdgeCases:
    """Edge cases: missing keys, None values, empty strings."""

    def test_subtask_missing_title_key(self) -> None:
        subtasks = [{"description": "desc", "effort": "m"}]
        # No title → no points from title/desc pair; effort not counted; no vague penalty
        score = score_decomposition(subtasks)
        # title.get("title", "") = "" → len < 10 → -1, but no +2 and no +1 for effort
        # Actually: task.get("title") is None (falsy) → elif branch: +1 if title only
        # but task.get("title") is falsy so: neither title+desc (+2) nor title only (+1)
        # effort is "m" which IS valid → +1; but len("") < 10 → -1; net = 0
        assert score == 0.0

    def test_subtask_with_none_description(self) -> None:
        subtasks = [{"title": "Fix authentication bug", "description": None, "effort": "s"}]
        # description is None (falsy) → +1 (title only) +1 (valid effort) -0 (title ≥ 10) = 2
        assert score_decomposition(subtasks) == 2.0

    def test_subtask_with_none_effort(self) -> None:
        subtasks = [{"title": "Fix authentication bug", "description": "desc", "effort": None}]
        # None not in VALID_EFFORTS → no effort bonus; +2 (title+desc) = 2
        assert score_decomposition(subtasks) == 2.0

    def test_exactly_ten_chars_title_not_penalised(self) -> None:
        # Boundary: title length exactly 10 → NOT < 10 → no penalty
        subtasks = [{"title": "1234567890", "description": "desc", "effort": "m"}]
        # +2 +1 = 3
        assert score_decomposition(subtasks) == 3.0

    def test_nine_chars_title_penalised(self) -> None:
        subtasks = [{"title": "123456789", "description": "desc", "effort": "m"}]
        # +2 +1 -1 = 2
        assert score_decomposition(subtasks) == 2.0

    def test_extra_keys_in_subtask_ignored(self) -> None:
        subtasks = [
            {
                "title": "Long enough title",
                "description": "desc",
                "effort": "m",
                "extra_key": "ignored",
                "another": 42,
            }
        ]
        # Same as base case: +2 +1 = 3
        assert score_decomposition(subtasks) == 3.0
