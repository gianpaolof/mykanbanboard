"""Token budget management for context layers.

Manages token allocation across context layers to stay within
model limits while prioritizing the most relevant information.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import logging

from .layers import ContextLayer, ContextPriority

logger = logging.getLogger(__name__)


class ModelTokenLimits(Enum):
    """Token limits for different models."""
    CLAUDE_SONNET = 180_000   # Claude 3.5 Sonnet context window
    CLAUDE_HAIKU = 180_000    # Claude 3.5 Haiku context window
    GPT4_TURBO = 128_000      # GPT-4 Turbo context window
    GPT4O = 128_000           # GPT-4o context window
    DEFAULT = 100_000         # Safe default


@dataclass
class TokenAllocation:
    """Token allocation for a single context layer."""
    layer_name: str
    priority: ContextPriority
    requested_tokens: int
    allocated_tokens: int
    was_truncated: bool = False


@dataclass
class TokenBudget:
    """Complete token budget with allocations."""
    total_budget: int
    reserved_for_output: int
    available_for_context: int
    allocations: list[TokenAllocation] = field(default_factory=list)
    total_allocated: int = 0
    remaining: int = 0

    def __post_init__(self):
        self.remaining = self.available_for_context - self.total_allocated


class TokenBudgetManager:
    """Manages token budget allocation across context layers.

    Strategies:
    1. Reserve tokens for model output (typically 2000-4000)
    2. Allocate by priority: CRITICAL -> HIGH -> MEDIUM -> LOW
    3. Within each priority level, allocate proportionally
    4. Truncate/summarize when layers exceed allocation
    """

    # Default token allocations per operation type
    DEFAULT_BUDGETS = {
        "triage": {
            "total": 4000,
            "output_reserve": 500,
            "global": 500,
            "relevant": 1500,
            "operation": 1000,
        },
        "decompose": {
            "total": 6000,
            "output_reserve": 1500,
            "global": 500,
            "relevant": 2000,
            "operation": 1500,
        },
        "chat": {
            "total": 8000,
            "output_reserve": 1000,
            "global": 1000,
            "relevant": 3000,
            "operation": 2500,
        },
        "daily_summary": {
            "total": 10000,
            "output_reserve": 2000,
            "global": 1000,
            "relevant": 4000,
            "operation": 2500,
        },
        "analyze": {
            "total": 12000,
            "output_reserve": 2500,
            "global": 1000,
            "relevant": 5000,
            "operation": 3000,
        },
        "default": {
            "total": 6000,
            "output_reserve": 1000,
            "global": 800,
            "relevant": 2500,
            "operation": 1500,
        },
    }

    def __init__(
        self,
        model_limit: int = ModelTokenLimits.DEFAULT.value,
        safety_margin: float = 0.9,  # Use 90% of limit as safety
    ):
        """Initialize the token budget manager.

        Args:
            model_limit: Maximum tokens for the model
            safety_margin: Fraction of limit to use (safety buffer)
        """
        self.model_limit = model_limit
        self.safety_margin = safety_margin
        self.effective_limit = int(model_limit * safety_margin)

    def get_budget_for_operation(self, operation_type: str) -> dict[str, int]:
        """Get the token budget configuration for an operation type.

        Args:
            operation_type: Type of operation (triage, decompose, etc.)

        Returns:
            Budget configuration dictionary
        """
        return self.DEFAULT_BUDGETS.get(
            operation_type,
            self.DEFAULT_BUDGETS["default"]
        ).copy()

    def allocate_budget(
        self,
        operation_type: str,
        layers: dict[str, ContextLayer],
        custom_budgets: Optional[dict[str, int]] = None,
    ) -> TokenBudget:
        """Allocate token budget across context layers.

        Args:
            operation_type: Type of operation being performed
            layers: Dictionary of context layers (global, relevant, operation)
            custom_budgets: Optional custom budget overrides

        Returns:
            TokenBudget with allocations for each layer
        """
        # Get base budget for operation
        budget_config = self.get_budget_for_operation(operation_type)
        if custom_budgets:
            budget_config.update(custom_budgets)

        total_budget = min(budget_config["total"], self.effective_limit)
        output_reserve = budget_config["output_reserve"]
        available = total_budget - output_reserve

        # Create budget object
        budget = TokenBudget(
            total_budget=total_budget,
            reserved_for_output=output_reserve,
            available_for_context=available,
        )

        # Sort layers by priority
        sorted_layers = sorted(
            layers.items(),
            key=lambda x: x[1].priority.value
        )

        # Allocate tokens by priority
        remaining = available
        for layer_name, layer in sorted_layers:
            # Get target allocation for this layer type
            layer_type = self._get_layer_type(layer_name)
            target = budget_config.get(layer_type, 1000)

            # Don't exceed remaining budget
            allocated = min(target, remaining, layer.estimated_tokens)

            # Check if truncation is needed
            was_truncated = layer.estimated_tokens > allocated

            allocation = TokenAllocation(
                layer_name=layer_name,
                priority=layer.priority,
                requested_tokens=layer.estimated_tokens,
                allocated_tokens=allocated,
                was_truncated=was_truncated,
            )
            budget.allocations.append(allocation)
            budget.total_allocated += allocated
            remaining -= allocated

            if was_truncated:
                logger.debug(
                    f"Layer '{layer_name}' truncated: "
                    f"{layer.estimated_tokens} -> {allocated} tokens"
                )

        budget.remaining = remaining
        return budget

    def _get_layer_type(self, layer_name: str) -> str:
        """Map layer name to budget key."""
        if "global" in layer_name.lower():
            return "global"
        elif "relevant" in layer_name.lower() or "similar" in layer_name.lower():
            return "relevant"
        elif "operation" in layer_name.lower() or "current" in layer_name.lower():
            return "operation"
        return "operation"

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a string.

        Uses a simple heuristic: ~4 characters per token for English text.
        This is an approximation - actual tokenization varies by model.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Rule of thumb: ~4 chars per token for mixed content
        # Could be improved with actual tokenizer if needed
        return len(text) // 4

    def fits_in_budget(self, text: str, budget: int) -> bool:
        """Check if text fits within a token budget.

        Args:
            text: Text to check
            budget: Token budget

        Returns:
            True if text fits
        """
        return self.estimate_tokens(text) <= budget

    def truncate_to_budget(
        self,
        text: str,
        budget: int,
        truncation_suffix: str = "...",
    ) -> str:
        """Truncate text to fit within a token budget.

        Args:
            text: Text to truncate
            budget: Token budget
            truncation_suffix: Suffix to add when truncating

        Returns:
            Truncated text
        """
        if self.fits_in_budget(text, budget):
            return text

        # Calculate max characters
        max_chars = budget * 4 - len(truncation_suffix)
        if max_chars <= 0:
            return truncation_suffix

        # Find a good breakpoint (end of sentence or word)
        truncated = text[:max_chars]

        # Try to end at sentence boundary
        last_period = truncated.rfind(". ")
        if last_period > max_chars * 0.7:  # Only if we keep 70%+ of content
            truncated = truncated[:last_period + 1]
        else:
            # End at word boundary
            last_space = truncated.rfind(" ")
            if last_space > max_chars * 0.9:
                truncated = truncated[:last_space]

        return truncated + truncation_suffix


def create_budget_manager(
    model_name: str = "claude-sonnet",
    safety_margin: float = 0.9,
) -> TokenBudgetManager:
    """Factory function to create a TokenBudgetManager.

    Args:
        model_name: Name of the model to use
        safety_margin: Safety margin for token budget

    Returns:
        Configured TokenBudgetManager
    """
    model_limits = {
        "claude-sonnet": ModelTokenLimits.CLAUDE_SONNET.value,
        "claude-haiku": ModelTokenLimits.CLAUDE_HAIKU.value,
        "gpt-4-turbo": ModelTokenLimits.GPT4_TURBO.value,
        "gpt-4o": ModelTokenLimits.GPT4O.value,
    }

    limit = model_limits.get(model_name.lower(), ModelTokenLimits.DEFAULT.value)
    return TokenBudgetManager(model_limit=limit, safety_margin=safety_margin)
