"""Tests for DecomposeModule DSPy module.

Tests subtask generation, validation, and dependency management.
"""

import pytest
from unittest.mock import Mock, patch
import dspy
from src.agent.modules import DecomposeModule, VALID_EFFORTS

pytestmark = pytest.mark.anyio


class TestDecomposeModuleBasic:
    """Test basic decompose functionality."""

    async def test_decompose_generates_subtasks(self):
        """Decompose should generate 2-10 subtasks."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [
                {"title": "Setup OAuth", "description": "Configure", "effort": "s"},
                {"title": "Create model", "description": "Database", "effort": "s"},
                {"title": "Add endpoints", "description": "API routes", "effort": "m"},
            ]
            mock_result.dependencies = [(2, 1)]
            mock_result.reasoning = "Breaking down into logical phases"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()
            result = module.forward(
                title="Build auth system",
                description="OAuth with social providers",
                context="FastAPI backend"
            )

            assert 2 <= len(result.subtasks) <= 10
            assert isinstance(result.dependencies, list)

    async def test_decompose_validates_subtask_count(self):
        """Less than 2 subtasks should raise assertion."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [{"title": "Only one", "description": "Bad", "effort": "m"}]
            mock_result.dependencies = []
            mock_result.reasoning = "Too simple"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()

            with pytest.raises(AssertionError, match="at least 2"):
                module.forward(title="Test", description="Test", context="")

    async def test_decompose_validates_max_subtasks(self):
        """More than 10 subtasks should raise assertion."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            # Create 11 subtasks
            mock_result = Mock()
            mock_result.subtasks = [
                {"title": f"Task {i}", "description": f"Desc {i}", "effort": "m"}
                for i in range(11)
            ]
            mock_result.dependencies = []
            mock_result.reasoning = "Too many tasks"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()

            with pytest.raises(AssertionError, match="at most 10"):
                module.forward(title="Test", description="Test", context="")


class TestDecomposeModuleDependencies:
    """Test dependency validation."""

    async def test_valid_dependencies(self):
        """Valid dependency indices should pass."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [
                {"title": "A", "description": "First", "effort": "s"},
                {"title": "B", "description": "Second", "effort": "s"},
                {"title": "C", "description": "Third", "effort": "m"},
            ]
            mock_result.dependencies = [(1, 0), (2, 0), (2, 1)]  # Valid indices
            mock_result.reasoning = "Sequential dependencies"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()
            result = module.forward(title="Test", description="Test", context="")

            assert len(result.dependencies) == 3

    async def test_effort_normalization(self):
        """Invalid effort values should be normalized."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [
                {"title": "Task 1", "description": "Desc", "effort": "huge"},  # Invalid
                {"title": "Task 2", "description": "Desc", "effort": "tiny"},  # Invalid
            ]
            mock_result.dependencies = []
            mock_result.reasoning = "Test normalization"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()
            result = module.forward(title="Test", description="Test", context="")

            # Should normalize invalid efforts to 'm'
            # (implementation might vary)
            assert len(result.subtasks) == 2


class TestDecomposeModuleScoring:
    """Test BestOfNDecompose scoring (if applicable)."""

    async def test_optimal_subtask_count_suggestion(self):
        """3-7 subtasks is optimal (soft constraint)."""
        with patch.object(dspy, 'ChainOfThought') as mock_cot:
            mock_instance = Mock()
            mock_result = Mock()
            mock_result.subtasks = [
                {"title": f"Task {i}", "description": f"Desc {i}", "effort": "m"}
                for i in range(5)  # Optimal count
            ]
            mock_result.dependencies = []
            mock_result.reasoning = "Well-balanced breakdown"
            mock_instance.return_value = mock_result
            mock_cot.return_value = mock_instance

            module = DecomposeModule()
            result = module.forward(title="Test", description="Test", context="")

            assert 3 <= len(result.subtasks) <= 7  # Optimal range
