# REST API Reference

Documentazione completa dell'API REST dell'AI Agent.

## Base URL

```
http://localhost:8765/api
```

## Autenticazione

Attualmente l'API non richiede autenticazione (localhost only).

---

## Health Check

### GET /api/health

Verifica lo stato del servizio.

**Response**

```json
{
  "status": "healthy",
  "service": "kanban-agent"
}
```

---

## Triage

### POST /api/triage

Analizza automaticamente un ticket e assegna priority, labels ed effort.

**Request Body**

| Campo | Tipo | Required | Descrizione |
|-------|------|----------|-------------|
| `ticket_id` | string | No | ID del ticket |
| `title` | string | Si | Titolo del ticket |
| `description` | string | Si | Descrizione del ticket |
| `existing_labels` | string[] | No | Labels esistenti nel board |

**Request Example**

```json
{
  "ticket_id": "abc123",
  "title": "Fix login bug on Safari",
  "description": "Users cannot login using Safari browser on iOS",
  "existing_labels": ["bug", "auth", "mobile", "frontend"]
}
```

**Response**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `priority` | string | `low`, `medium`, `high`, `critical` |
| `labels` | string[] | Max 3 labels suggerite |
| `effort` | string | `xs`, `s`, `m`, `l`, `xl` |
| `reasoning` | string | Spiegazione delle scelte |

**Response Example**

```json
{
  "priority": "high",
  "labels": ["bug", "auth", "mobile"],
  "effort": "s",
  "reasoning": "Login issues are critical for user access. Safari on iOS affects a significant user base. The intermittent nature suggests a specific browser quirk that should be fixable within half a day."
}
```

**Errors**

| Status | Descrizione |
|--------|-------------|
| 500 | Triage failed |
| 504 | Timeout (12s) |

---

## Decompose

### POST /api/decompose

Scompone un task complesso in subtask atomici.

**Request Body**

| Campo | Tipo | Required | Descrizione |
|-------|------|----------|-------------|
| `ticket_id` | string | No | ID del ticket |
| `title` | string | Si | Titolo del task |
| `description` | string | Si | Descrizione dettagliata |
| `context` | string | No | Contesto aggiuntivo dal board |

**Request Example**

```json
{
  "ticket_id": "task123",
  "title": "Implement user authentication",
  "description": "Add login/logout with JWT tokens, password reset, and OAuth2",
  "context": "Tech stack: React frontend, FastAPI backend, PostgreSQL"
}
```

**Response**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `subtasks` | object[] | Lista di subtask |
| `subtasks[].title` | string | Titolo del subtask |
| `subtasks[].description` | string | Descrizione |
| `subtasks[].effort` | string | Stima effort |
| `dependencies` | [int, int][] | Coppie di dipendenze (idx, depends_on_idx) |
| `reasoning` | string | Spiegazione della decomposizione |

**Response Example**

```json
{
  "subtasks": [
    {
      "title": "Setup JWT configuration",
      "description": "Configure JWT secret, token expiration, refresh strategy",
      "effort": "xs"
    },
    {
      "title": "Create user model and migrations",
      "description": "SQLAlchemy User model with password hashing",
      "effort": "s"
    },
    {
      "title": "Implement login endpoint",
      "description": "POST /auth/login with email/password validation",
      "effort": "s"
    },
    {
      "title": "Implement logout endpoint",
      "description": "POST /auth/logout with token invalidation",
      "effort": "xs"
    },
    {
      "title": "Add password reset flow",
      "description": "Email-based password reset with secure tokens",
      "effort": "m"
    }
  ],
  "dependencies": [[2, 0], [2, 1], [3, 2], [4, 1]],
  "reasoning": "The task is broken down following the natural implementation order..."
}
```

---

## Chat

### POST /api/chat

Invia un messaggio all'agent e ricevi una risposta con azione.

**Request Body**

| Campo | Tipo | Required | Descrizione |
|-------|------|----------|-------------|
| `message` | string | Si | Messaggio dell'utente |
| `context` | object | No | Contesto corrente del board |

**Request Example**

```json
{
  "message": "Crea un ticket per aggiungere dark mode",
  "context": {
    "tickets": [
      {"id": "1", "title": "Fix login bug", "status": "in_progress"}
    ],
    "current_view": "board"
  }
}
```

**Response**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `action` | string | Azione da eseguire |
| `params` | object | Parametri per l'azione |
| `response` | string | Risposta in linguaggio naturale |

**Actions Disponibili**

| Action | Descrizione | Params |
|--------|-------------|--------|
| `create` | Crea ticket | `{title, description?, labels?}` |
| `update` | Modifica ticket | `{ticket_id, ...changes}` |
| `move` | Sposta ticket | `{ticket_id, column}` |
| `search` | Cerca ticket | `{query}` |
| `summarize` | Genera summary | `{}` |
| `decompose` | Scomponi task | `{ticket_id}` |
| `none` | Solo risposta | `{}` |

**Response Example**

```json
{
  "action": "create",
  "params": {
    "title": "Add dark mode support",
    "labels": ["feature", "ui"]
  },
  "response": "Ho creato il ticket 'Add dark mode support' con le labels feature e ui."
}
```

---

## Search

### POST /api/search

Ricerca semantica tra i ticket.

**Request Body**

| Campo | Tipo | Required | Default | Descrizione |
|-------|------|----------|---------|-------------|
| `query` | string | Si | - | Query di ricerca |
| `limit` | int | No | 10 | Numero max risultati |

**Request Example**

```json
{
  "query": "problemi di performance database",
  "limit": 5
}
```

**Response**

```json
{
  "results": [
    {
      "id": "ticket123",
      "title": "Optimize slow database queries",
      "description": "Several queries taking >5s",
      "score": 0.92,
      "explanation": "High semantic match for 'performance' and 'database'"
    },
    {
      "id": "ticket456",
      "title": "Add database connection pooling",
      "description": "Improve DB connection management",
      "score": 0.78,
      "explanation": "Related to database optimization"
    }
  ],
  "query": "problemi di performance database"
}
```

---

## Daily Summary

### GET /api/daily-summary

Genera un riepilogo giornaliero personalizzato.

**Response**

```json
{
  "greeting": "Buongiorno! Hai 3 task in progress e una deadline domani.",
  "focus_today": [
    "Completare il fix del bug login (high priority)",
    "Review della PR di autenticazione",
    "Preparare la release v2.0"
  ],
  "blockers": [
    "Il ticket di integrazione API attende documentazione esterna"
  ],
  "quick_wins": [
    "Chiudi 'Update README' - manca solo il merge"
  ]
}
```

---

## Parse Automation Rule

### POST /api/parse-rule

Converte una regola di automazione da linguaggio naturale a formato strutturato.

**Request Body**

| Campo | Tipo | Required | Descrizione |
|-------|------|----------|-------------|
| `natural_language` | string | Si | Regola in linguaggio naturale |
| `board_context` | object | No | Contesto del board |

**Request Example**

```json
{
  "natural_language": "When a ticket is moved to Done, add the 'completed' label",
  "board_context": {
    "columns": ["Backlog", "Todo", "In Progress", "Done"],
    "labels": ["bug", "feature", "completed", "urgent"]
  }
}
```

**Response**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `rule_name` | string | Nome breve della regola |
| `trigger_type` | string | Tipo di trigger |
| `trigger_config` | object | Configurazione trigger |
| `action_type` | string | Tipo di azione |
| `action_config` | object | Configurazione azione |
| `confidence` | float | Confidenza del parsing (0-1) |
| `explanation` | string | Spiegazione |

**Trigger Types**

| Trigger | Descrizione |
|---------|-------------|
| `ticket_created` | Nuovo ticket creato |
| `ticket_moved` | Ticket spostato di colonna |
| `ticket_updated` | Ticket modificato |
| `label_added` | Label aggiunta |
| `label_removed` | Label rimossa |
| `due_date_approaching` | Deadline vicina |
| `priority_changed` | Priority cambiata |

**Action Types**

| Action | Descrizione |
|--------|-------------|
| `move_ticket` | Sposta ticket |
| `set_priority` | Imposta priority |
| `add_label` | Aggiungi label |
| `remove_label` | Rimuovi label |
| `set_due_date` | Imposta deadline |
| `notify` | Invia notifica |
| `auto_triage` | Esegui triage AI |

**Response Example**

```json
{
  "rule_name": "Add completed on done",
  "trigger_type": "ticket_moved",
  "trigger_config": {"column_name": "Done"},
  "action_type": "add_label",
  "action_config": {"label_name": "completed"},
  "confidence": 0.95,
  "explanation": "When a ticket is moved to the Done column, the 'completed' label will be automatically added."
}
```

---

## Judge Ticket Quality

### POST /api/agent/judge

Valuta la qualita di un ticket usando LLM-as-Judge.

**Request Body**

| Campo | Tipo | Required | Descrizione |
|-------|------|----------|-------------|
| `title` | string | Si | Titolo del ticket |
| `description` | string | Si | Descrizione |
| `priority` | string | Si | Priority assegnata |
| `effort` | string | Si | Effort estimate |
| `labels` | string[] | Si | Labels assegnate |

**Response**

```json
{
  "clarity_score": 8,
  "completeness_score": 7,
  "actionability_score": 9,
  "feedback": "Good ticket with clear requirements. Consider adding acceptance criteria.",
  "overall_score": 8.0
}
```

---

## Multi-Hop Analysis

### POST /api/agent/analyze

Analisi approfondita di un ticket con ragionamento multi-hop.

**Request Body**

```json
{
  "title": "Refactor authentication module",
  "description": "The auth module has grown complex and needs restructuring"
}
```

**Response**

```json
{
  "context_summary": "Authentication module requiring architectural review",
  "key_themes": ["security", "code-quality", "maintainability"],
  "patterns": ["Code duplication in auth flows", "Missing error handling"],
  "dependencies": "Affects: login, signup, password-reset, OAuth",
  "insights": "The module has technical debt accumulated over multiple features",
  "recommendations": "1. Extract common auth logic to shared service\n2. Add comprehensive error handling\n3. Write integration tests before refactoring",
  "complexity": "high"
}
```

---

## Statistics

### GET /api/agent/stats

Statistiche aggregate delle chiamate all'agent.

**Query Parameters**

| Param | Tipo | Default | Descrizione |
|-------|------|---------|-------------|
| `period` | string | `day` | `hour`, `day`, `week` |

**Response**

```json
{
  "total_calls": 150,
  "avg_latency_ms": 2340,
  "success_rate": 0.96,
  "total_tokens": 45000,
  "period": "day"
}
```

### GET /api/agent/stats/modules

Statistiche per modulo.

```json
{
  "modules": {
    "triage": {"calls": 80, "avg_latency_ms": 2100, "success_rate": 0.98},
    "decompose": {"calls": 30, "avg_latency_ms": 3500, "success_rate": 0.93},
    "chat": {"calls": 40, "avg_latency_ms": 2000, "success_rate": 0.95}
  },
  "period": "day"
}
```

### GET /api/agent/stats/hourly

Breakdown orario.

```json
{
  "hourly": [
    {"hour": "2024-01-15T10:00:00", "calls": 12, "avg_latency_ms": 2200},
    {"hour": "2024-01-15T11:00:00", "calls": 15, "avg_latency_ms": 2100}
  ],
  "hours_requested": 24
}
```

### GET /api/agent/stats/errors

Errori recenti.

```json
{
  "errors": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "module": "triage",
      "error": "LLM timeout",
      "input_preview": "Fix critical..."
    }
  ],
  "count": 1
}
```

---

## Suggestions

### POST /api/agent/suggestions

Suggerimenti proattivi per migliorare il board.

**Query Parameters**

| Param | Tipo | Default | Descrizione |
|-------|------|---------|-------------|
| `deep` | bool | `false` | Usa LLM per analisi approfondita |

**Request Body**

```json
{
  "columns": [
    {"id": "col1", "name": "Todo"},
    {"id": "col2", "name": "In Progress"},
    {"id": "col3", "name": "Done"}
  ],
  "tickets": [
    {
      "id": "t1",
      "title": "Old task",
      "column_id": "col2",
      "updated_at": "2024-01-01T00:00:00"
    }
  ]
}
```

**Response**

```json
{
  "suggestions": [
    {
      "type": "stale_ticket",
      "message": "Ticket 'Old task' hasn't been updated in 14 days",
      "action": "Review and update or close",
      "priority": "medium",
      "ticket_id": "t1"
    },
    {
      "type": "wip_limit",
      "message": "Column 'In Progress' has too many tickets",
      "action": "Consider moving completed items to Done",
      "priority": "high",
      "column_id": "col2"
    }
  ]
}
```

---

## Error Responses

Tutte le API restituiscono errori nel formato:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Descrizione |
|-------------|-------------|
| 400 | Bad Request - Input non valido |
| 500 | Internal Server Error |
| 504 | Gateway Timeout - Operazione troppo lenta |

## Rate Limiting

Default: 20 richieste/minuto (configurabile via `MAX_REQUESTS_PER_MINUTE`)

## Timeouts

| Endpoint | Timeout |
|----------|---------|
| `/triage` | 12s |
| `/decompose` | 12s |
| `/chat` | 12s |
| `/daily-summary` | 10s |
| `/parse-rule` | 15s |
| `/agent/judge` | 15s |
| `/agent/analyze` | 60s |
