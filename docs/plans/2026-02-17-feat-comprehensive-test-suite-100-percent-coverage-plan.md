---
title: "feat: Comprehensive Test Suite for 100% Logic Coverage"
type: feat
status: active
date: 2026-02-17
---

# Comprehensive Test Suite for 100% Logic Coverage

## Enhancement Summary

**Deepened on:** 2026-02-17
**Research agents used:** 8 parallel specialists (architecture, database integrity, Python code quality, simplicity, Rust testing, async patterns, performance oracle, security sentinel)

### Key Improvements Discovered

1. **Collapse to 3 phases** — 6→3 phases, ~200→120 hours, ~255→178 tests. Removes imaginary scale tests (10k tickets), flaky time-based assertions, and duplicate coverage.
2. **Production bugs to fix first** — BestOfNDecompose has two `forward()` defs (line 266 + 329 in `modules.py`); Python silently uses the second. REQUEST_TIMEOUT_SECS (15s) < CHAT_TIMEOUT (20s) — Rust times out before FastAPI returns.
3. **Correct mocking patterns** — `dspy.utils.DummyLM` (not custom MockPrediction). `chromadb.EphemeralClient()` (not PersistentClient with clear_all). `asyncio_mode = "auto"` (not anyio + asyncio mixed).
4. **Remove Phase 5 (performance)** — p95 latency dominated by LLM API, not your code. 10k tickets is fiction for a local desktop app.
5. **Defer cargo-tarpaulin** — Poor macOS support; `cargo test` suffices. Use llvm-cov if coverage gates needed later.
6. **routes_with_context.py is NOT imported** — Clarify if dead code before writing context tests against it.

### New Security Findings (Fix Immediately)

- `str(e)` in all 500 error handlers leaks internal file paths and stack traces
- `"csp": null` in `tauri.conf.json` — no Content Security Policy
- No `max_length` on `TriageRequest.description` field
- No board isolation in ChromaDB search (all boards share one collection)
- Prompt injection via ticket title/description into DSPy prompts

### Critical Architecture Findings

- `get_chroma_manager()` creates a **new ChromaManager instance per HTTP request** (should be singleton)
- `get_context_manager()` singleton has no `threading.Lock` (race condition on first request)
- `hash(query)` is non-deterministic across processes (breaks cache keys)
- 22 tests in `test_extraction.py` are hollow stubs — they don't call `extract_value()` or `safe_extract()` from production code
- `test_chat_board_context.py` uses `src.api.main` (doesn't exist); needs `src.main`

---

## Overview

Build a comprehensive test suite covering ~85% of business logic for the Kanban AI project's Python AI Agent (FastAPI + DSPy) and Rust Backend (Tauri). This initiative will increase test coverage from ~30% overall to 80%+ across all critical components, adding ~178 high-quality tests (not inflated with hollow stubs).

**Current State:**
- ✅ Python: 119 passing, 28 failing, 11 skipped (~40% coverage estimated)
- ❌ Rust: 0 tests (0% coverage)
- 📦 Test infrastructure partially complete (missing pytest-cov, pytest-asyncio proper config)

**Target State:**
- ✅ Python: 80%+ coverage with all critical paths tested
- ✅ Rust: 65%+ coverage with CRUD, database, and commands tested
- ✅ All integration points validated (Tauri ↔ FastAPI ↔ DSPy ↔ ChromaDB)
- ✅ Edge cases and error paths tested

## Problem Statement

### Critical Gaps (High Risk)

**1. Rust Backend — 0% Coverage (3,143 LOC untested)**
- **Impact:** Data corruption, cascade delete failures, foreign key violations, SQLite deadlocks
- **Risk:** This is the data persistence layer — bugs here cause data loss
- Components: `commands.rs` (1,800 LOC), `db/mod.rs` (120 LOC), `models.rs` (300 LOC), `agent.rs` (600 LOC)

**2. Context System — 0% Coverage (2,048 LOC untested)**
- **Impact:** Token budget overflows, cache poisoning, incorrect context → wrong AI decisions
- Components: `context/manager.py`, `context/builder.py`, `context/layers.py`, `context/cache.py`, `context/token_budget.py`

**3. Analytics & Judge/Suggester — 0% Coverage (736 LOC untested)**
- Components: `agent/analytics.py` (356 LOC), `agent/judge.py` (190 LOC), `agent/suggester.py` (190 LOC)

### Known Issues to Fix During Testing

**Production Bug: BestOfNDecompose.forward() defined twice**
```python
# src/agent/modules.py — LINES 266 AND 329
# Python silently uses the second definition
# First impl (lines 266-327): multi-candidate scoring logic
# Second impl (lines 329-388): single-call with dspy.Assert
# Fix: keep only the correct implementation
```

**Timeout Mismatch (agent.rs:12 vs routes.py:CHAT_TIMEOUT)**
```
REQUEST_TIMEOUT_SECS = 15   # agent.rs
CHAT_TIMEOUT = 20           # Python routes.py
# Rust times out BEFORE FastAPI returns for chat, analyze, and other long ops
# Fix: REQUEST_TIMEOUT_SECS should be max(all Python timeouts) + 5
```

**Per-Request ChromaManager Instantiation (routes.py)**
```python
# get_chroma_manager() creates new ChromaManager on every HTTP request
# Should be a singleton initialized at startup
# Fix: initialize once in main.py lifespan, inject via Depends()
```

**ContextManager Singleton Race Condition (context/manager.py)**
```python
# _context_manager_instance global has no threading.Lock
# Fix: add threading.Lock() around singleton creation
```

**28 Failing Tests**
- `test_chat_board_context.py` imports `src.api.main` (doesn't exist → `src.main`)
- Integration tests failing due to missing mocks
- ChromaDB tests failing on embedding operations

## Proposed Solution — 3 Phases

### Phase 1: Infrastructure + Rust Backend (Week 1-2)
Fix dependencies, resolve bugs, write all Rust tests.

### Phase 2: Python Core (Week 2-3)
Context system, analytics/judge/suggester, API integration tests.

### Phase 3: Edge Cases + Error Paths (Week 3)
Empty states, special characters, LLM failure modes, timeout validation.

**Excluded (per simplicity analysis):**
- Performance benchmarks (LLM latency dominates; 10k tickets is not realistic)
- Thread-safety stress tests (single-user desktop app)
- cargo-tarpaulin (poor macOS support; `cargo test` suffices)

## Technical Approach

### Python Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "9.0"
addopts = [
    "-ra",
    "--strict-markers",
    "-m", "not live_api",
]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
asyncio_default_test_loop_scope = "function"
markers = [
    "live_api: mark test as requiring real LLM API (skipped by default)",
    "integration: mark test as integration test",
    "unit: mark test as unit test",
    "slow: mark test as slow (> 1s)",
]

[tool.coverage.run]
source = ["src"]
branch = true
# Do NOT set core = "sysmon" — doesn't support branch coverage on Python 3.12
omit = [
    "tests/*",
    "**/__pycache__/*",
    "**/conftest.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

### Python Test Organization (Final Layout)

```
tests/
├── conftest.py                      # Typed fixtures + DeterministicLM
├── factories.py                     # Pydantic model factories (NEW)
├── unit/                            # Pure function tests, no I/O
│   ├── test_extraction.py           # REWRITE: call actual extract_value/safe_extract
│   ├── test_labels_extraction.py    # Keep: already tests real extract_labels
│   ├── test_timeout.py              # Keep: tests real run_with_timeout
│   ├── test_validators.py           # Trim: remove vacuous tautology tests
│   └── test_dspy_compat.py          # Keep: tests real _dspy_assert shim
├── modules/                         # DSPy module tests via DeterministicLM
│   ├── test_triage_module.py        # REWRITE: use stub LM, not ChainOfThought patch
│   ├── test_decompose_module.py     # Extend + add BestOfNDecompose test
│   ├── test_daily_summary.py        # NEW
│   ├── test_action_decider.py       # NEW
│   └── test_rule_parser.py          # NEW
├── context/                         # NEW: ContextManager, cache, token budget
│   ├── test_manager.py
│   ├── test_builder.py
│   └── test_context_internals.py    # Merged: cache + token budget (5→3 files)
├── agent/                           # NEW: analytics, judge, suggester
│   ├── test_analytics.py
│   ├── test_judge.py
│   └── test_suggester.py
├── integration/                     # FastAPI endpoint tests, DI chain intact
│   ├── test_triage_api.py           # Fix mock boundary
│   ├── test_decompose_api.py
│   ├── test_chat_api.py
│   ├── test_analyze_api.py
│   ├── test_daily_summary_api.py    # NEW
│   ├── test_parse_rule_api.py       # NEW
│   ├── test_judge_api.py            # NEW
│   └── test_suggestions_api.py      # NEW
├── edge_cases/
│   ├── test_empty_states.py
│   ├── test_boundary_conditions.py  # Replace 10MB test with max_length validator test
│   └── test_special_characters.py
├── regression/
│   └── test_labels_bug.py           # Keep: documents specific production bugs
└── e2e/                             # NEW: live_api marker, CI-gated only
    └── test_live_chat.py            # Replaces test_chat_board_context.py
```

### Conftest.py — Correct Patterns

```python
# tests/conftest.py
from __future__ import annotations
from collections.abc import Generator
from typing import Any
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
import dspy

from src.main import app


# ── App Client ────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ── DSPy Stub LM ──────────────────────────────────────────────────────────────
# Use dspy.utils.DummyLM (built into DSPy 3.x) to stub the LM without API calls

@pytest.fixture(autouse=True)
def reset_dspy_settings() -> Generator[None, None, None]:
    """Reset DSPy global state between tests to prevent cross-test contamination."""
    original = dspy.settings.lm
    yield
    dspy.settings.lm = original


@pytest.fixture
def stub_lm() -> dspy.utils.DummyLM:
    """Configure DSPy with a deterministic stub LM."""
    lm = dspy.utils.DummyLM([
        {"priority": "high", "labels": ["bug", "auth"], "effort_estimate": "m",
         "reasoning": "Stub reasoning for testing."}
    ])
    dspy.configure(lm=lm)
    return lm


# ── Typed Module Mock Fixtures ────────────────────────────────────────────────
# Replace repeated `with patch('src.api.routes.TriageModule') as mock_class: ...`

@pytest.fixture
def mock_triage_module() -> Generator[Mock, None, None]:
    """Inject a mock TriageModule into the route handler."""
    with patch("src.api.routes.TriageModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


@pytest.fixture
def mock_decompose_module() -> Generator[Mock, None, None]:
    with patch("src.api.routes.DecomposeModule") as mock_class:
        instance = Mock()
        mock_class.return_value = instance
        yield instance


# ── ChromaDB Isolation ────────────────────────────────────────────────────────
# Use EphemeralClient: never touches the filesystem, safe for parallel test runs

@pytest.fixture
def isolated_chroma() -> Generator[Any, None, None]:
    """In-memory ChromaDB, no ONNX download, no filesystem side-effects."""
    import chromadb
    from chromadb.utils import embedding_functions
    from src.db.chroma import ChromaManager

    client = chromadb.EphemeralClient()
    manager = ChromaManager.__new__(ChromaManager)
    manager.client = client
    # Use DefaultEmbeddingFunction (no OpenAI key needed)
    manager.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    manager.collection = client.get_or_create_collection(
        name="test_tickets",
        embedding_function=manager.embedding_fn,
    )
    yield manager


# ── Typed Fixture Data ────────────────────────────────────────────────────────

@pytest.fixture
def sample_ticket() -> dict[str, str | list[str]]:
    return {
        "ticket_id": "test-123",
        "title": "Fix login bug on Safari",
        "description": "Users report they cannot login when using Safari browser",
        "existing_labels": ["bug", "auth", "browser"],
    }
```

### factories.py — Pydantic-anchored Fixtures

```python
# tests/factories.py
"""Test data factories anchored to real Pydantic models.
If a required field is added to a model, factories fail at import time — not inside tests."""
from src.api.routes import TriageRequest

def make_triage_request(**overrides) -> dict:
    defaults = TriageRequest(
        ticket_id="test-123",
        title="Fix login bug on Safari",
        description="Users cannot login on Safari",
        existing_labels=["bug", "auth"],
    ).model_dump()
    return {**defaults, **overrides}
```

### DSPy Module Testing Pattern

```python
# tests/modules/test_triage_module.py
# Correct: use DummyLM, not ChainOfThought patch

class TestTriageModule:
    def test_triage_with_valid_inputs(self, stub_lm):
        """Test full forward pass with stub LM — exercises prompt + parsing."""
        module = TriageModule()
        result = module.forward(
            title="Fix login bug",
            description="Users cannot log in on Safari",
            existing_labels=["bug", "auth"],
        )
        assert result.priority in VALID_PRIORITIES
        assert isinstance(result.labels, list)
        assert result.effort_estimate in VALID_EFFORTS

    @pytest.mark.parametrize("effort", ["xs", "s", "m", "l", "xl"])
    def test_valid_effort_estimates(self, stub_lm, effort: str) -> None:
        """Each effort value tested independently — failure shows exact value."""
        # ... (avoids for loop over test cases in single test function)
```

### Integration Test Pattern (Fix Mock Boundary)

```python
# tests/integration/test_triage_api.py
# Correct: mock at module boundary, not class

class TestTriageAPI:
    def test_triage_success(
        self,
        client: TestClient,
        sample_ticket: dict,
        mock_triage_module: Mock,   # Use fixture, not repeated with-patch
    ) -> None:
        mock_triage_module.forward.return_value = Mock(
            priority="high",
            labels=["bug", "auth"],
            effort_estimate="m",
            reasoning="Test reasoning",
        )
        response = client.post("/api/triage", json=sample_ticket)
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "high"
```

### Rust Testing Strategy

**Key decisions from research:**
- `Connection::open_in_memory()` for most unit tests (fast, isolated, no filesystem)
- `tempfile::TempDir` ONLY for v2 migration tests (must test pre-migration schema)
- `httpmock` for mocking HTTP calls to FastAPI from `agent.rs`
- LLVM engine required for cargo-tarpaulin on macOS (not Ptrace)
- Refactor Tauri commands to accept `&rusqlite::Connection` for testability (not `tauri::State`)

**Cargo.toml additions:**
```toml
[dev-dependencies]
tempfile = "3"
tokio = { version = "1", features = ["full", "test-util"] }
httpmock = "0.8"

# For Tauri integration testing only (not needed for unit tests):
# tauri = { version = "2.0", features = ["test"] }
```

**In-memory DB helper (add to db/mod.rs):**
```rust
#[cfg(test)]
pub fn new_in_memory() -> AppResult<Self> {
    let conn = Connection::open_in_memory()?;
    conn.execute_batch("PRAGMA foreign_keys = ON; PRAGMA busy_timeout = 1000;")?;
    let db = Database { conn: Arc::new(Mutex::new(conn)) };
    // Execute schema.sql directly (migrations already in schema for new DBs)
    let schema = include_str!("schema.sql");
    db.conn.lock().unwrap().execute_batch(schema)?;
    Ok(db)
}
```

**Test file organization:**
```
apps/desktop/src-tauri/
├── src/
│   ├── db/mod.rs           # Add #[cfg(test)] mod tests inline
│   ├── models.rs           # Add #[cfg(test)] mod tests inline
│   └── commands.rs         # Add #[cfg(test)] mod tests (after refactor)
└── tests/                  # Integration tests only
    ├── common/mod.rs       # Shared helpers
    ├── db_tests.rs         # Migration + constraint + cascade tests
    ├── commands_tests.rs   # CRUD integration tests
    └── agent_tests.rs      # HTTP client tests (httpmock)
```

## Implementation Phases

### Phase 1: Infrastructure + Rust Backend (Weeks 1-2)
**Target: ~65 tests | Fix production bugs**

#### Task 1.1: Fix Python Test Configuration
**Files:**
- `services/agent/pyproject.toml`

**Changes:**
```bash
cd services/agent
uv add --dev pytest-asyncio>=0.24.0 pytest-cov>=4.0.0 time-machine
```

Update `pyproject.toml` with the configuration from the Technical Approach section above.

**Key fixes:**
- Add `asyncio_mode = "auto"` (replace anyio + asyncio inconsistency)
- Remove `anyio` usages; keep only `pytest-asyncio`
- Add marker registration in `pyproject.toml` (not only in conftest)
- Add `-m "not live_api"` to default addopts

**Acceptance Criteria:**
- [ ] `pytest` runs with no unknown marker warnings
- [ ] All async tests work without `@pytest.mark.asyncio` decorator
- [ ] Coverage reports generated to `htmlcov/`

---

#### Task 1.2: Fix Production Bugs (Pre-Test)
**Files:**
- `services/agent/src/agent/modules.py` — Remove duplicate `forward()` on `BestOfNDecompose`
- `apps/desktop/src-tauri/src/agent.rs` — Fix `REQUEST_TIMEOUT_SECS` to be > all Python timeouts
- `services/agent/tests/test_chat_board_context.py` — Fix `src.api.main` → `src.main`; add `@pytest.mark.live_api`

**Changes:**
```python
# modules.py — Remove the FIRST forward() definition (lines 266-327)
# Keep only the second one (lines 329-388) which has the dspy.Assert constraints
```

```rust
// agent.rs — Fix timeout hierarchy
// const REQUEST_TIMEOUT_SECS: u64 = 15; // WRONG: less than CHAT_TIMEOUT (20s)
const REQUEST_TIMEOUT_SECS: u64 = 65; // max(60s ANALYZE_TIMEOUT) + 5s buffer
```

**Acceptance Criteria:**
- [ ] BestOfNDecompose has exactly one `forward()` method
- [ ] Rust timeout > max FastAPI operation timeout
- [ ] `test_chat_board_context.py` correctly imports from `src.main`
- [ ] Live API tests marked with `@pytest.mark.live_api` and excluded by default

---

#### Task 1.3: Rust In-Memory DB Infrastructure
**Files:**
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/src-tauri/src/db/mod.rs`

**Changes:**
```toml
# Cargo.toml dev-dependencies
[dev-dependencies]
tempfile = "3"
tokio = { version = "1", features = ["full", "test-util"] }
httpmock = "0.8"
```

Add `new_in_memory()` constructor to `Database` struct (see Technical Approach above).

**Acceptance Criteria:**
- [ ] `cargo test` runs with 0 tests (no failures)
- [ ] `Database::new_in_memory()` compiles and creates usable in-memory DB

---

#### Task 1.4: Rust Database Layer Tests
**Files:**
- `apps/desktop/src-tauri/src/db/mod.rs` (add `#[cfg(test)]` module)
- `apps/desktop/src-tauri/tests/db_tests.rs` (new)

**Test cases — 15 tests:**

```rust
// Constraint tests
#[test] fn test_label_name_unique_constraint_enforced()
#[test] fn test_ticket_priority_check_constraint_rejects_invalid_value()
#[test] fn test_automation_rule_trigger_type_check_constraint()
#[test] fn test_ticket_title_not_null_constraint()

// Cascade delete
#[test] fn test_cascade_delete_board_removes_all_descendants()
// Verifies: columns, tickets, comments, subtasks, ticket_labels all gone
// Verifies: labels (independent table) survive

// Migration
#[test] fn test_v2_migration_adds_project_context_column()
// Uses TempDir (not in_memory) — needs pre-migration schema
#[test] fn test_v2_migration_is_idempotent()
#[test] fn test_v2_migration_preserves_existing_rows()

// Triggers
#[test] fn test_update_trigger_advances_boards_updated_at()
#[test] fn test_update_trigger_advances_tickets_updated_at()

// Transaction
#[test] fn test_create_ticket_rolls_back_on_label_failure()
// Verifies savepoint rollback when label FK fails

// General
#[test] fn test_get_or_create_default_board_idempotent()
#[test] fn test_run_migrations_on_fresh_db_succeeds()
#[test] fn test_foreign_key_enforcement_on_ticket_insert()
#[test] fn test_sqlite_does_not_deadlock_on_cascade_delete()
```

**Acceptance Criteria:**
- [ ] 15+ database tests written and passing
- [ ] Cascade delete fully verified (board → column → ticket → comments/subtasks/ticket_labels)
- [ ] Coverage: 90%+ for `db/mod.rs`

---

#### Task 1.5: Rust CRUD Command Tests
**Files:**
- `apps/desktop/src-tauri/tests/commands_tests.rs` (new)

**Prerequisite:** Refactor Tauri commands to accept `&rusqlite::Connection` (thin wrappers), making them unit-testable without the full Tauri runtime.

**Test cases — 30 tests:**

```rust
// Board/Column
#[test] fn test_create_board_returns_board_with_id()
#[test] fn test_create_column_position_auto_increment()
#[test] fn test_cascade_delete_board()
#[test] fn test_reorder_columns_batch_update()

// Tickets
#[test] fn test_create_ticket_with_all_fields()
#[test] fn test_create_ticket_minimal()
#[test] fn test_update_ticket_priority()
#[test] fn test_update_ticket_invalid_priority_rejected()
#[test] fn test_delete_ticket_cascade()  // subtasks + labels removed
#[test] fn test_move_ticket_to_nonexistent_column()  // returns error
#[test] fn test_date_parse_fallback_uses_now()  // unwrap_or_else on parse error

// Labels
#[test] fn test_create_label_with_unique_name()
#[test] fn test_create_duplicate_label_returns_existing()  // UNIQUE handled gracefully
#[test] fn test_add_label_to_ticket()
#[test] fn test_add_duplicate_label_to_ticket_idempotent()
#[test] fn test_remove_label_from_ticket()

// Subtasks
#[test] fn test_create_subtask()
#[test] fn test_toggle_subtask_completed()
#[test] fn test_delete_parent_ticket_removes_subtasks()

// Comments
#[test] fn test_create_comment()
#[test] fn test_delete_ticket_removes_comments()

// Automation
#[test] fn test_create_automation_rule()
#[test] fn test_automation_rule_invalid_trigger_type_rejected()

// Model serialization
#[test] fn test_priority_enum_roundtrip()
#[test] fn test_effort_enum_roundtrip()
#[test] fn test_unknown_priority_deserialization_fallback()
#[test] fn test_project_context_json_roundtrip()
```

**Acceptance Criteria:**
- [ ] 30+ command tests written and passing
- [ ] Coverage: 75%+ for `commands.rs`

---

#### Task 1.6: Rust Agent HTTP Client Tests
**Files:**
- `apps/desktop/src-tauri/tests/agent_tests.rs` (new)

**Test cases — 10 tests using `httpmock`:**

```rust
#[tokio::test]
async fn test_triage_request_success_parses_response()

#[tokio::test]
async fn test_triage_request_timeout_returns_error()
// Mock server delays 65+ seconds, verify error within timeout

#[tokio::test]
async fn test_triage_request_500_returns_agent_error()

#[tokio::test]
async fn test_chat_request_success()

#[tokio::test]
async fn test_sync_tickets_success()

#[tokio::test]
async fn test_network_unreachable_returns_error()

#[tokio::test]
async fn test_health_check_200_returns_ok()

#[tokio::test]
async fn test_health_check_non_200_returns_not_healthy()

#[tokio::test]
async fn test_request_timeout_constant_exceeds_all_python_timeouts()
// Compile-time assertion: REQUEST_TIMEOUT_SECS > CHAT_TIMEOUT (20) + 5
```

**Acceptance Criteria:**
- [ ] 10+ agent client tests written and passing
- [ ] Timeout hierarchy enforced as a test
- [ ] Coverage: 70%+ for `agent.rs`

---

### Phase 2: Python Core Coverage (Weeks 2-3)
**Target: ~80 tests | Context, analytics, API integration**

#### Task 2.1: Rebuild Unit Tests (Delete Hollow Stubs)

**Delete:**
- All 22 tests in `tests/unit/test_extraction.py` — they test inline logic, not production code

**Rewrite `test_extraction.py`** — 20 tests that call actual `extract_value()` and `safe_extract()` from `src.api.routes`:

```python
# tests/unit/test_extraction.py
from src.api.routes import extract_value, safe_extract, extract_labels

class TestExtractValue:
    def test_returns_string_attribute(self) -> None:
        pred = Mock(priority="high")
        assert extract_value(pred, "priority", str) == "high"

    def test_falls_back_to_store_dict_key(self) -> None:
        """DSPy 3.x stores values in _store dict."""
        pred = Mock(spec=[])  # no .priority attribute
        pred._store = {"priority": "medium"}
        assert extract_value(pred, "priority", str) == "medium"

    def test_returns_default_for_missing_attribute(self) -> None:
        pred = Mock(spec=[])
        pred._store = {}
        assert extract_value(pred, "priority", str, default="low") == "low"
```

**Trim `test_validators.py`** — Remove tautological tests (e.g., `assert priority in VALID_PRIORITIES` for each value in `VALID_PRIORITIES`). Add meaningful tests of validation logic.

**Acceptance Criteria:**
- [ ] `test_extraction.py` rewritten — all 20 new tests call production functions
- [ ] No test contains `assert x in VALID_PRIORITIES` as its only assertion

---

#### Task 2.2: Context System Tests
**Files:**
- `services/agent/tests/context/test_manager.py` (new)
- `services/agent/tests/context/test_builder.py` (new)
- `services/agent/tests/context/test_context_internals.py` (new — merges cache + token_budget)

**Before writing:** Verify that `src/context/` is actually imported in `src/main.py` (not in dead `routes_with_context.py`). If `routes_with_context.py` is dead code, delete it before writing tests against the context system.

**Context Manager — 15 tests:**

```python
# tests/context/test_manager.py
@pytest.fixture
def manager(isolated_chroma) -> ContextManager:
    return ContextManager(chroma_manager=isolated_chroma)

class TestContextManager:
    def test_get_triage_context_builds_3_layers(self, manager): ...
    def test_sync_tickets_adds_to_chromadb(self, manager): ...
    def test_sync_tickets_upserts_existing(self, manager): ...
    def test_sync_failure_is_logged_not_raised(self, manager): ...
    def test_cache_invalidation_on_ticket_update(self, manager): ...
    def test_singleton_factory_returns_same_instance(self): ...
    def test_get_triage_context_with_empty_chromadb(self, manager): ...
    # ... more
```

**Context Builder — 10 tests:**

```python
class TestContextBuilder:
    def test_build_triage_context_includes_existing_labels(self, builder): ...
    def test_token_budget_overflow_truncates_relevant_layer(self, builder): ...
    def test_empty_chromadb_returns_global_only(self, builder): ...
    def test_layer_priorities(self, builder): ...
```

**Context Internals (cache + token_budget) — 15 tests:**

```python
# tests/context/test_context_internals.py
class TestContextCache:
    def test_cache_hit_returns_value(self, cache): ...
    def test_cache_miss_returns_none(self, cache): ...
    def test_ttl_expiration(self, cache, time_machine): ...
    # Use time-machine (not freezegun) for async TTL tests

class TestTokenBudgetManager:
    def test_allocate_budget_default_split(self, budget_mgr): ...
    def test_overflow_truncates_relevant_layer_first(self, budget_mgr): ...
    def test_token_count_for_1000_tickets(self, budget_mgr): ...
    # Test truncation with mock list, not real ChromaDB seed
```

**Acceptance Criteria:**
- [ ] 40+ context tests written and passing
- [ ] EphemeralClient used — no filesystem side effects
- [ ] Coverage: 75%+ for `context/`

---

#### Task 2.3: Analytics, Judge, Suggester Tests
**Files:**
- `services/agent/tests/agent/test_analytics.py` (new — 10 tests)
- `services/agent/tests/agent/test_judge.py` (new — 8 tests)
- `services/agent/tests/agent/test_suggester.py` (new — 8 tests)

**Analytics:**
```python
class TestAgentAnalytics:
    def test_log_call_creates_db_entry(self, analytics): ...
    def test_get_stats_aggregates_correctly(self, analytics): ...
    def test_deduplication_by_input_hash(self, analytics): ...
    def test_db_corruption_recovery(self, analytics): ...
    def test_get_module_breakdown(self, analytics): ...
```

**Judge — score validation:**
```python
class TestTicketQualityJudge:
    def test_scores_clamped_to_0_10_range(self, stub_lm): ...
    def test_empty_description_scores_low_completeness(self, stub_lm): ...
    def test_feedback_minimum_length(self, stub_lm): ...
    def test_llm_returns_score_above_10_clamped(self, stub_lm): ...
```

**Suggester — remove `test_circular_suggestions_avoided` (tests LLM judgment, not your code):**
```python
class TestProactiveSuggester:
    def test_suggests_stale_tickets(self, suggester): ...
    def test_max_5_suggestions(self, suggester): ...
    def test_suggestions_sorted_by_priority(self, suggester): ...
    def test_malformed_json_recovery(self, suggester): ...
```

**Acceptance Criteria:**
- [ ] 26+ tests written and passing
- [ ] Coverage: 70%+ for analytics, judge, suggester

---

#### Task 2.4: API Integration Tests for Uncovered Endpoints
**Files:**
- `services/agent/tests/integration/test_daily_summary_api.py` (new)
- `services/agent/tests/integration/test_parse_rule_api.py` (new)
- `services/agent/tests/integration/test_judge_api.py` (new)
- `services/agent/tests/integration/test_suggestions_api.py` (new)

The following 10 endpoints have zero integration tests:
`/api/daily-summary`, `/api/parse-rule`, `/api/agent/judge`, `/api/agent/analyze`,
`/api/agent/stats`, `/api/agent/suggestions`, `/api/sync-tickets`,
`/api/index-ticket`, `/api/context/invalidate-cache`, `/api/context/cache-stats`

**Pattern for all new integration tests (use fixture, not repeated with-patch):**
```python
# tests/integration/test_daily_summary_api.py
class TestDailySummaryAPI:
    def test_daily_summary_success(
        self, client: TestClient, mock_daily_summary_module: Mock
    ) -> None:
        mock_daily_summary_module.forward.return_value = Mock(
            greeting="Good morning!",
            focus_today=["Fix login bug"],
            blockers=[],
            quick_wins=["Update docs"],
        )
        response = client.post("/api/daily-summary", json={
            "in_progress": [{"id": "1", "title": "Fix bug", "priority": "high"}],
            "blocked": [],
            "due_soon": [],
            "recently_completed": [],
        })
        assert response.status_code == 200
```

**Acceptance Criteria:**
- [ ] 20+ new integration tests for previously untested endpoints
- [ ] All use fixture-based mocking (no repeated `with patch()` blocks)

---

### Phase 3: Edge Cases + Error Paths (Week 3)
**Target: ~33 tests | Error paths, edge cases, security validation**

#### Task 3.1: Edge Case Tests
**Files:**
- `services/agent/tests/edge_cases/test_empty_states.py` (new)
- `services/agent/tests/edge_cases/test_boundary_conditions.py` (new)
- `services/agent/tests/edge_cases/test_special_characters.py` (new)

**Key tests — 20 tests:**

```python
# empty_states.py
def test_triage_with_empty_existing_labels(client, mock_triage_module): ...
def test_daily_summary_with_zero_tickets(client, mock_daily_summary_module): ...
def test_search_with_no_chromadb_results(client): ...

# boundary_conditions.py
def test_ticket_with_exactly_3_labels(client, mock_triage_module): ...
# NOT: test_extremely_long_description_10mb
# INSTEAD: test that max_length validator rejects > 10000 chars at the Pydantic level
def test_description_max_length_validated(): ...
def test_title_max_length_validated(): ...

# special_characters.py
def test_sql_injection_in_title_safely_handled(client): ...
def test_emoji_in_description_preserved(client): ...
def test_unicode_in_labels_roundtrip(client): ...
def test_prompt_injection_in_title_sanitized(client): ...  # Security: \n\nIgnore previous
```

---

#### Task 3.2: Error Path Tests
**Files:**
- `services/agent/tests/edge_cases/test_error_paths.py` (new)

**13 tests:**

```python
class TestErrorPaths:
    def test_llm_returns_invalid_enum_falls_back_to_default(
        self, client: TestClient, mock_triage_module: Mock
    ) -> None:
        mock_triage_module.forward.return_value = Mock(
            priority="INVALID",  # Not in VALID_PRIORITIES
            labels=[],
            effort_estimate="m",
            reasoning="test",
        )
        response = client.post("/api/triage", json=make_triage_request())
        # Should not 500 — should fall back to "medium" or return 422
        assert response.status_code in [200, 422]

    def test_timeout_returns_504(self, client): ...
    def test_module_raises_exception_returns_500(self, client, mock_triage_module): ...
    def test_500_error_does_not_leak_stack_trace(self, client, mock_triage_module): ...
    # Security: verify str(e) is NOT in the response body

    def test_triage_missing_required_fields_returns_422(self, client): ...
    def test_chromadb_unreachable_logs_but_continues(self, client): ...
```

---

#### Task 3.3: ChromaDB Data Integrity Tests
**Files:**
- `services/agent/tests/integration/test_chroma_integrity.py` (new)

**10 tests using isolated_chroma fixture:**

```python
class TestChromaIntegrity:
    def test_ghost_ticket_not_in_search_after_delete(self, isolated_chroma): ...
    # Critical: ticket deleted from SQLite should also be removed from ChromaDB

    def test_upsert_preserves_document_count(self, isolated_chroma): ...
    def test_clear_all_collection_remains_usable(self, isolated_chroma): ...
    def test_metadata_fields_match_sqlite_schema(self, isolated_chroma): ...
    def test_search_returns_correct_result_structure(self, isolated_chroma): ...
    def test_get_stats_reflects_actual_document_count(self, isolated_chroma): ...
```

---

## Revised Test Count

| Component | Current | New Tests | Target Coverage |
|-----------|---------|-----------|-----------------|
| Rust Database | 0 | 15 | 90% `db/mod.rs` |
| Rust Commands | 0 | 30 | 75% `commands.rs` |
| Rust Agent Client | 0 | 10 | 70% `agent.rs` |
| Python Unit (rebuilt) | 88 → keep ~45 useful | 20 new | 80% extraction/validators |
| DSPy Modules | 19 (patched wrong) | 25 new | 80% modules |
| Context System | 0 | 40 | 75% context/ |
| Analytics/Judge/Suggester | 0 | 26 | 70% each |
| API Integration (new endpoints) | 26 | 20 new | 85% routes |
| Edge Cases + Error Paths | 0 | 33 | N/A |
| **TOTAL NEW** | — | **~178** | **80%+ overall** |

**Excluded (YAGNI):**
- Performance benchmarks (Phase 5 removed)
- Thread-safety stress tests (single-user desktop app)
- cargo-tarpaulin CI gate (defer; use `cargo test`)
- 10MB description test (replace with `max_length` validator test)
- E2E 1000-ticket fixture seeding (replace with `TokenBudgetManager` unit test)

## Quality Gates

**Before Merge:**
- [ ] All tests pass (0 failures)
- [ ] `pytest --cov=src --cov-fail-under=80`
- [ ] `cargo test` — all Rust tests pass
- [ ] No DSPy version conflicts (only one dspy package installed)
- [ ] No `@pytest.mark.skip` without a clear reason comment

**Not Required (yet):**
- cargo-tarpaulin coverage gate (poor macOS support; add later with llvm-cov)
- Performance benchmarks
- Thread-safety stress tests

## Dependencies

**Python:**
```bash
uv add --dev pytest-asyncio>=0.24.0 pytest-cov>=4.0.0 time-machine
```

**Rust (Cargo.toml dev-dependencies):**
```toml
tempfile = "3"
tokio = { version = "1", features = ["full", "test-util"] }
httpmock = "0.8"
```

## Risks & Mitigation

**Risk 1: routes_with_context.py is dead code**
- Check `src/main.py` imports before writing context tests
- If dead: delete it (697 LOC), then write tests for `src/api/routes.py` context path

**Risk 2: ChromaDB DefaultEmbeddingFunction downloads ONNX model (79MB)**
- Use `EphemeralClient` with explicit `embeddings=` parameter
- Or use `DeterministicEmbeddingFunction` (char frequency, no downloads)

**Risk 3: Rust command tests require DI refactor**
- Commands using `tauri::State<Database>` cannot be unit-tested without Tauri runtime
- Refactor to extract `impl Database { fn create_ticket(...) }` called from the Tauri command

**Risk 4: Fixing bugs may cause temporary test failures**
- Fix production bugs (Task 1.2) before running full test suite
- Track bug fixes as separate commits

## References

### Internal Documentation
- [Testing Guide](../development/testing.md)
- [Agent Design](../AGENT_DESIGN.md)
- [DSPy Labels Bug Fix Plan](./2026-02-17-fix-dspy-labels-extraction-tdd-plan.md)

### External Resources
- [pytest-asyncio Guide](https://pytest-asyncio.readthedocs.io/) — asyncio_mode="auto"
- [DSPy DummyLM](https://dspy.ai/api/utils/DummyLM/) — built-in stub LM
- [httpmock](https://docs.rs/httpmock/) — Rust HTTP mocking
- [cargo test Book](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [chromadb.EphemeralClient](https://docs.trychroma.com/) — in-memory ChromaDB
- [time-machine](https://github.com/adamchainz/time-machine) — async-safe time mocking
