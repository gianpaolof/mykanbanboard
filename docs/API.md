# Kanban AI - API Reference

## Overview

Kanban AI espone due tipi di API:

1. **Tauri Commands** - IPC tra frontend React e backend Rust
2. **Agent HTTP API** - REST API del Python sidecar (localhost:8765)

---

## Tauri Commands (IPC)

### Tickets

#### get_tickets
Recupera tutti i ticket, opzionalmente filtrati per colonna.

```typescript
invoke<Ticket[]>('get_tickets', { columnId?: string })
```

**Response:**
```typescript
interface Ticket {
  id: string;
  title: string;
  description?: string;
  columnId: string;
  position: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  effort?: 'xs' | 's' | 'm' | 'l' | 'xl';
  dueDate?: string; // ISO 8601
  labels: Label[];
  createdAt: string;
  updatedAt: string;
}
```

#### get_ticket
Recupera un singolo ticket per ID.

```typescript
invoke<Ticket>('get_ticket', { id: string })
```

#### create_ticket
Crea un nuovo ticket.

```typescript
invoke<Ticket>('create_ticket', { 
  ticket: {
    title: string;
    description?: string;
    columnId: string;
    priority?: Priority;
    labels?: string[]; // label IDs
  }
})
```

#### update_ticket
Aggiorna un ticket esistente.

```typescript
invoke<Ticket>('update_ticket', {
  id: string;
  updates: {
    title?: string;
    description?: string;
    columnId?: string;
    position?: number;
    priority?: Priority;
    effort?: Effort;
    dueDate?: string;
    labels?: string[];
  }
})
```

#### delete_ticket
Elimina un ticket.

```typescript
invoke<void>('delete_ticket', { id: string })
```

#### move_ticket
Sposta un ticket in una nuova colonna/posizione.

```typescript
invoke<Ticket>('move_ticket', {
  id: string;
  columnId: string;
  position: number;
})
```

#### reorder_tickets
Riordina i ticket in una colonna.

```typescript
invoke<void>('reorder_tickets', {
  columnId: string;
  ticketIds: string[]; // nuovo ordine
})
```

---

### Columns

#### get_columns
Recupera tutte le colonne.

```typescript
invoke<Column[]>('get_columns')
```

**Response:**
```typescript
interface Column {
  id: string;
  name: string;
  position: number;
  color?: string;
  wipLimit?: number;
}
```

#### create_column
Crea una nuova colonna.

```typescript
invoke<Column>('create_column', {
  column: {
    name: string;
    color?: string;
    wipLimit?: number;
  }
})
```

#### update_column
Aggiorna una colonna.

```typescript
invoke<Column>('update_column', {
  id: string;
  updates: {
    name?: string;
    position?: number;
    color?: string;
    wipLimit?: number;
  }
})
```

#### delete_column
Elimina una colonna (deve essere vuota).

```typescript
invoke<void>('delete_column', { id: string })
```

---

### Labels

#### get_labels
Recupera tutte le labels.

```typescript
invoke<Label[]>('get_labels')
```

**Response:**
```typescript
interface Label {
  id: string;
  name: string;
  color: string;
}
```

#### create_label
Crea una nuova label.

```typescript
invoke<Label>('create_label', {
  label: {
    name: string;
    color: string;
  }
})
```

#### delete_label
Elimina una label.

```typescript
invoke<void>('delete_label', { id: string })
```

---

### Agent Proxy

#### agent_triage
Esegue auto-triage di un ticket.

```typescript
invoke<TriageResult>('agent_triage', {
  ticketId: string;
  title: string;
  description: string;
})
```

**Response:**
```typescript
interface TriageResult {
  priority: Priority;
  labels: string[];
  effort: Effort;
  reasoning: string;
}
```

#### agent_chat
Invia un messaggio all'agent.

```typescript
invoke<ChatResponse>('agent_chat', {
  message: string;
  context?: {
    currentView: string;
    selectedTicket?: string;
    // ... altri dati contestuali
  }
})
```

**Response:**
```typescript
interface ChatResponse {
  action: string;
  params: Record<string, any>;
  response: string;
}
```

#### agent_decompose
Decompone un ticket in subtask.

```typescript
invoke<DecomposeResult>('agent_decompose', {
  ticketId: string;
})
```

**Response:**
```typescript
interface DecomposeResult {
  subtasks: Array<{
    title: string;
    description: string;
    effort: Effort;
  }>;
  dependencies: Array<[number, number]>;
}
```

#### agent_daily_summary
Genera il daily summary.

```typescript
invoke<DailySummary>('agent_daily_summary')
```

**Response:**
```typescript
interface DailySummary {
  greeting: string;
  focusToday: string[];
  blockers: string[];
  wins: string[];
}
```

---

## Agent HTTP API (Python Sidecar)

Base URL: `http://127.0.0.1:8765`

### Health

#### GET /health
Check stato del server.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Triage

#### POST /api/triage
Auto-triage di un ticket.

**Request:**
```json
{
  "ticket_id": "uuid-string",
  "title": "Fix login bug",
  "description": "Users cannot login on Safari browser"
}
```

**Response:**
```json
{
  "priority": "high",
  "labels": ["bug", "auth", "browser-compat"],
  "effort": "s",
  "reasoning": "Login functionality is critical for user access. Safari-specific issues typically indicate CSS or JS compatibility problems that can be resolved quickly."
}
```

**Errors:**
- `400` - Invalid input
- `429` - Rate limited
- `500` - LLM error

---

### Chat

#### POST /api/chat
Interazione conversazionale con l'agent.

**Request:**
```json
{
  "message": "Cosa devo fare oggi?",
  "context": {
    "tickets": [
      {"id": "1", "title": "Fix bug", "status": "in_progress"},
      {"id": "2", "title": "Write docs", "status": "todo"}
    ],
    "current_view": "board"
  }
}
```

**Response:**
```json
{
  "action": "summarize",
  "params": {},
  "response": "Buongiorno! Oggi ti consiglio di concentrarti su:\n1. Completare 'Fix bug' che è già in progress\n2. Iniziare 'Write docs'\n\nHai anche 2 ticket in backlog da considerare per domani."
}
```

**Actions disponibili:**
| Action | Description | Params |
|--------|-------------|--------|
| `create_ticket` | Crea nuovo ticket | `{title, description?, priority?, labels?}` |
| `update_ticket` | Modifica ticket | `{ticket_id, updates}` |
| `move_ticket` | Sposta ticket | `{ticket_id, column_id}` |
| `search_tickets` | Cerca ticket | `{query}` |
| `summarize` | Genera summary | `{}` |
| `none` | Solo risposta | `{}` |

---

### Decompose

#### POST /api/decompose
Scompone un task in subtask.

**Request:**
```json
{
  "ticket_id": "uuid-string"
}
```

**Response:**
```json
{
  "subtasks": [
    {
      "title": "Research Safari login issues",
      "description": "Investigate known Safari bugs with form submission and session cookies",
      "effort": "xs"
    },
    {
      "title": "Fix form submission",
      "description": "Update form handling to be Safari-compatible",
      "effort": "s"
    },
    {
      "title": "Add Safari-specific tests",
      "description": "Add E2E tests running on Safari",
      "effort": "s"
    }
  ],
  "dependencies": [
    [1, 0],
    [2, 1]
  ]
}
```

---

### Daily Summary

#### GET /api/daily-summary
Genera il riepilogo giornaliero.

**Response:**
```json
{
  "greeting": "Buongiorno! Ecco il tuo riepilogo:",
  "focus_today": [
    "Completare il fix del login bug (high priority, in progress)",
    "Review PR #42 di Marco",
    "Preparare demo per meeting di domani"
  ],
  "blockers": [
    "Ticket #15 bloccato: in attesa di design mockup"
  ],
  "wins": [
    "Ticket #23 è quasi pronto, manca solo il test finale"
  ]
}
```

---

### Search

#### GET /api/search
Ricerca semantica sui ticket.

**Request:**
```
GET /api/search?query=problemi%20di%20performance&limit=5
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-1",
      "title": "Ottimizzare query database",
      "score": 0.92,
      "explanation": "Alto match semantico per 'performance' e 'ottimizzare'"
    },
    {
      "id": "uuid-2", 
      "title": "Ridurre tempo di caricamento homepage",
      "score": 0.87,
      "explanation": "Match per concetto di performance/velocità"
    }
  ]
}
```

---

### Embeddings

#### POST /api/embeddings/add
Aggiunge embedding per un ticket (chiamato automaticamente on create/update).

**Request:**
```json
{
  "ticket_id": "uuid-string",
  "title": "Fix login bug",
  "description": "Users cannot login on Safari"
}
```

**Response:**
```json
{
  "success": true
}
```

#### DELETE /api/embeddings/{ticket_id}
Rimuove embedding per un ticket (chiamato on delete).

**Response:**
```json
{
  "success": true
}
```

---

## Error Responses

Tutti gli endpoint possono ritornare errori nel formato:

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {
    // Optional additional info
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_input` | 400 | Parametri mancanti o invalidi |
| `not_found` | 404 | Risorsa non trovata |
| `rate_limited` | 429 | Troppe richieste |
| `llm_error` | 502 | Errore dal provider LLM |
| `internal_error` | 500 | Errore interno del server |

---

## Rate Limits

- **Triage/Decompose/Chat:** 20 requests/minute
- **Search:** 60 requests/minute
- **Daily Summary:** 10 requests/minute

Headers nelle response:
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1704067200
```

---

## WebSocket (Future)

Per real-time updates, sarà disponibile:

```
ws://127.0.0.1:8765/ws
```

**Events:**
```json
{"type": "ticket_created", "data": {...}}
{"type": "ticket_updated", "data": {...}}
{"type": "agent_thinking", "data": {"status": "processing"}}
{"type": "agent_response", "data": {...}}
```
