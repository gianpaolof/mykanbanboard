# Kanban AI Agent - API Reference

Base URL: `http://localhost:8765`

## Authentication

Currently no authentication required (local sidecar service).

## Endpoints

### Health Check

**GET** `/api/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "kanban-agent"
}
```

---

### Auto-Triage

**POST** `/api/triage`

Automatically assign priority, labels, and effort estimate to a ticket.

**Request Body:**
```json
{
  "ticket_id": "string",
  "title": "string",
  "description": "string",
  "existing_labels": ["string"]
}
```

**Response:**
```json
{
  "priority": "low" | "medium" | "high" | "critical",
  "labels": ["string"],
  "effort": "xs" | "s" | "m" | "l" | "xl",
  "reasoning": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/api/triage \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "abc-123",
    "title": "Production API returning 500 errors",
    "description": "Users getting errors on /api/users endpoint",
    "existing_labels": ["bug", "backend", "api"]
  }'
```

**Priority Criteria:**
- `critical`: Blocks production/users, immediate fix required
- `high`: Important, significant impact, 1-2 days
- `medium`: Standard, normal planning
- `low`: Nice-to-have, can wait

**Effort Criteria:**
- `xs`: < 1 hour
- `s`: 1-4 hours
- `m`: 1-2 days
- `l`: 3-5 days
- `xl`: > 1 week

---

### Task Decomposition

**POST** `/api/decompose`

Break down a complex task into actionable subtasks.

**Request Body:**
```json
{
  "ticket_id": "string",
  "title": "string",
  "description": "string",
  "context": "string"
}
```

**Response:**
```json
{
  "subtasks": [
    {
      "title": "string",
      "description": "string",
      "effort": "xs" | "s" | "m" | "l" | "xl"
    }
  ],
  "dependencies": [[0, 1]],
  "reasoning": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/api/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "abc-456",
    "title": "Build OAuth authentication",
    "description": "Implement OAuth with Google and GitHub",
    "context": "FastAPI backend, React frontend"
  }'
```

**Dependencies Format:**
Array of `[subtask_index, depends_on_index]` pairs.
Example: `[[2, 0], [3, 1]]` means subtask 2 depends on 0, subtask 3 depends on 1.

---

### Chat

**POST** `/api/chat`

Send a message to the agent and get an action decision.

**Request Body:**
```json
{
  "message": "string",
  "context": {
    "tickets": [],
    "current_view": "string"
  }
}
```

**Response:**
```json
{
  "action": "create" | "update" | "move" | "search" | "summarize" | "decompose" | "none",
  "params": {},
  "response": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a ticket for fixing the login bug",
    "context": {
      "current_view": "board",
      "tickets": []
    }
  }'
```

**Action Types:**
- `create`: Create new ticket
- `update`: Update ticket metadata
- `move`: Move ticket to different status
- `search`: Search for tickets
- `summarize`: Generate summary
- `decompose`: Break down task
- `none`: Conversational response

---

### Semantic Search

**POST** `/api/search`

Search for tickets using semantic similarity.

**Request Body:**
```json
{
  "query": "string",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "score": 0.95,
      "explanation": "string"
    }
  ],
  "query": "string"
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication login issues",
    "limit": 5
  }'
```

**Notes:**
- Requires OpenAI API key for embeddings
- Score range: 0.0 - 1.0 (higher is better)
- Results sorted by relevance

---

### Daily Summary

**GET** `/api/daily-summary`

Generate a personalized daily work summary.

**Response:**
```json
{
  "greeting": "string",
  "focus_today": ["string"],
  "blockers": ["string"],
  "quick_wins": ["string"]
}
```

**Example:**
```bash
curl http://localhost:8765/api/daily-summary
```

**Note:** Currently returns a basic summary. Will be enhanced to accept ticket context in future versions.

---

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

**Common Error Codes:**
- `400`: Invalid request
- `422`: Validation error
- `500`: Internal server error

**Example Error:**
```json
{
  "error": "validation_error",
  "message": "Field 'title' is required",
  "details": {
    "field": "title",
    "type": "missing"
  }
}
```

---

## Interactive Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

These provide:
- Interactive testing
- Request/response schemas
- Example requests
- Try-it-out functionality

---

## Rate Limiting

Default: 20 requests per minute (configurable via `MAX_REQUESTS_PER_MINUTE`)

**Headers:**
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1640000000
```

---

## WebSocket Support (Future)

WebSocket endpoint for real-time agent interaction (planned):

**WS** `/ws/agent`

```javascript
const ws = new WebSocket('ws://localhost:8765/ws/agent');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Agent:', data.message);
};

ws.send(JSON.stringify({
  type: 'chat',
  message: 'What should I do next?'
}));
```

---

## SDK Example (Python)

```python
import httpx

class KanbanAgent:
    def __init__(self, base_url="http://localhost:8765"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

    def triage(self, ticket_id, title, description, existing_labels=None):
        response = self.client.post("/api/triage", json={
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "existing_labels": existing_labels or [],
        })
        response.raise_for_status()
        return response.json()

    def decompose(self, ticket_id, title, description, context=None):
        response = self.client.post("/api/decompose", json={
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "context": context,
        })
        response.raise_for_status()
        return response.json()

    def chat(self, message, context=None):
        response = self.client.post("/api/chat", json={
            "message": message,
            "context": context or {},
        })
        response.raise_for_status()
        return response.json()

# Usage
agent = KanbanAgent()
result = agent.triage(
    ticket_id="123",
    title="Fix login bug",
    description="Users can't login",
)
print(f"Priority: {result['priority']}")
```

---

## Integration with Tauri

The Python agent runs as a sidecar alongside the Tauri app:

```rust
// Tauri command to call agent
#[tauri::command]
async fn agent_triage(
    ticket_id: String,
    title: String,
    description: String,
) -> Result<TriageResponse, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://localhost:8765/api/triage")
        .json(&json!({
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    response.json().await.map_err(|e| e.to_string())
}
```

```typescript
// Frontend usage
import { invoke } from '@tauri-apps/api/core';

const result = await invoke('agent_triage', {
  ticketId: '123',
  title: 'Fix login bug',
  description: 'Users cannot login',
});

console.log('Priority:', result.priority);
```
