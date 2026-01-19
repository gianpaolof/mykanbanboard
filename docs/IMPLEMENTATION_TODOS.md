# Smart Context System - Implementation TODOs

Questo documento contiene le TODO list dettagliate per l'implementazione del Smart Context System.

**Totale Tasks: ~253**

---

## Ordine di Esecuzione Consigliato

```
CRITICHE (Blockers - Fare Prima):
┌─────────────────────────────────────┐
│ FASE 1 + FASE 2 (in parallelo)      │
│ • Python Foundation                  │
│ • Fix Critical Bugs                  │
└───────────────┬─────────────────────┘
                ↓
CORE FEATURES:
┌─────────────────────────────────────┐
│ FASE 3 + FASE 6 (in parallelo)      │
│ • Context-Aware Modules              │
│ • ChromaDB Sync                      │
└───────────────┬─────────────────────┘
                ↓
USER EXPERIENCE:
┌─────────────────────────────────────┐
│ FASE 4 → FASE 5 (sequenziali)       │
│ • Rust Backend per project context   │
│ • React Frontend UI                  │
└───────────────┬─────────────────────┘
                ↓
OPTIMIZATION (Post-MVP):
┌─────────────────────────────────────┐
│ FASE 7                               │
│ • Feedback Loop                      │
│ • DSPy Optimization                  │
│ • A/B Testing                        │
└─────────────────────────────────────┘
```

---

## FASE 1: Python Foundation (44 tasks)

**Priority: CRITICAL**
**Files Critici:** `context_types.py`, `context_manager.py`, `retriever.py`

### 1.1 context_types.py

File: `/services/agent/src/agent/context_types.py`

- [ ] **1.1.1** Create `ContextLayer` enum: `GLOBAL`, `FEATURE`, `RELATED`, `CURRENT`
- [ ] **1.1.2** Create `TokenBudget` dataclass:
  - `total_budget: int = 4000`
  - `reserved_for_response: int = 1000`
  - `layer_budgets: dict[ContextLayer, float]` (15%, 20%, 35%, 30%)
  - `available` property
  - `get_layer_budget(layer)` method
- [ ] **1.1.3** Create `LabelConvention` dataclass: `name`, `description`, `when_to_use`
- [ ] **1.1.4** Create `PriorityRule` dataclass: `condition`, `priority`, `reasoning`
- [ ] **1.1.5** Create `GlobalContext` dataclass with `to_text()` method
- [ ] **1.1.6** Create `FeatureContext` dataclass with `to_text()` method
- [ ] **1.1.7** Create `RelatedTicket` dataclass
- [ ] **1.1.8** Create `RelatedContext` dataclass with `to_text()` method
- [ ] **1.1.9** Create `CurrentTicketContext` dataclass with `to_text()` method
- [ ] **1.1.10** Create `AssembledContext` dataclass with `to_full_text()` method

### 1.2 context_manager.py

File: `/services/agent/src/agent/context_manager.py`

- [ ] **1.2.1** Define `DOMAIN_KEYWORDS` dict (8 domains: auth, ui, api, database, hardware, performance, security, testing)
- [ ] **1.2.2** Implement `detect_domain(title, description) -> Optional[str]`
- [ ] **1.2.3** Create `ContextManager` class with caches
- [ ] **1.2.4** Implement `assemble_context()` method
- [ ] **1.2.5** Implement `_get_global_context(project_context)` method
- [ ] **1.2.6** Implement `_get_feature_context(domain)` method with caching
- [ ] **1.2.7** Implement `_get_related_context(query, exclude_id)` via ChromaDB
- [ ] **1.2.8** Implement `_calculate_token_counts()` with budget redistribution

### 1.3 retriever.py

File: `/services/agent/src/agent/retriever.py`

- [ ] **1.3.1** Import dspy.Retrieve and ChromaManager
- [ ] **1.3.2** Create `ChromaRetriever(dspy.Retrieve)` class
- [ ] **1.3.3** Implement `forward(query, k)` method
- [ ] **1.3.4** Implement `retrieve_with_metadata(query, k)` method
- [ ] **1.3.5** Implement `retrieve_by_labels(labels, k)` method
- [ ] **1.3.6** Add `from_default()` factory method

### 1.4 Tests

- [ ] **1.4.1** Test TokenBudget calculations
- [ ] **1.4.2** Test LabelConvention/PriorityRule instantiation
- [ ] **1.4.3** Test GlobalContext.to_text() with truncation
- [ ] **1.4.4** Test FeatureContext.to_text()
- [ ] **1.4.5** Test RelatedContext.to_text() with empty/full lists
- [ ] **1.4.6** Test CurrentTicketContext.to_text()
- [ ] **1.4.7** Test AssembledContext.to_full_text()
- [ ] **1.4.8** Test detect_domain() for all 8 domains
- [ ] **1.4.9** Test ContextManager._get_global_context()
- [ ] **1.4.10** Test ContextManager._get_feature_context() caching
- [ ] **1.4.11** Test ContextManager._get_related_context() with mock ChromaDB
- [ ] **1.4.12** Test ChromaRetriever.forward()
- [ ] **1.4.13** Add test fixtures in conftest.py

---

## FASE 2: Fix Bugs (27 tasks)

**Priority: CRITICAL**
**Files Critici:** `routes.py`, `models.py`

### 2.1 Fix MultiHop (routes.py:668)

- [ ] **2.1.1** Import ChromaManager in routes.py
- [ ] **2.1.2** Add ChromaManager dependency to analyze endpoint
- [ ] **2.1.3** Query ChromaDB for similar tickets
- [ ] **2.1.4** Format similar tickets as JSON
- [ ] **2.1.5** Replace hardcoded `similar_tickets="[]"` with real data
- [ ] **2.1.6** Add error handling for ChromaDB failures

### 2.2 Fix DailySummary (routes.py:454-458)

- [ ] **2.2.1** Create `DailySummaryRequest` model in models.py
- [ ] **2.2.2** Change endpoint from GET to POST
- [ ] **2.2.3** Add request parameter to function signature
- [ ] **2.2.4** Import new model in routes.py
- [ ] **2.2.5** Extract ticket titles from request
- [ ] **2.2.6** Pass real data to summary_module
- [ ] **2.2.7** Update docstring

### 2.3 Enable Cache in Routes

- [ ] **2.3.1** Import DSPyCache and dspy_cache instance
- [ ] **2.3.2** Add caching to triage endpoint
- [ ] **2.3.3** Add caching to decompose endpoint
- [ ] **2.3.4** Add caching to chat endpoint (shorter TTL)
- [ ] **2.3.5** Add caching to parse-rule endpoint
- [ ] **2.3.6** Add `/agent/cache-stats` endpoint
- [ ] **2.3.7** Add `/agent/cache-invalidate` endpoint
- [ ] **2.3.8** Skip cache for analyze endpoint (dynamic)
- [ ] **2.3.9** Skip cache for daily-summary endpoint (dynamic)

---

## FASE 3: Context-Aware Modules (35 tasks)

**Priority: HIGH**
**Files Critici:** `context_modules.py`, `dynamic_multihop.py`

### 3.1 context_modules.py

File: `/services/agent/src/agent/context_modules.py`

- [ ] **3.1.1** Create file structure
- [ ] **3.1.2** Define `ContextAwareTriageSignature` with all input/output fields
- [ ] **3.1.3** Implement `ContextAwareTriageModule` with ContextManager
- [ ] **3.1.4** Define `ContextAwareDecomposeSignature`
- [ ] **3.1.5** Implement `ContextAwareDecomposeModule`
- [ ] **3.1.6** Add DSPy assertions and suggestions
- [ ] **3.1.7** Add domain detection helper
- [ ] **3.1.8** Export modules in `__init__.py`

### 3.2 dynamic_multihop.py

File: `/services/agent/src/agent/dynamic_multihop.py`

- [ ] **3.2.1** Create file structure
- [ ] **3.2.2** Define Hop 1 Signature: `DynamicContextGathering`
- [ ] **3.2.3** Define Hop 2 Signature: `DynamicDeepAnalysis`
- [ ] **3.2.4** Define Hop 3 Signature: `DynamicInsightGeneration`
- [ ] **3.2.5** Implement `DynamicMultiHopAnalyzer` class
- [ ] **3.2.6** Implement `forward()` with dynamic retrieval between hops
- [ ] **3.2.7** Implement `_execute_queries()` helper
- [ ] **3.2.8** Implement `_aggregate_context()` helper
- [ ] **3.2.9** Add DSPy assertions per hop
- [ ] **3.2.10** Add `analyze(ticket)` convenience method
- [ ] **3.2.11** Export in `__init__.py`

### 3.3 Integrate in routes.py

- [ ] **3.3.1** Import context-aware modules
- [ ] **3.3.2** Add ContextManager dependency injection
- [ ] **3.3.3** Update `/triage` to use ContextAwareTriageModule
- [ ] **3.3.4** Update `/decompose` to use ContextAwareDecomposeModule
- [ ] **3.3.5** Update `/agent/analyze` to use DynamicMultiHopAnalyzer
- [ ] **3.3.6** Update `/daily-summary` with real ticket data
- [ ] **3.3.7** Update `/chat` with enriched context
- [ ] **3.3.8** Add `/sync-tickets` endpoint
- [ ] **3.3.9** Add context management endpoints
- [ ] **3.3.10** Update models.py with new request types

### 3.4 Testing

- [ ] **3.4.1** Test ContextAwareTriageModule
- [ ] **3.4.2** Test DynamicMultiHopAnalyzer
- [ ] **3.4.3** Integration test: full triage flow
- [ ] **3.4.4** Integration test: full analyze flow

---

## FASE 4: Rust Backend (28 tasks)

**Priority: MEDIUM**
**Files Critici:** `models.rs`, `commands.rs`, `agent.rs`

### 4.1 Database Migration

- [ ] **4.1.1** Design JSON schema for project_context
- [ ] **4.1.2** Add `project_context TEXT` column to boards table
- [ ] **4.1.3** Add `description TEXT` column to boards table
- [ ] **4.1.4** Handle migration for existing data (ALTER TABLE)

### 4.2 Models + Commands

- [ ] **4.2.1** Create `LabelConvention` struct
- [ ] **4.2.2** Create `PriorityRule` struct
- [ ] **4.2.3** Create `ProjectContext` struct
- [ ] **4.2.4** Create `UpdateProjectContext` DTO
- [ ] **4.2.5** Update `Board` struct with new fields
- [ ] **4.2.6** Update `BoardListItem` if needed
- [ ] **4.2.7** Update `get_board` command to parse JSON
- [ ] **4.2.8** Update `create_board` command
- [ ] **4.2.9** Update `update_board` command
- [ ] **4.2.10** Create `get_project_context` command
- [ ] **4.2.11** Create `set_project_context` command
- [ ] **4.2.12** Create `update_project_context` command
- [ ] **4.2.13** Create `clear_project_context` command
- [ ] **4.2.14** Register commands in lib.rs

### 4.3 Pass Context in HTTP Calls

- [ ] **4.3.1** Update `TriageRequest` struct with project_context
- [ ] **4.3.2** Update `DecomposeRequest` struct
- [ ] **4.3.3** Create `DailySummaryRequest` struct (POST)
- [ ] **4.3.4** Create `TicketSummary` helper struct
- [ ] **4.3.5** Update `agent_triage` command signature
- [ ] **4.3.6** Update `agent_decompose` command signature
- [ ] **4.3.7** Update `agent_daily_summary` to POST
- [ ] **4.3.8** Create `agent_index_ticket` command

---

## FASE 5: React Frontend (45 tasks)

**Priority: MEDIUM**
**Files Critici:** `projectStore.ts`, `ProjectSettings.tsx`, `ProjectWizard.tsx`

### 5.1 Types + Store

- [ ] **5.1.1** Create `types/project.ts` with interfaces
- [ ] **5.1.2** Create `ProjectContext` interface
- [ ] **5.1.3** Create `ProjectContextCreate` and `ProjectContextUpdate` types
- [ ] **5.1.4** Add `DEFAULT_PROJECT_CONTEXT` constant
- [ ] **5.1.5** Export from `types/index.ts`
- [ ] **5.1.6** Create `stores/projectStore.ts` with persist middleware
- [ ] **5.1.7** Define `ProjectState` interface
- [ ] **5.1.8** Implement core actions (load, save, reset)
- [ ] **5.1.9** Implement field update actions
- [ ] **5.1.10** Implement label convention actions
- [ ] **5.1.11** Implement priority rule actions
- [ ] **5.1.12** Add selectors

### 5.2 Settings UI

- [ ] **5.2.1** Create `ProjectSettings.tsx` main component
- [ ] **5.2.2** Implement settings sections
- [ ] **5.2.3** Create `components/settings/project/` directory
- [ ] **5.2.4** Create `TechStackInput.tsx` with autocomplete
- [ ] **5.2.5** Add tech suggestions and category badges
- [ ] **5.2.6** Create `ModulesList.tsx` component
- [ ] **5.2.7** Add module CRUD and reordering
- [ ] **5.2.8** Create `LabelConventions.tsx` component
- [ ] **5.2.9** Add label convention editing
- [ ] **5.2.10** Create `PriorityRules.tsx` component
- [ ] **5.2.11** Add rule ordering
- [ ] **5.2.12** Create `ContextPreview.tsx` with token estimation
- [ ] **5.2.13** Add "Copy as Text" button
- [ ] **5.2.14** Add "Project" tab to SettingsModal

### 5.3 Wizard

- [ ] **5.3.1** Create `ProjectWizard.tsx` container
- [ ] **5.3.2** Implement 3-step state management
- [ ] **5.3.3** Add step progress indicator
- [ ] **5.3.4** Implement navigation buttons
- [ ] **5.3.5** Create `WizardStep1.tsx` (Project Info)
- [ ] **5.3.6** Add validation for step 1
- [ ] **5.3.7** Create `WizardStep2.tsx` (Tech Stack)
- [ ] **5.3.8** Add quick-select presets
- [ ] **5.3.9** Create `WizardStep3.tsx` (Conventions)
- [ ] **5.3.10** Add simplified setup with templates
- [ ] **5.3.11** Add auto-open on first load
- [ ] **5.3.12** Handle wizard completion
- [ ] **5.3.13** Handle "Skip Setup"

### 5.4 Integration

- [ ] **5.4.1** Add project context API to `tauri.ts`
- [ ] **5.4.2** Update `agentApi.triage` with context
- [ ] **5.4.3** Update `agentApi.decompose` with context
- [ ] **5.4.4** Update `agentApi.chat` with context
- [ ] **5.4.5** Add `api.project` to unified API
- [ ] **5.4.6** Update `boardStore.addTicket` to pass context
- [ ] **5.4.7** Add context loading on board switch
- [ ] **5.4.8** Update `AgentChat.tsx` with context
- [ ] **5.4.9** Update `CreateTicketModal.tsx` for auto-triage
- [ ] **5.4.10** Create `ProjectContextBadge.tsx` indicator
- [ ] **5.4.11** Add badge to Header

---

## FASE 6: ChromaDB Sync (22 tasks)

**Priority: HIGH**
**Files Critici:** `routes.py`, `commands.rs`, `chroma.py`

### 6.1 Index Endpoint (Python)

- [ ] **6.1.1** Create `IndexTicketRequest` model
- [ ] **6.1.2** Create `IndexTicketResponse` model
- [ ] **6.1.3** Implement `POST /api/index-ticket` endpoint
- [ ] **6.1.4** Create `DeleteTicketRequest` model
- [ ] **6.1.5** Implement `DELETE /api/index-ticket/{ticket_id}` endpoint
- [ ] **6.1.6** Add unit tests for index endpoint

### 6.2 Rust Sync

- [ ] **6.2.1** Create `IndexTicketRequest` struct in Rust
- [ ] **6.2.2** Create `index_ticket_async()` fire-and-forget function
- [ ] **6.2.3** Modify `create_ticket` to trigger indexing
- [ ] **6.2.4** Modify `update_ticket` to trigger re-indexing
- [ ] **6.2.5** Modify `delete_ticket` to remove from index
- [ ] **6.2.6** Add metadata extraction helper
- [ ] **6.2.7** Handle agent unavailability gracefully

### 6.3 Bulk Reindex

- [ ] **6.3.1** Create `BulkReindexRequest` model
- [ ] **6.3.2** Create `BulkReindexResponse` model
- [ ] **6.3.3** Implement `POST /api/reindex-all` endpoint
- [ ] **6.3.4** Add `add_tickets_batch()` to ChromaManager
- [ ] **6.3.5** Create Rust `reindex_all_tickets` command
- [ ] **6.3.6** Add function to fetch all tickets for reindex
- [ ] **6.3.7** Add frontend trigger in `tauri.ts`
- [ ] **6.3.8** Add progress feedback (optional)
- [ ] **6.3.9** Add CLI command (optional)

---

## FASE 7: DSPy Optimization & Feedback Loop (52 tasks)

**Priority: LOW (Post-MVP)**
**Files Critici:** `metrics.py`, `optimizer.py`, `FeedbackButtons.tsx`

### 7.1 Database Schema

- [ ] **7.1.1** Create `feedback_schema.sql` migration
- [ ] **7.1.2** Create `FeedbackDB` class
- [ ] **7.1.3** Add initialization to app startup

### 7.2 API Endpoints

- [ ] **7.2.1** Create feedback Pydantic models
- [ ] **7.2.2** Create `feedback_routes.py`
- [ ] **7.2.3** Create `calculate_edit_distance()` utility
- [ ] **7.2.4** Register router in main.py
- [ ] **7.2.5** Export models from api/__init__.py

### 7.3 React Components

- [ ] **7.3.1** Create TypeScript types for feedback
- [ ] **7.3.2** Add feedback API methods to tauri.ts
- [ ] **7.3.3** Add Rust command for feedback submission
- [ ] **7.3.4** Create `FeedbackButtons.tsx` component
- [ ] **7.3.5** Integrate into TicketAnalysisPanel
- [ ] **7.3.6** Integrate into AgentChat
- [ ] **7.3.7** Create `FeedbackStatsWidget.tsx`
- [ ] **7.3.8** Integrate into AgentStatsPanel

### 7.4 Metrics

- [ ] **7.4.1** Create `metrics.py` module
- [ ] **7.4.2** Implement `triage_metric()` (40% priority, 40% labels, 20% effort)
- [ ] **7.4.3** Implement `decompose_metric()` (30% count, 40% similarity, 30% judge)
- [ ] **7.4.4** Implement `chat_metric()` (50% relevance, 50% action)
- [ ] **7.4.5** Implement `daily_summary_metric()`
- [ ] **7.4.6** Implement `rule_parser_metric()`
- [ ] **7.4.7** Create helper functions (title_similarity, embedding_similarity)

### 7.5 Optimizer

- [ ] **7.5.1** Create `optimizer.py` module
- [ ] **7.5.2** Implement `ModuleOptimizer` class
- [ ] **7.5.3** Implement `get_training_data()` method
- [ ] **7.5.4** Implement `optimize()` method with adaptive optimizer selection
- [ ] **7.5.5** Implement `_evaluate()` method
- [ ] **7.5.6** Create `prompts/` directory structure

### 7.6 A/B Testing

- [ ] **7.6.1** Create `ab_testing.py` module
- [ ] **7.6.2** Define `PromptVariant` dataclass
- [ ] **7.6.3** Implement `ABTestManager` class
- [ ] **7.6.4** Implement variant selection logic
- [ ] **7.6.5** Implement promotion decision logic
- [ ] **7.6.6** Integrate A/B testing into routes.py
- [ ] **7.6.7** Add A/B stats endpoint

### 7.7 CLI

- [ ] **7.7.1** Create `cli.py` module
- [ ] **7.7.2** Implement `optimize` command
- [ ] **7.7.3** Implement `stats` command
- [ ] **7.7.4** Implement `promote` command
- [ ] **7.7.5** Implement `rollback` command
- [ ] **7.7.6** Add CLI entry point to pyproject.toml

### 7.8 Scheduler

- [ ] **7.8.1** Create `scheduler.py` module
- [ ] **7.8.2** Implement nightly optimization job
- [ ] **7.8.3** Implement auto-promotion job
- [ ] **7.8.4** Integrate into main.py startup
- [ ] **7.8.5** Add scheduler configuration
- [ ] **7.8.6** Create optimization_runs table
- [ ] **7.8.7** Add monitoring/alerting

### 7.9 Testing

- [ ] **7.9.1** Test metrics functions
- [ ] **7.9.2** Test feedback_db operations
- [ ] **7.9.3** Test optimizer
- [ ] **7.9.4** Test feedback API
- [ ] **7.9.5** Test FeedbackButtons component

---

## Riepilogo

| Fase | Tasks | Priorità | Dipendenze |
|------|-------|----------|------------|
| 1. Python Foundation | 44 | CRITICAL | Nessuna |
| 2. Fix Bugs | 27 | CRITICAL | Nessuna |
| 3. Context-Aware Modules | 35 | HIGH | Fase 1, 2 |
| 4. Rust Backend | 28 | MEDIUM | Nessuna |
| 5. React Frontend | 45 | MEDIUM | Fase 4 |
| 6. ChromaDB Sync | 22 | HIGH | Fase 1, 2 |
| 7. DSPy Optimization | 52 | LOW | Tutte |
| **TOTALE** | **253** | | |

---

## Come Usare Questo Documento

1. **Copia le sezioni** nel tuo task tracker (GitHub Issues, Linear, etc.)
2. **Assegna le fasi** a sviluppatori diversi per parallelizzazione
3. **Spunta i task** man mano che vengono completati
4. **Aggiorna le dipendenze** se scopri nuovi blockers

---

*Generato da Claude Code per il progetto Kanban AI*
*Ultimo aggiornamento: Gennaio 2026*
