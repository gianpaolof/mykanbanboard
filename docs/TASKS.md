# Kanban AI - Task List

> Usa questa lista per tracciare il progresso. Ogni task ha un prompt per Claude Code.

---

## Phase 1: Foundation (MVP)

### 1.1 Setup & Infrastructure

- [ ] **TASK-001**: Inizializzare Tauri app con React + TypeScript
  ```
  Prompt: "Inizializza il progetto Tauri in apps/desktop con React 18, TypeScript, Vite, Tailwind CSS. Configura gli alias @ per gli import."
  ```

- [ ] **TASK-002**: Configurare Tailwind con design tokens
  ```
  Prompt: "Configura Tailwind CSS con i design tokens da docs/UI_DESIGN.md. Crea il file tailwind.config.js con i colori, font, spacing del design system."
  ```

- [ ] **TASK-003**: Installare dipendenze frontend
  ```
  Prompt: "Installa le dipendenze: zustand, @dnd-kit/core, @dnd-kit/sortable, cmdk, framer-motion, lucide-react, clsx, tailwind-merge. Configura i path alias in tsconfig."
  ```

- [ ] **TASK-004**: Setup shadcn/ui
  ```
  Prompt: "Inizializza shadcn/ui con tema dark. Installa i componenti: button, input, select, dialog, dropdown-menu, command, tooltip."
  ```

### 1.2 Database (Rust)

- [x] **TASK-005**: Creare schema SQLite
  ```
  Prompt: "Crea il modulo db.rs in src-tauri/src/ con lo schema SQLite per boards, columns, tickets, labels, comments. Usa rusqlite. Implementa le migrations."
  ```
  > Completato: Schema SQLite in `src-tauri/src/db/schema.sql` con 5 tabelle, 11 indici, constraints e triggers.

- [x] **TASK-006**: Implementare models Rust
  ```
  Prompt: "Crea models.rs con le struct Rust: Board, Column, Ticket, Label, Comment. Deriva Serialize, Deserialize. Aggiungi i tipi enum Priority e Effort."
  ```
  > Completato: `src-tauri/src/models.rs` con tutti i models, enums Priority/Effort, e DTOs per create/update.

- [x] **TASK-007**: Implementare error handling
  ```
  Prompt: "Crea error.rs con AppError enum usando thiserror. Implementa From<rusqlite::Error> e la conversione a tauri::InvokeError."
  ```
  > Completato: `src-tauri/src/error.rs` con AppError enum e conversioni.

### 1.3 Tauri Commands (Rust)

- [x] **TASK-008**: CRUD Boards
  ```
  Prompt: "Crea i Tauri commands in commands.rs: get_board, get_default_board, create_board, update_board. Usa State<Database> per accedere al db."
  ```
  > Completato: `get_default_board` command che crea board e 5 colonne default se non esistono.

- [x] **TASK-009**: CRUD Columns
  ```
  Prompt: "Aggiungi i commands: get_columns, create_column, update_column, delete_column, reorder_columns. Gestisci il position field per l'ordinamento."
  ```
  > Completato: 5 commands per columns con position management.

- [x] **TASK-010**: CRUD Tickets
  ```
  Prompt: "Aggiungi i commands: get_tickets, create_ticket, update_ticket, delete_ticket, move_ticket. Il move_ticket deve aggiornare column_id e position."
  ```
  > Completato: 6 commands per tickets con labels e comments eager loading.

- [x] **TASK-011**: CRUD Labels
  ```
  Prompt: "Aggiungi i commands: get_labels, create_label, update_label, delete_label, add_label_to_ticket, remove_label_from_ticket."
  ```
  > Completato: 6 commands per labels con junction table management.

### 1.4 React Components (UI)

- [ ] **TASK-012**: Creare utility cn()
  ```
  Prompt: "Crea lib/utils.ts con la funzione cn() che usa clsx e tailwind-merge. Aggiungi generateId() e formatRelativeDate()."
  ```

- [ ] **TASK-013**: Creare types TypeScript
  ```
  Prompt: "Crea types/index.ts con le interfacce: Board, Column, Ticket, Label, Comment, Priority, Effort. Aggiungi i tipi Input per create/update."
  ```

- [ ] **TASK-014**: Creare boardStore (Zustand)
  ```
  Prompt: "Crea stores/boardStore.ts con Zustand. State: board, tickets (per column), isLoading, error. Actions: loadBoard, createTicket, updateTicket, deleteTicket, moveTicket."
  ```

- [ ] **TASK-015**: Creare TicketCard component
  ```
  Prompt: "Crea components/kanban/TicketCard.tsx con glassmorphism style. Mostra: priority dot, labels, title, due date, effort. Usa useSortable di dnd-kit. Animazioni con framer-motion."
  ```

- [ ] **TASK-016**: Creare KanbanColumn component
  ```
  Prompt: "Crea components/kanban/KanbanColumn.tsx. Header con color dot, title, count. Lista di TicketCard. useDroppable per drag target. Add ticket button."
  ```

- [ ] **TASK-017**: Creare KanbanBoard component
  ```
  Prompt: "Crea components/kanban/KanbanBoard.tsx. DndContext con sensors. Mappa le colonne. Gestisci onDragStart, onDragOver, onDragEnd. DragOverlay per il card in movimento."
  ```

- [ ] **TASK-018**: Creare TicketModal component
  ```
  Prompt: "Crea components/kanban/TicketModal.tsx. Form per edit ticket: title, description (textarea), priority (select), effort (select), labels, due date. Bottoni AI Triage e Decompose."
  ```

- [ ] **TASK-019**: Creare Sidebar component
  ```
  Prompt: "Crea components/layout/Sidebar.tsx. Logo, workspace name, nav items (Board, List, Timeline), filters (All, My Tickets, Due Soon), labels list. Stile come nel mockup."
  ```

- [ ] **TASK-020**: Creare Header component
  ```
  Prompt: "Crea components/layout/Header.tsx. Board title, search bar con shortcut Cmd+K, view toggle (Board/List/Timeline), AI button, settings button."
  ```

- [ ] **TASK-021**: Creare CommandPalette component
  ```
  Prompt: "Crea components/layout/CommandPalette.tsx usando cmdk. Groups: Actions (new ticket, AI, summary), Navigation (views), Recent tickets. Keyboard shortcuts display."
  ```

- [ ] **TASK-022**: Assemblare App.tsx
  ```
  Prompt: "Crea App.tsx che assembla: Sidebar, Header, KanbanBoard. Carica il board all'avvio con useEffect. Gestisci il CommandPalette con Cmd+K. Aggiungi il layout base con flex."
  ```

### 1.5 Integrazione

- [x] **TASK-023**: Collegare frontend a backend
  ```
  Prompt: "Aggiorna boardStore per usare invoke() di @tauri-apps/api/core. Testa create, read, update, delete ticket. Verifica che il drag & drop persista i cambiamenti."
  ```
  > Completato: `src/lib/tauri.ts` API wrapper + `stores/boardStore.ts` aggiornato con invoke(), optimistic updates, e rollback on error.

- [ ] **TASK-024**: Testare MVP
  ```
  Prompt: "Testa il flusso completo: crea board, aggiungi colonne, crea tickets, drag & drop, edit ticket, delete. Verifica che i dati persistano dopo riavvio app."
  ```

---

## Phase 2: AI Agent

### 2.1 Python Setup

- [x] **TASK-025**: Inizializzare Python project
  ```
  Prompt: "Inizializza services/agent con pyproject.toml (uv). Dipendenze: fastapi, uvicorn, dspy-ai, chromadb, anthropic, pydantic-settings. Crea struttura cartelle."
  ```
  > Completato: `services/agent/pyproject.toml` con tutte le dipendenze, struttura cartelle, Makefile, start.sh.

- [x] **TASK-026**: Creare config.py
  ```
  Prompt: "Crea src/config.py con pydantic-settings. Campi: anthropic_api_key, openai_api_key (optional), default_model, chroma_path, port. Leggi da .env."
  ```
  > Completato: `services/agent/src/config.py` con Settings class e validazione.

- [x] **TASK-027**: Setup DSPy con Claude
  ```
  Prompt: "Crea src/main.py con FastAPI. Setup DSPy con Claude come LM. Funzione setup_dspy() chiamata all'avvio. Endpoint /health per verificare."
  ```
  > Completato: `services/agent/src/main.py` con FastAPI, lifespan, CORS, DSPy setup.

### 2.2 DSPy Modules

- [x] **TASK-028**: Creare TriageModule
  ```
  Prompt: "Crea agent/modules.py con TriageModule. Signature TriageTicket con input (title, description, existing_labels) e output (priority, labels, effort, reasoning). Usa ChainOfThought."
  ```
  > Completato: `services/agent/src/agent/modules.py` con TriageModule e TriageTicket signature.

- [x] **TASK-029**: Creare DecomposeModule
  ```
  Prompt: "Aggiungi DecomposeModule. Input: title, description. Output: subtasks (list of {title, description, effort}), dependencies (list of tuples). Max 7 subtasks."
  ```
  > Completato: DecomposeModule con DecomposeTask signature.

- [x] **TASK-030**: Creare DailySummaryModule
  ```
  Prompt: "Aggiungi DailySummaryModule. Input: in_progress, blocked, due_soon tickets. Output: greeting, focus_today (top 3), blockers, quick_wins."
  ```
  > Completato: DailySummaryModule con DailySummary signature.

- [x] **TASK-031**: Creare ChatModule
  ```
  Prompt: "Aggiungi ChatModule (ActionDecider). Input: message, context. Output: action (create/update/move/search/summarize/none), params, response."
  ```
  > Completato: ActionDeciderModule con ActionDecider signature.

### 2.3 API Endpoints

- [ ] **TASK-032**: Endpoint /api/triage
  ```
  Prompt: "Crea api/routes.py con router. POST /api/triage riceve {ticket_id, title, description}, chiama TriageModule, ritorna {priority, labels, effort, reasoning}."
  ```

- [ ] **TASK-033**: Endpoint /api/decompose
  ```
  Prompt: "Aggiungi POST /api/decompose. Riceve {ticket_id}, carica ticket da DB, chiama DecomposeModule, ritorna {subtasks, dependencies}."
  ```

- [ ] **TASK-034**: Endpoint /api/daily-summary
  ```
  Prompt: "Aggiungi GET /api/daily-summary. Carica tickets, filtra per stato, chiama DailySummaryModule, ritorna summary."
  ```

- [ ] **TASK-035**: Endpoint /api/chat
  ```
  Prompt: "Aggiungi POST /api/chat. Riceve {message, context}. Chiama ChatModule. Se action != 'none', esegui l'azione. Ritorna {action, response}."
  ```

### 2.4 ChromaDB

- [ ] **TASK-036**: Setup ChromaDB
  ```
  Prompt: "Crea db/chroma.py con VectorStore class. Metodi: add_ticket, update_ticket, delete_ticket, search. Collection 'tickets' con cosine similarity."
  ```

- [ ] **TASK-037**: Endpoint /api/search
  ```
  Prompt: "Aggiungi GET /api/search?query=xxx&limit=5. Usa VectorStore.search(), ritorna tickets ordinati per score."
  ```

### 2.5 Integrazione Agent in UI

- [ ] **TASK-038**: Proxy agent in Rust
  ```
  Prompt: "Aggiungi commands Tauri: call_agent_triage, call_agent_decompose, call_agent_chat, call_agent_search. Fanno HTTP request a localhost:8765."
  ```

- [ ] **TASK-039**: Creare AgentChat component
  ```
  Prompt: "Crea components/ai/AgentChat.tsx. Slide-in panel da destra. Lista messaggi (user/assistant). Input con send button. Chiama call_agent_chat."
  ```

- [ ] **TASK-040**: Integrare AI Triage in TicketModal
  ```
  Prompt: "Aggiungi handler per 'AI Triage' button in TicketModal. Chiama call_agent_triage, mostra risultato, permetti di applicare i suggerimenti."
  ```

- [ ] **TASK-041**: Integrare Decompose
  ```
  Prompt: "Aggiungi handler per 'Decompose' button. Chiama call_agent_decompose, mostra subtasks suggeriti, permetti di crearli come tickets."
  ```

- [ ] **TASK-042**: Gestire sidecar Python
  ```
  Prompt: "Crea sidecar.rs per gestire il processo Python. Start all'avvio di Tauri, stop alla chiusura. Health check per verificare che sia ready."
  ```

---

## Phase 3: Polish

- [ ] **TASK-043**: Animazioni polish
- [ ] **TASK-044**: Keyboard shortcuts completi
- [ ] **TASK-045**: Empty states e loading
- [ ] **TASK-046**: Error handling UI
- [ ] **TASK-047**: Light mode
- [ ] **TASK-048**: Settings page
- [ ] **TASK-049**: Multiple boards
- [ ] **TASK-050**: Export/Import

---

## Progress Tracker

| Phase | Total | Done | Progress |
|-------|-------|------|----------|
| 1. Foundation | 24 | 8 | 33% |
| 2. AI Agent | 18 | 7 | 39% |
| 3. Polish | 8 | 0 | 0% |
| **Total** | **50** | **15** | **30%** |

---

## Quick Start

### Primo Sprint (Week 1)
Focus: Setup + Database + UI Base

1. TASK-001 - TASK-004 (Setup)
2. TASK-005 - TASK-007 (Database) **DONE**
3. TASK-012 - TASK-014 (Utils, Types, Store)
4. TASK-015 - TASK-017 (Core components)

### Secondo Sprint (Week 2)
Focus: CRUD completo + Integrazione

1. TASK-008 - TASK-011 (Tauri commands) **DONE**
2. TASK-018 - TASK-022 (UI components)
3. TASK-023 - TASK-024 (Integrazione) **TASK-023 DONE**

### Terzo Sprint (Week 3)
Focus: AI Agent

1. TASK-025 - TASK-031 (Python + DSPy) **DONE**
2. TASK-032 - TASK-037 (API endpoints)
3. TASK-038 - TASK-042 (Integrazione UI)
