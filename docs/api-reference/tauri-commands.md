# Tauri Commands Reference

I comandi Tauri (IPC) permettono la comunicazione tra il frontend React e il backend Rust.

## Overview

```typescript
import { invoke } from '@tauri-apps/api/core'

// Chiamata di un comando
const result = await invoke<ResultType>('command_name', { arg1: value1 })
```

---

## Ticket Commands

### create_ticket

Crea un nuovo ticket.

```typescript
interface CreateTicketRequest {
  title: string
  description?: string
  column_id: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  labels?: string[]
  effort?: 'xs' | 's' | 'm' | 'l' | 'xl'
  due_date?: string  // ISO 8601
}

interface Ticket {
  id: string
  title: string
  description: string | null
  status: string
  priority: string
  labels: string[]
  effort: string | null
  column_id: string
  position: number
  created_at: string
  updated_at: string
  due_date: string | null
}

// Usage
const ticket = await invoke<Ticket>('create_ticket', {
  data: {
    title: 'Fix login bug',
    description: 'Users cannot login on Safari',
    column_id: 'col_todo',
    priority: 'high',
    labels: ['bug', 'auth']
  }
})
```

### get_tickets

Recupera tutti i ticket.

```typescript
const tickets = await invoke<Ticket[]>('get_tickets')
```

### get_ticket

Recupera un singolo ticket.

```typescript
const ticket = await invoke<Ticket>('get_ticket', { id: 'ticket_123' })
```

### update_ticket

Aggiorna un ticket esistente.

```typescript
interface UpdateTicketRequest {
  title?: string
  description?: string
  priority?: string
  labels?: string[]
  effort?: string
  due_date?: string | null
}

const updated = await invoke<Ticket>('update_ticket', {
  id: 'ticket_123',
  updates: {
    priority: 'critical',
    labels: ['bug', 'urgent']
  }
})
```

### delete_ticket

Elimina un ticket.

```typescript
await invoke('delete_ticket', { id: 'ticket_123' })
```

### move_ticket

Sposta un ticket in una nuova colonna/posizione.

```typescript
interface MoveTicketRequest {
  ticket_id: string
  column_id: string
  position: number
}

await invoke('move_ticket', {
  ticket_id: 'ticket_123',
  column_id: 'col_done',
  position: 0
})
```

---

## Board Commands

### get_board

Recupera la struttura del board.

```typescript
interface Column {
  id: string
  name: string
  position: number
  color: string | null
  wip_limit: number | null
}

interface Board {
  id: string
  name: string
  columns: Column[]
  created_at: string
}

const board = await invoke<Board>('get_board')
```

### create_column

Crea una nuova colonna.

```typescript
interface CreateColumnRequest {
  name: string
  position?: number
  color?: string
  wip_limit?: number
}

const column = await invoke<Column>('create_column', {
  data: {
    name: 'Review',
    position: 2,
    color: '#6366f1'
  }
})
```

### update_column

Aggiorna una colonna.

```typescript
await invoke('update_column', {
  id: 'col_123',
  updates: {
    name: 'Code Review',
    wip_limit: 3
  }
})
```

### delete_column

Elimina una colonna (i ticket vengono spostati).

```typescript
await invoke('delete_column', {
  id: 'col_123',
  move_tickets_to: 'col_backlog'  // Colonna destinazione
})
```

### reorder_columns

Riordina le colonne.

```typescript
await invoke('reorder_columns', {
  order: ['col_1', 'col_2', 'col_3', 'col_4']
})
```

---

## Search Commands

### search_tickets

Ricerca full-text nei ticket.

```typescript
interface SearchOptions {
  query: string
  filters?: {
    status?: string[]
    priority?: string[]
    labels?: string[]
  }
  limit?: number
}

interface SearchResult {
  id: string
  title: string
  description: string
  score: number
}

const results = await invoke<SearchResult[]>('search_tickets', {
  options: {
    query: 'login bug',
    filters: { priority: ['high', 'critical'] },
    limit: 10
  }
})
```

---

## AI Commands

### triage_ticket

Richiede il triage automatico di un ticket.

```typescript
interface TriageResult {
  priority: string
  labels: string[]
  effort: string
  reasoning: string
}

const triage = await invoke<TriageResult>('triage_ticket', {
  ticket_id: 'ticket_123'
})
```

### decompose_ticket

Richiede la decomposizione di un ticket.

```typescript
interface Subtask {
  title: string
  description: string
  effort: string
}

interface DecomposeResult {
  subtasks: Subtask[]
  dependencies: [number, number][]
  reasoning: string
}

const result = await invoke<DecomposeResult>('decompose_ticket', {
  ticket_id: 'ticket_123'
})
```

### chat

Invia un messaggio all'agent AI.

```typescript
interface ChatResult {
  action: string
  params: Record<string, unknown>
  response: string
}

const result = await invoke<ChatResult>('chat', {
  message: 'Crea un ticket per dark mode',
  context: {
    current_view: 'board',
    tickets: [/* ... */]
  }
})
```

### get_daily_summary

Ottiene il summary giornaliero.

```typescript
interface DailySummary {
  greeting: string
  focus_today: string[]
  blockers: string[]
  quick_wins: string[]
}

const summary = await invoke<DailySummary>('get_daily_summary')
```

---

## Label Commands

### get_labels

Recupera tutte le labels usate.

```typescript
interface Label {
  name: string
  color: string
  count: number  // Numero di ticket con questa label
}

const labels = await invoke<Label[]>('get_labels')
```

### create_label

Crea una nuova label.

```typescript
const label = await invoke<Label>('create_label', {
  name: 'urgent',
  color: '#ef4444'
})
```

### delete_label

Elimina una label (rimossa da tutti i ticket).

```typescript
await invoke('delete_label', { name: 'urgent' })
```

---

## Settings Commands

### get_settings

Recupera le impostazioni utente.

```typescript
interface Settings {
  theme: 'light' | 'dark' | 'system'
  auto_triage: boolean
  keyboard_shortcuts: Record<string, string>
  default_view: 'board' | 'list' | 'timeline'
}

const settings = await invoke<Settings>('get_settings')
```

### update_settings

Aggiorna le impostazioni.

```typescript
await invoke('update_settings', {
  settings: {
    theme: 'dark',
    auto_triage: true
  }
})
```

---

## Events

I comandi possono emettere eventi che il frontend puo ascoltare.

### Listen to Events

```typescript
import { listen } from '@tauri-apps/api/event'

// Nuovo ticket creato
const unlisten = await listen<Ticket>('ticket:created', (event) => {
  console.log('New ticket:', event.payload)
})

// Cleanup
unlisten()
```

### Available Events

| Event | Payload | Descrizione |
|-------|---------|-------------|
| `ticket:created` | `Ticket` | Nuovo ticket creato |
| `ticket:updated` | `{id, changes}` | Ticket modificato |
| `ticket:deleted` | `{id}` | Ticket eliminato |
| `ticket:moved` | `{id, from_col, to_col, position}` | Ticket spostato |
| `board:updated` | `Board` | Struttura board cambiata |
| `ai:triage_complete` | `{ticket_id, result}` | Triage completato |
| `ai:error` | `{operation, error}` | Errore AI |

### Emit Events (Rust side)

```rust
// In un comando Rust
use tauri::Manager;

#[tauri::command]
async fn create_ticket(
    app: tauri::AppHandle,
    data: CreateTicketRequest,
) -> Result<Ticket, String> {
    let ticket = // ... create ticket ...

    // Emit event to frontend
    app.emit("ticket:created", &ticket)
        .map_err(|e| e.to_string())?;

    Ok(ticket)
}
```

---

## Error Handling

Tutti i comandi possono restituire errori come stringhe.

```typescript
try {
  const ticket = await invoke<Ticket>('get_ticket', { id: 'invalid' })
} catch (error) {
  // error e una stringa con il messaggio di errore
  console.error('Failed to get ticket:', error)
}
```

### Common Errors

| Errore | Descrizione |
|--------|-------------|
| `"Ticket not found: {id}"` | Ticket non esiste |
| `"Column not found: {id}"` | Colonna non esiste |
| `"Database error: ..."` | Errore SQLite |
| `"Agent error: ..."` | Errore comunicazione con agent |
| `"Invalid input: ..."` | Dati di input non validi |

---

## Best Practices

### 1. Type Safety

Definisci sempre i tipi per request e response:

```typescript
// types/tauri.ts
export interface Ticket { /* ... */ }
export interface Board { /* ... */ }

// In components
const ticket = await invoke<Ticket>('get_ticket', { id })
```

### 2. Error Handling

Wrappa le chiamate in try-catch:

```typescript
async function safeInvoke<T>(
  command: string,
  args?: Record<string, unknown>
): Promise<T | null> {
  try {
    return await invoke<T>(command, args)
  } catch (error) {
    console.error(`Command ${command} failed:`, error)
    toast.error(`Operation failed: ${error}`)
    return null
  }
}
```

### 3. Optimistic Updates

Aggiorna la UI prima della risposta:

```typescript
function updateTicket(id: string, changes: Partial<Ticket>) {
  // 1. Update UI immediately
  store.updateTicket(id, changes)

  // 2. Persist to backend
  invoke('update_ticket', { id, updates: changes })
    .catch((error) => {
      // 3. Rollback on error
      store.rollbackTicket(id)
      toast.error('Update failed')
    })
}
```

### 4. Batching

Raggruppa operazioni multiple:

```typescript
// Instead of multiple calls
for (const ticket of tickets) {
  await invoke('update_ticket', { id: ticket.id, updates })
}

// Use batch command
await invoke('batch_update_tickets', {
  updates: tickets.map(t => ({ id: t.id, ...updates }))
})
```
