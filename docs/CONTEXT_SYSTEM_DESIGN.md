# Context Management System Design

## Overview

The Context Management System provides sophisticated, layered context to DSPy modules in the Kanban AI agent. It addresses critical issues found during code archaeology:

1. **DailySummary receives EMPTY ticket lists** - Fixed by requiring frontend to send actual ticket data
2. **MultiHopAnalyzer has hardcoded `similar_tickets="[]"`** - Fixed by integrating ChromaDB retrieval
3. **ChromaDB not synced with SQLite** - Fixed by adding sync endpoints
4. **No context layers** - Fixed by implementing Global/Relevant/Operation layers
5. **No retrieval-based dynamic context** - Fixed by integrating semantic search

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      API ROUTES                                  │
│  /api/triage, /api/decompose, /api/chat, /api/daily-summary     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT MANAGER                               │
│  • High-level orchestration                                      │
│  • ChromaDB sync management                                      │
│  • Cache coordination                                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT BUILDER                               │
│  • Determines context needs per operation                        │
│  • Builds context layers                                         │
│  • Applies token budget constraints                              │
└───────────┬─────────────────┬─────────────────┬─────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│  GLOBAL CONTEXT   │ │ RELEVANT CONTEXT  │ │ OPERATION CONTEXT │
│  Layer 1          │ │ Layer 2           │ │ Layer 3           │
│  • Board info     │ │ • Similar tickets │ │ • Current action  │
│  • Columns        │ │ • Related by      │ │ • Target ticket   │
│  • Labels         │ │   labels          │ │ • User intent     │
│  • Conventions    │ │ • Recently        │ │ • Parameters      │
│                   │ │   modified        │ │                   │
└───────────────────┘ └─────────┬─────────┘ └───────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │      CHROMADB         │
                    │  Vector Store         │
                    │  (Semantic Search)    │
                    └───────────────────────┘
```

## Context Layers

### Layer 1: Global Project Context (Static, per-board)

Contains board-wide information that changes infrequently:

```python
@dataclass
class GlobalContext(ContextLayer):
    board_id: str
    board_name: str
    board_description: str
    columns: list[dict]           # Workflow stages
    all_labels: list[str]         # Available labels
    workflow_description: str     # How work flows
    conventions: dict             # Naming, process rules
    total_tickets: int
    tickets_by_status: dict[str, int]
    tickets_by_priority: dict[str, int]
```

**Used by:**
- All operations (provides baseline context)
- Triage (for label consistency)
- Rule parsing (for column/label validation)

**Cache TTL:** 5 minutes

### Layer 2: Relevant Tickets Context (Dynamic, via ChromaDB)

Contains dynamically retrieved related tickets:

```python
@dataclass
class RelevantTicketsContext(ContextLayer):
    similar_tickets: list[dict]   # Semantically similar
    related_by_labels: list[dict] # Share labels
    recently_modified: list[dict] # Recent activity
    query_used: str               # For debugging
    similarity_threshold: float
```

**Used by:**
- Triage (patterns from similar tickets)
- Decompose (reference task structures)
- Analyze (multi-hop reasoning input)
- Chat (relevant context for queries)

**Cache TTL:** 1 minute

### Layer 3: Operation Context (Specific to action)

Contains information specific to the current operation:

```python
@dataclass
class OperationContext(ContextLayer):
    operation_type: str           # triage, decompose, etc.
    target_ticket: dict           # The ticket being acted on
    user_intent: str              # What user wants
    parameters: dict              # Operation-specific params
    conversation_history: list    # For chat
    time_context: str             # morning, afternoon, etc.
```

**Used by:**
- All operations (operation-specific data)
- Chat (conversation continuity)
- Daily summary (time-appropriate greetings)

**Cache TTL:** Not cached (always fresh)

## Token Budget Management

Each operation has a defined token budget:

| Operation | Total | Output Reserve | Global | Relevant | Operation |
|-----------|-------|----------------|--------|----------|-----------|
| Triage    | 4000  | 500            | 500    | 1500     | 1000      |
| Decompose | 6000  | 1500           | 500    | 2000     | 1500      |
| Chat      | 8000  | 1000           | 1000   | 3000     | 2500      |
| Daily Sum | 10000 | 2000           | 1000   | 4000     | 2500      |
| Analyze   | 12000 | 2500           | 1000   | 5000     | 3000      |

### Budget Allocation Strategy

1. **Reserve for output** - Ensure model has room to respond
2. **Allocate by priority** - CRITICAL > HIGH > MEDIUM > LOW
3. **Proportional within priority** - Share remaining budget
4. **Truncate when needed** - Summarize layers that exceed budget

```python
# Example token allocation
budget = token_manager.allocate_budget(
    operation_type="analyze",
    layers={
        "global": global_context,
        "relevant": relevant_context,
        "operation": operation_context,
    }
)

# Check allocations
for alloc in budget.allocations:
    if alloc.was_truncated:
        logger.warning(f"{alloc.layer_name} truncated")
```

## ChromaDB Sync

### Problem

ChromaDB and SQLite can become out of sync:
- Tickets created in SQLite not in ChromaDB
- Deleted tickets still in ChromaDB
- Updated tickets have stale embeddings

### Solution

1. **Full sync on startup**
2. **Incremental sync on ticket changes**
3. **Periodic background sync**

```python
# Sync endpoint
@router.post("/sync-tickets")
async def sync_tickets(request: SyncTicketsRequest):
    status = await ctx_manager.sync_tickets_to_chroma(
        tickets=request.tickets,
        force_full_sync=request.force_full_sync,
    )
    return {"synced": status.tickets_in_chroma}

# Single ticket sync
await ctx_manager.sync_single_ticket(ticket, action="upsert")
await ctx_manager.sync_single_ticket(ticket, action="delete")
```

## Integration Examples

### Triage Endpoint

```python
@router.post("/triage")
async def triage_ticket(request: TriageRequestWithContext):
    ticket = {
        "id": request.ticket_id,
        "title": request.title,
        "description": request.description,
    }

    # Build context
    context = ctx_manager.get_triage_context(ticket, board_data)

    # Get enhanced labels (existing + from similar tickets)
    existing_labels = context.get_existing_labels()

    # Run triage with rich context
    result = triage_module(
        title=request.title,
        description=request.description,
        existing_labels=existing_labels,
    )
```

### Daily Summary Endpoint (FIXED)

**Before (broken):**
```python
# Empty lists passed!
result = summary_module(
    in_progress=[],
    blocked=[],
    due_soon=[],
    recently_completed=[],
)
```

**After (fixed):**
```python
@router.post("/daily-summary")
async def get_daily_summary(request: DailySummaryRequest):
    # Frontend sends ACTUAL ticket data
    in_progress = [t.model_dump() for t in request.in_progress]
    blocked = [t.model_dump() for t in request.blocked]

    # Build context with real data
    context = ctx_manager.get_daily_summary_context(
        in_progress=in_progress,
        blocked=blocked,
        due_soon=due_soon,
        recently_completed=recently_completed,
    )

    # Run with real data
    result = summary_module(
        in_progress=format_tickets(in_progress),
        blocked=format_tickets(blocked),
        due_soon=format_tickets(due_soon),
        recently_completed=format_tickets(recently_completed),
    )
```

### Analyze Endpoint (FIXED)

**Before (broken):**
```python
# Hardcoded empty similar tickets!
result = analyzer(
    ticket_title=request.title,
    ticket_description=request.description,
    similar_tickets="[]"  # ALWAYS EMPTY
)
```

**After (fixed):**
```python
@router.post("/agent/analyze")
async def analyze_ticket(request: AnalyzeRequestWithContext):
    ticket = {"title": request.title, "description": request.description}

    # Get context with REAL similar tickets from ChromaDB
    context = ctx_manager.get_analyze_context(ticket, board_data)

    # Get actual similar tickets as JSON
    similar_tickets_json = context.get_similar_tickets_json()

    # Run with real similar tickets
    result = analyzer(
        ticket_title=request.title,
        ticket_description=request.description,
        similar_tickets=similar_tickets_json,  # NOW REAL DATA!
    )
```

## Caching Strategy

### Cache Types and TTLs

| Cache Type | TTL | Description |
|------------|-----|-------------|
| global_context | 5 min | Board structure (columns, labels) |
| similar_tickets | 1 min | ChromaDB search results |
| label_context | 2 min | Label aggregations |
| embeddings | 10 min | Computed embeddings |
| board_stats | 3 min | Ticket statistics |

### Cache Invalidation

```python
# Invalidate board cache (on structure change)
ctx_manager.invalidate_board_cache(board_id)

# Clear all caches
ctx_manager.clear_all_cache()

# Auto-invalidation on sync
await ctx_manager.sync_tickets_to_chroma(tickets)
# ^ This invalidates similar_tickets cache
```

### Cache Decorators

```python
from context.cache import cached, async_cached

@cached(cache_type="global_context", ttl=300)
def get_board_labels(board_id: str) -> list[str]:
    # Expensive operation
    return fetch_labels_from_db(board_id)

@async_cached(cache_type="similar_tickets", ttl=60)
async def search_similar(query: str) -> list[dict]:
    return await chroma.search(query)
```

## File Structure

```
services/agent/src/context/
├── __init__.py           # Public exports
├── layers.py             # Context layer classes
├── builder.py            # ContextBuilder class
├── manager.py            # ContextManager (main entry)
├── token_budget.py       # Token budget management
└── cache.py              # Caching utilities
```

## Usage in Routes

```python
from ..context import ContextManager, get_context_manager

def get_ctx_manager(
    chroma: ChromaManager = Depends(get_chroma_manager),
) -> ContextManager:
    return get_context_manager(chroma)

@router.post("/api/triage")
async def triage_ticket(
    request: TriageRequest,
    ctx_manager: ContextManager = Depends(get_ctx_manager),
):
    context = ctx_manager.get_triage_context(ticket, board_data)
    # Use context...
```

## Frontend Integration

### Required Changes

1. **Daily Summary must send ticket data:**
```typescript
const response = await fetch('/api/daily-summary', {
  method: 'POST',
  body: JSON.stringify({
    in_progress: tickets.filter(t => t.status === 'in_progress'),
    blocked: tickets.filter(t => t.status === 'blocked'),
    due_soon: tickets.filter(t => isDueSoon(t)),
    recently_completed: tickets.filter(t => isRecentlyCompleted(t)),
  })
});
```

2. **Sync tickets on changes:**
```typescript
// On app startup
await fetch('/api/sync-tickets', {
  method: 'POST',
  body: JSON.stringify({ tickets: allTickets, force_full_sync: true })
});

// On ticket create/update/delete
await fetch('/api/sync-tickets', {
  method: 'POST',
  body: JSON.stringify({ tickets: [updatedTicket] })
});
```

3. **Include board context in requests:**
```typescript
const boardContext = {
  board_id: currentBoard.id,
  board_name: currentBoard.name,
  columns: columns.map(c => ({ id: c.id, name: c.name })),
  labels: Array.from(usedLabels),
};

const response = await fetch('/api/triage', {
  method: 'POST',
  body: JSON.stringify({
    ticket_id: ticket.id,
    title: ticket.title,
    description: ticket.description,
    board_context: boardContext,
  })
});
```

## Performance Considerations

1. **Caching reduces ChromaDB calls** - Similar ticket queries cached for 1 minute
2. **Token budgets prevent bloat** - Context truncated to fit model limits
3. **Lazy loading** - Only load context needed for specific operation
4. **Background sync** - ChromaDB sync doesn't block requests

## Testing

```python
import pytest
from context import ContextManager, ContextBuilder

@pytest.fixture
def context_manager(mock_chroma):
    return ContextManager(chroma_manager=mock_chroma)

def test_triage_context_includes_labels(context_manager):
    ticket = {"title": "Fix bug", "description": "Something broken"}
    board_data = {"labels": ["bug", "urgent"]}

    context = context_manager.get_triage_context(ticket, board_data)

    assert "bug" in context.get_existing_labels()
    assert "urgent" in context.get_existing_labels()

def test_analyze_context_retrieves_similar_tickets(context_manager, mock_chroma):
    mock_chroma.search.return_value = [
        {"id": "1", "title": "Similar bug", "score": 0.9}
    ]

    ticket = {"title": "Fix bug", "description": "Something broken"}
    context = context_manager.get_analyze_context(ticket)

    json_str = context.get_similar_tickets_json()
    assert "Similar bug" in json_str
```
