# Data Flow

Questa pagina descrive i flussi di dati principali in Kanban AI.

## Ticket Lifecycle

```mermaid
sequenceDiagram
    participant U as User
    participant R as React UI
    participant Z as Zustand Store
    participant T as Tauri Backend
    participant S as SQLite
    participant A as AI Agent
    participant C as ChromaDB
    participant L as LLM

    Note over U,L: 1. Ticket Creation

    U->>R: Create ticket form
    R->>Z: Optimistic update
    R->>T: invoke("create_ticket")
    T->>S: INSERT ticket
    T->>C: Add to vector store

    alt Auto-Triage Enabled
        T->>A: POST /api/triage
        A->>L: Generate triage
        L-->>A: priority, labels, effort
        A-->>T: TriageResponse
        T->>S: UPDATE ticket
        T->>C: Update embeddings
    end

    T-->>R: Ticket created
    R->>Z: Confirm update

    Note over U,L: 2. Ticket Update

    U->>R: Edit ticket
    R->>Z: Optimistic update
    R->>T: invoke("update_ticket")
    T->>S: UPDATE ticket
    T->>C: Update embeddings
    T-->>R: Success
    R->>Z: Confirm update

    Note over U,L: 3. Ticket Deletion

    U->>R: Delete ticket
    R->>Z: Optimistic remove
    R->>T: invoke("delete_ticket")
    T->>S: DELETE ticket
    T->>C: Remove from index
    T-->>R: Success
```

## Search Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as React UI
    participant T as Tauri Backend
    participant S as SQLite FTS
    participant C as ChromaDB

    U->>R: Enter search query
    R->>T: invoke("search_tickets", query)

    par Full-text Search
        T->>S: FTS query
        S-->>T: FTS results
    and Semantic Search
        T->>C: Vector similarity
        C-->>T: Semantic results
    end

    T->>T: Merge & rank results
    T-->>R: SearchResponse
    R->>U: Display results
```

### Search Ranking

```
Final Score = (0.6 × FTS Score) + (0.4 × Semantic Score) + Recency Boost

Where:
- FTS Score: BM25 relevance from SQLite FTS5
- Semantic Score: Cosine similarity from ChromaDB
- Recency Boost: +0.1 for tickets modified in last 7 days
```

## AI Chat Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as React UI
    participant T as Tauri Backend
    participant A as AI Agent
    participant D as DSPy
    participant L as LLM

    U->>R: Type message
    R->>T: invoke("chat", message)
    T->>A: POST /api/chat

    A->>D: ActionDecider
    D->>L: Decide action

    alt action = "create"
        L-->>D: {action: "create", params: {...}}
        D->>D: Execute create_ticket tool
    else action = "search"
        L-->>D: {action: "search", params: {...}}
        D->>D: Execute search_tickets tool
    else action = "summarize"
        L-->>D: {action: "summarize"}
        D->>D: DailySummaryModule
    else action = "none"
        L-->>D: {action: "none", response: "..."}
    end

    D-->>A: Result
    A-->>T: ChatResponse
    T-->>R: Response
    R->>U: Display in chat
```

## Auto-Triage Flow

```mermaid
sequenceDiagram
    participant T as Tauri Backend
    participant A as AI Agent
    participant D as DSPy/TriageModule
    participant L as LLM

    T->>A: POST /api/triage
    Note right of T: {title, description, existing_labels}

    A->>D: TriageModule.forward()

    D->>L: ChainOfThought prompt
    Note right of D: "Analyze this ticket..."

    L->>L: Reasoning steps
    L-->>D: {priority, labels, effort, reasoning}

    D->>D: Validate with Assertions
    Note right of D: Assert priority in valid set

    alt Validation Failed
        D->>L: Retry with feedback
        L-->>D: Corrected output
    end

    D-->>A: Validated result
    A-->>T: TriageResponse
```

## Decomposition Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as React UI
    participant T as Tauri Backend
    participant A as AI Agent
    participant D as DSPy
    participant L as LLM

    U->>R: Click "Decompose"
    R->>T: invoke("decompose_ticket", id)
    T->>A: POST /api/decompose

    A->>D: BestOfNDecompose (n=3)

    loop Generate N candidates
        D->>L: DecomposeTask prompt
        L-->>D: {subtasks, dependencies}
        D->>D: Score candidate
    end

    D->>D: Select best candidate
    D->>D: Validate with Assertions
    D-->>A: DecomposeResponse

    A-->>T: {subtasks, dependencies, score}
    T-->>R: Response

    R->>U: Show subtasks preview
    U->>R: Confirm creation

    loop For each subtask
        R->>T: invoke("create_ticket", subtask)
    end
```

## Sync Flow (Future)

```mermaid
sequenceDiagram
    participant L as Local App
    participant S as Sync Service
    participant R as Remote DB
    participant O as Other Devices

    Note over L,O: Initial Sync

    L->>S: Connect with auth token
    S->>R: Get latest state
    R-->>S: All tickets (since last sync)
    S-->>L: Sync package

    L->>L: Merge with local state
    L->>L: Resolve conflicts

    Note over L,O: Real-time Updates

    L->>S: Local change (create/update/delete)
    S->>R: Persist change
    S->>O: Broadcast to other devices

    O->>O: Apply change
```

## Event Flow

```mermaid
graph LR
    subgraph Frontend
        Action[User Action]
        Store[Zustand Store]
        UI[React UI]
    end

    subgraph Backend
        IPC[IPC Handler]
        DB[SQLite]
        Events[Event Emitter]
    end

    Action --> Store
    Store --> IPC
    IPC --> DB
    DB --> Events
    Events -->|ticket:created| UI
    Events -->|ticket:updated| UI
    Events -->|ticket:deleted| UI
```

### Event Types

| Event | Payload | Trigger |
|-------|---------|---------|
| `ticket:created` | `Ticket` | New ticket saved |
| `ticket:updated` | `{id, changes}` | Ticket modified |
| `ticket:deleted` | `{id}` | Ticket removed |
| `ticket:moved` | `{id, from, to}` | Column changed |
| `board:updated` | `Board` | Board structure changed |
| `ai:triage_complete` | `{ticketId, result}` | Auto-triage finished |

## State Synchronization

```mermaid
graph TB
    subgraph Sources["Data Sources"]
        SQLite[(SQLite)]
        ChromaDB[(ChromaDB)]
    end

    subgraph Cache["Cache Layer"]
        Zustand[Zustand Store]
        LocalStorage[Local Storage]
    end

    subgraph Views["UI Views"]
        Board[Board View]
        List[List View]
        Search[Search Results]
    end

    SQLite -->|Initial Load| Zustand
    ChromaDB -->|Search| Zustand
    Zustand -->|Persist| LocalStorage
    Zustand -->|Subscribe| Board
    Zustand -->|Subscribe| List
    Zustand -->|Subscribe| Search
```

### Optimistic Updates

```typescript
// Pattern for optimistic updates

async function updateTicket(id: string, changes: Partial<Ticket>) {
  // 1. Save current state for rollback
  const previousTickets = store.getState().tickets

  // 2. Optimistically update UI
  store.setState({
    tickets: tickets.map(t =>
      t.id === id ? { ...t, ...changes } : t
    )
  })

  try {
    // 3. Persist to backend
    await invoke('update_ticket', { id, changes })
  } catch (error) {
    // 4. Rollback on failure
    store.setState({ tickets: previousTickets })
    toast.error('Failed to update ticket')
  }
}
```

## Caching Strategy

### Frontend Cache

```typescript
// Zustand with persistence
const useTicketStore = create(
  persist(
    (set, get) => ({
      tickets: [],
      lastFetch: null,

      fetchTickets: async () => {
        // Check cache freshness (5 min)
        const now = Date.now()
        if (get().lastFetch && now - get().lastFetch < 300000) {
          return // Use cached data
        }

        const tickets = await invoke('get_tickets')
        set({ tickets, lastFetch: now })
      },
    }),
    {
      name: 'ticket-cache',
      partialize: (state) => ({
        tickets: state.tickets,
        lastFetch: state.lastFetch,
      }),
    }
  )
)
```

### Backend Cache

```rust
// LRU cache for frequent queries
use lru::LruCache;

struct QueryCache {
    cache: Mutex<LruCache<String, Vec<Ticket>>>,
    ttl: Duration,
}

impl QueryCache {
    fn get(&self, key: &str) -> Option<Vec<Ticket>> {
        let mut cache = self.cache.lock().unwrap();
        cache.get(key).cloned()
    }

    fn set(&self, key: String, value: Vec<Ticket>) {
        let mut cache = self.cache.lock().unwrap();
        cache.put(key, value);
    }
}
```

### AI Response Cache

```python
# Cache AI responses to avoid repeated calls
from functools import lru_cache
import hashlib

class ResponseCache:
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size

    def get_key(self, module: str, **kwargs) -> str:
        content = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(f"{module}:{content}".encode()).hexdigest()

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value
```
