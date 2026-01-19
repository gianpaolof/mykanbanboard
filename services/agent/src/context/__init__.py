"""Context Management System for Kanban AI DSPy modules.

This module provides a sophisticated context management system with:
- Layered context architecture (Global, Relevant, Operation)
- Smart context building with token budget management
- ChromaDB integration for semantic retrieval
- Caching for expensive operations
"""

from .manager import ContextManager, get_context_manager, init_context_manager
from .builder import ContextBuilder
from .layers import (
    ContextLayer,
    GlobalContext,
    RelevantTicketsContext,
    OperationContext,
)
from .token_budget import TokenBudgetManager
from .cache import ContextCache

__all__ = [
    "ContextManager",
    "get_context_manager",
    "init_context_manager",
    "ContextBuilder",
    "ContextLayer",
    "GlobalContext",
    "RelevantTicketsContext",
    "OperationContext",
    "TokenBudgetManager",
    "ContextCache",
]
