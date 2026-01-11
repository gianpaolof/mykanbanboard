# Kanban AI - Task List

> Usa questa lista per tracciare il progresso. Ogni task ha un prompt per Claude Code.

---

## Phase 1: Foundation (MVP)

### 1.1 Setup & Infrastructure

- [x] **TASK-001**: Inizializzare Tauri app con React + TypeScript
  > Completato: Progetto esistente con Tauri 2.0, React 18, TypeScript, Vite.

- [x] **TASK-002**: Configurare Tailwind con design tokens
  > Completato: tailwind.config.js con design system glassmorphism.

- [x] **TASK-003**: Installare dipendenze frontend
  > Completato: zustand, @dnd-kit, cmdk, framer-motion, lucide-react installati.

- [x] **TASK-004**: Setup shadcn/ui
  > Completato: shadcn/ui configurato con tema dark.

### 1.2 Database (Rust)

- [x] **TASK-005**: Creare schema SQLite
  > Completato: Schema SQLite in `src-tauri/src/db/schema.sql` con 5 tabelle, 11 indici, constraints e triggers.

- [x] **TASK-006**: Implementare models Rust
  > Completato: `src-tauri/src/models.rs` con tutti i models, enums Priority/Effort, e DTOs per create/update.

- [x] **TASK-007**: Implementare error handling
  > Completato: `src-tauri/src/error.rs` con AppError enum e conversioni.

### 1.3 Tauri Commands (Rust)

- [x] **TASK-008**: CRUD Boards
  > Completato: `get_default_board` command che crea board e 5 colonne default se non esistono.

- [x] **TASK-009**: CRUD Columns
  > Completato: 5 commands per columns con position management.

- [x] **TASK-010**: CRUD Tickets
  > Completato: 6 commands per tickets con labels e comments eager loading.

- [x] **TASK-011**: CRUD Labels
  > Completato: 6 commands per labels con junction table management.

### 1.4 React Components (UI)

- [x] **TASK-012**: Creare utility cn()
  > Completato: `lib/utils.ts` con cn(), generateId(), formatRelativeDate().

- [x] **TASK-013**: Creare types TypeScript
  > Completato: `types/index.ts` con tutte le interfacce.

- [x] **TASK-014**: Creare boardStore (Zustand)
  > Completato: `stores/boardStore.ts` con state e actions.

- [x] **TASK-015**: Creare TicketCard component
  > Completato: `components/kanban/TicketCard.tsx` con glassmorphism e dnd-kit.

- [x] **TASK-016**: Creare KanbanColumn component
  > Completato: `components/kanban/KanbanColumn.tsx`.

- [x] **TASK-017**: Creare KanbanBoard component
  > Completato: `components/kanban/KanbanBoard.tsx` con DndContext.

- [x] **TASK-018**: Creare TicketModal component
  > Completato: `components/kanban/TicketModal.tsx` con form e AI buttons.

- [x] **TASK-019**: Creare Sidebar component
  > Completato: `components/layout/Sidebar.tsx`.

- [x] **TASK-020**: Creare Header component
  > Completato: `components/layout/Header.tsx`.

- [x] **TASK-021**: Creare CommandPalette component
  > Completato: `components/layout/CommandPalette.tsx` con cmdk.

- [x] **TASK-022**: Assemblare App.tsx
  > Completato: `App.tsx` con layout completo.

### 1.5 Integrazione

- [x] **TASK-023**: Collegare frontend a backend
  > Completato: `src/lib/tauri.ts` API wrapper + `stores/boardStore.ts` aggiornato con invoke(), optimistic updates, e rollback on error.

- [x] **TASK-024**: Testare MVP
  > Completato: Testato flusso completo con create/delete ticket, AI chat, triage, decompose. Delete ticket funzionante.

---

## Phase 2: AI Agent

### 2.1 Python Setup

- [x] **TASK-025**: Inizializzare Python project
  > Completato: `services/agent/pyproject.toml` con tutte le dipendenze, struttura cartelle, Makefile, start.sh.

- [x] **TASK-026**: Creare config.py
  > Completato: `services/agent/src/config.py` con Settings class e validazione.

- [x] **TASK-027**: Setup DSPy con Claude
  > Completato: `services/agent/src/main.py` con FastAPI, lifespan, CORS, DSPy setup.

### 2.2 DSPy Modules

- [x] **TASK-028**: Creare TriageModule
  > Completato: `services/agent/src/agent/modules.py` con TriageModule e TriageTicket signature.

- [x] **TASK-029**: Creare DecomposeModule
  > Completato: DecomposeModule con DecomposeTask signature.

- [x] **TASK-030**: Creare DailySummaryModule
  > Completato: DailySummaryModule con DailySummary signature.

- [x] **TASK-031**: Creare ChatModule
  > Completato: ActionDeciderModule con ActionDecider signature.

### 2.3 API Endpoints

- [x] **TASK-032**: Endpoint /api/triage
  > Completato: POST /api/triage in `services/agent/src/api/routes.py`.

- [x] **TASK-033**: Endpoint /api/decompose
  > Completato: POST /api/decompose con parsing subtasks.

- [x] **TASK-034**: Endpoint /api/daily-summary
  > Completato: GET /api/daily-summary.

- [x] **TASK-035**: Endpoint /api/chat
  > Completato: POST /api/chat con ActionDecider.

### 2.4 ChromaDB

- [x] **TASK-036**: Setup ChromaDB
  > Completato: `services/agent/src/db/chroma.py` con VectorStore class.

- [x] **TASK-037**: Endpoint /api/search
  > Completato: POST /api/search in routes.py.

### 2.5 Integrazione Agent in UI

- [x] **TASK-038**: Proxy agent in Rust
  > Completato: `src-tauri/src/agent.rs` con 6 commands (agent_triage, agent_decompose, agent_chat, agent_daily_summary, agent_search, agent_health).

- [x] **TASK-039**: Creare AgentChat component
  > Completato: `components/ai/AgentChat.tsx` slide-in panel con messaggi, typing indicator, actions display.

- [x] **TASK-040**: Integrare AI Triage in TicketModal
  > Completato: TicketModal aggiornato con handleAITriage, risultati panel, e apply suggestions.

- [x] **TASK-041**: Integrare Decompose
  > Completato: TicketModal aggiornato con handleDecompose, subtasks selection, e create subtasks.

- [x] **TASK-042**: Gestire sidecar Python
  > Completato: Sidecar management in lib.rs con auto-start, health check, e cleanup on exit.

---

## Phase 3: Polish

- [x] **TASK-043**: Animazioni polish
  > Completato: Creato lib/animations.ts con configurazioni Framer Motion riusabili (spring, fade, stagger, modal, card variants).

- [x] **TASK-044**: Keyboard shortcuts completi
  > Completato: Integrato useKanbanShortcuts hook in App.tsx con tutti gli shortcuts (⌘K, ⌘N, ⌘⇧A, ⌘1-3, ⌘/, ⌘⇧S).

- [x] **TASK-045**: Empty states e loading
  > Completato: EmptyColumn per colonne vuote, BoardSkeleton per loading state animato.

- [x] **TASK-046**: Error handling UI
  > Completato: Integrato sonner toast, aggiunto toast.error/success a tutte le operazioni in boardStore.
- [x] **TASK-047**: Light mode
  > Completato: themeStore con Zustand persist, CSS variables per light/dark, ThemeToggle component, darkMode:'class' Tailwind strategy.

- [x] **TASK-048**: Settings page
  > Completato: SettingsModal con tab Appearance/AI/Shortcuts, settingsStore, AppearanceSettings, AISettings, KeyboardShortcutsSettings.

- [x] **TASK-049**: Multiple boards
  > Completato: BoardListItem/BoardCreate/BoardUpdate types, boardStore multi-board con persist, CreateBoardModal, BoardItem, BoardContextMenu, Sidebar boards section.

- [x] **TASK-050**: Export/Import
  > Completato: export-import.ts lib con validation, DataManagementSettings component, Data tab in Settings con export/import JSON.

### 3.2 Performance & Stability

- [x] **TASK-051**: Debug & Fix Freezing
  > Completato: Timeout 15s su AgentChat con cancellation, Rust timeout ridotto a 15s, Python agent timeout wrapper 12s per DSPy calls.

- [x] **TASK-052**: Performance Optimization
  > Completato: React.memo su TicketCard, KanbanColumn, KanbanBoard, TicketModal. useMemo/useCallback per handlers e computed values.

---

## Progress Tracker

| Phase | Total | Done | Progress |
|-------|-------|------|----------|
| 1. Foundation | 24 | 24 | 100% |
| 2. AI Agent | 18 | 18 | 100% |
| 3. Polish | 10 | 10 | 100% |
| **Total** | **52** | **52** | **100%** |

---

## Quick Start

### Come lanciare l'app

```bash
# Terminal 1: Desktop app
cd apps/desktop
pnpm tauri dev

# Terminal 2: Python agent (opzionale, si avvia automaticamente)
cd services/agent
cp .env.example .env  # Aggiungi ANTHROPIC_API_KEY
./start.sh
```

### Task Completati per Sprint

**Sprint 1 (Setup + Database + UI Base)**: DONE
- TASK-001 - TASK-004 (Setup)
- TASK-005 - TASK-007 (Database)
- TASK-012 - TASK-014 (Utils, Types, Store)
- TASK-015 - TASK-017 (Core components)

**Sprint 2 (CRUD + Integrazione)**: DONE
- TASK-008 - TASK-011 (Tauri commands)
- TASK-018 - TASK-022 (UI components)
- TASK-023 (Integrazione frontend-backend)

**Sprint 3 (AI Agent)**: DONE
- TASK-025 - TASK-031 (Python + DSPy)
- TASK-032 - TASK-037 (API endpoints)
- TASK-038 - TASK-042 (Integrazione UI)

**Rimanenti**: TASK-024 (testing), TASK-043 - TASK-050 (polish)
