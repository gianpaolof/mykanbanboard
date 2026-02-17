---
title: Comprehensive Unit Tests for Triage Functionality
type: feat
status: active
date: 2026-02-16
---

# Comprehensive Unit Tests for Triage Functionality

## Overview

The Kanban AI app's core AI features (triage, decompose, deep analysis) are currently not working reliably despite having valid API credentials. The trial-and-error debugging approach has proven ineffective. This plan establishes a systematic testing foundation to validate and fix the triage functionality before using the app in production.

**Goal**: Create comprehensive unit tests that validate DSPy agent behavior, ensuring triage, decompose, and deep analysis work correctly. Once tests pass, the app is ready for use.

## Problem Statement

### Current Issues
- **Triage not working**: Priority/label/effort assignment fails
- **Deep analysis not working**: Multi-hop analysis doesn't complete
- **Decompose not working**: Subtask generation fails
- **Valid API keys**: OpenAI/Anthropic credentials are valid with remaining credits
- **Trial-and-error approach**: No systematic way to validate fixes

### Root Causes Identified
1. **DSPy 3.x compatibility**: Breaking changes in assertion/extraction APIs
2. **Timeout synchronization**: Misaligned timeouts across Tauri → FastAPI → DSPy stack
3. **Context flow**: Board context not properly flowing through call chain
4. **Test coverage gaps**: Most existing tests are marked `@pytest.mark.skip`

### Why This Matters
Without reliable AI features, the Kanban app provides no value over manual task management. Users need confidence that triage will correctly classify tickets before trusting the system.

## Proposed Solution

Create a comprehensive test suite organized in 5 phases (foundation → modules → integration → edge cases → performance). Use mocked LLM responses to avoid API costs during development, with optional live API tests for validation.

### Test Strategy

**Phase-Based Approach:**
1. **Foundation Tests** (Critical): DSPy compatibility, extraction utilities, timeout mechanisms
2. **Module Tests** (Critical): Individual DSPy module behavior and validation
3. **Integration Tests** (High): End-to-end API flows with real components
4. **Edge Case Tests** (Medium): Malformed inputs, error scenarios, boundary conditions
5. **Performance Tests** (Low): Load testing, concurrent requests, token limits

**Mocking Strategy:**
- Mock DSPy LM responses for fast, deterministic tests
- Mock ChromaDB for isolated module tests
- Use real FastAPI TestClient for integration tests
- Optional `@pytest.mark.live_api` flag for real LLM calls

## Technical Approach

### Test Architecture

```
tests/
├── conftest.py                    # Shared fixtures and mocks
├── unit/
│   ├── test_dspy_compat.py       # DSPy 3.x compatibility layer
│   ├── test_extraction.py         # extract_value(), safe_extract()
│   ├── test_timeout.py            # run_sync_with_timeout()
│   └── test_validators.py         # Priority/effort/action validators
├── modules/
│   ├── test_triage_module.py     # TriageModule validation
│   ├── test_decompose_module.py  # DecomposeModule validation
│   ├── test_multihop.py          # DynamicMultiHopAnalyzer
│   └── test_context_aware.py    # Context-aware module variants
├── integration/
│   ├── test_triage_api.py        # /api/triage endpoint
│   ├── test_decompose_api.py     # /api/decompose endpoint
│   ├── test_analyze_api.py       # /api/agent/analyze endpoint
│   ├── test_chat_api.py          # /api/chat endpoint
│   └── test_judge_api.py         # /api/agent/judge endpoint
├── edge_cases/
│   ├── test_invalid_inputs.py    # Malformed requests
│   ├── test_chromadb_edge.py     # Empty collection, sync failures
│   ├── test_context_edge.py      # Missing/partial board_context
│   └── test_dependency_validation.py  # Out-of-bounds indices
└── performance/
    ├── test_concurrent_requests.py   # Load testing
    ├── test_token_limits.py          # Large descriptions
    └── test_cache_performance.py     # Cache hit rates
```

### Key Files to Modify

**Test Files (New):**
- `/services/agent/tests/unit/` - Foundation tests
- `/services/agent/tests/modules/` - Module-level tests
- `/services/agent/tests/integration/` - API endpoint tests
- `/services/agent/tests/edge_cases/` - Error scenario tests

**Test Infrastructure (Update):**
- `/services/agent/tests/conftest.py:1-50` - Add DSPy mocking fixtures
- `/services/agent/pyproject.toml:dependencies` - Add `pytest-asyncio`, `pytest-timeout`, `pytest-mock`

**Source Files (Fix as tests reveal issues):**
- `/services/agent/src/agent/modules.py:11-36` - DSPy compatibility shims
- `/services/agent/src/agent/modules.py:108-163` - TriageModule
- `/services/agent/src/agent/modules.py:198-389` - DecomposeModule
- `/services/agent/src/agent/multihop.py` - DynamicMultiHopAnalyzer
- `/services/agent/src/api/routes.py` - Timeout and error handling

### Technical Considerations

**DSPy Testing Challenges:**
- DSPy modules are stateful and depend on global `dspy.configure()`
- Need to reset DSPy state between tests
- Mock LM must return valid Prediction objects
- Assertions and suggestions require special handling

**Timeout Testing:**
- Use `pytest-timeout` plugin for test-level timeouts
- Mock `asyncio.wait_for()` to simulate timeouts
- Test coordinator timeout logic across layers

**ChromaDB Testing:**
- Use in-memory collection for fast tests
- Fixture to populate with sample tickets
- Test both empty and populated scenarios

**Context Flow Testing:**
- Verify `board_context` propagates through entire stack
- Test with minimal, partial, and full context
- Validate `board_id` injection in chat endpoint

## Implementation Phases

### Phase 1: Foundation Tests (Critical - Day 1)

**Goal**: Validate low-level utilities and DSPy compatibility layer

**Tasks:**
- [x] Create `tests/unit/test_dspy_compat.py` with tests for:
  - `_dspy_assert()` shim behavior
  - `_dspy_suggest()` shim behavior
  - Compatibility with DSPy 2.x and 3.x
- [x] Create `tests/unit/test_extraction.py` with tests for:
  - `extract_value()` with Prediction objects
  - `extract_value()` with single-element lists
  - `extract_value()` with bound methods
  - `safe_extract()` fallback behavior
- [x] Create `tests/unit/test_timeout.py` with tests for:
  - `run_sync_with_timeout()` normal completion
  - `run_sync_with_timeout()` timeout behavior
  - `run_sync_with_timeout()` exception propagation
- [x] Create `tests/unit/test_validators.py` with tests for:
  - Valid/invalid priority values
  - Valid/invalid effort values
  - Valid/invalid action values
  - Label normalization (string → list, unwrap singles)

**Success Criteria:**
- ✅ All foundation tests pass (69 tests)
- ✅ 100% coverage of utility functions
- ✅ DSPy compatibility verified

**Estimated Effort:** 4-6 hours

### Phase 2: Module-Level Tests (Critical - Day 1-2)

**Goal**: Validate DSPy module logic with mocked LLM responses

**Tasks:**
- [ ] Create `tests/modules/test_triage_module.py` with tests for:
  - Basic triage with valid inputs
  - Triage with invalid priority (should assert/fail)
  - Triage with invalid effort (should assert/fail)
  - Label normalization (string vs list)
  - Reasoning length validation (soft suggest)
- [ ] Create `tests/modules/test_context_aware.py` with tests for:
  - `ContextAwareTriageModule` with full context
  - Triage with empty ChromaDB (no similar tickets)
  - Triage with existing labels filter
  - Triage with project-specific priority rules
- [ ] Create `tests/modules/test_decompose_module.py` with tests for:
  - Basic decompose with 2-10 subtasks
  - Decompose with invalid subtask count (should assert)
  - Dependency validation (valid indices)
  - Effort normalization in subtasks
  - `BestOfNDecompose` scoring function
- [ ] Create `tests/modules/test_multihop.py` with tests for:
  - `DynamicMultiHopAnalyzer` with 3 complete hops
  - Hop 1: query generation
  - Retrieval phase: ChromaDB integration
  - Hop 2: deep analysis
  - Hop 3: actionable insights
  - Partial failure (hop 2 fails, does hop 3 run?)

**Success Criteria:**
- All module tests pass with mocked LLM
- Validation logic verified independently
- Context-aware behavior validated

**Estimated Effort:** 8-12 hours

### Phase 3: Integration Tests (High - Day 2-3)

**Goal**: Validate full API endpoint behavior with real FastAPI TestClient

**Tasks:**
- [ ] Create `tests/integration/test_triage_api.py` with tests for:
  - POST `/api/triage` with valid ticket
  - POST `/api/triage` with timeout (mocked slow LLM)
  - POST `/api/triage` with invalid response (triggers assertion)
  - POST `/api/triage` with board/project context
- [ ] Create `tests/integration/test_decompose_api.py` with tests for:
  - POST `/api/decompose` with valid task
  - POST `/api/decompose` with timeout
  - POST `/api/decompose` with invalid decomposition
- [ ] Create `tests/integration/test_analyze_api.py` with tests for:
  - POST `/api/agent/analyze` with valid ticket
  - POST `/api/agent/analyze` with 60s timeout
  - POST `/api/agent/analyze` with partial hop completion
- [ ] Create `tests/integration/test_chat_api.py` with tests for:
  - POST `/api/chat` with "create ticket" intent
  - POST `/api/chat` with board_context (verify board_id injection)
  - POST `/api/chat` with other action types (update/move/search)
  - POST `/api/chat` with 20s timeout
- [ ] Create `tests/integration/test_judge_api.py` with tests for:
  - POST `/api/agent/judge` with valid ticket
  - POST `/api/agent/judge` with score validation (0-10)

**Success Criteria:**
- All API endpoints return expected status codes
- Timeout behavior verified (504 after timeout)
- Error responses include meaningful messages
- Board context flows through to DSPy modules

**Estimated Effort:** 10-14 hours

### Phase 4: Edge Case Tests (Medium - Day 3-4)

**Goal**: Validate error handling and boundary conditions

**Tasks:**
- [ ] Create `tests/edge_cases/test_invalid_inputs.py` with tests for:
  - Malformed JSON requests
  - Missing required fields (title, description)
  - Oversized inputs (10k+ char descriptions)
  - Invalid ticket_id formats
- [ ] Create `tests/edge_cases/test_chromadb_edge.py` with tests for:
  - Empty ChromaDB collection (fresh install)
  - ChromaDB sync failure
  - Stale ChromaDB data (outdated tickets)
- [ ] Create `tests/edge_cases/test_context_edge.py` with tests for:
  - Missing board_context (None)
  - Partial board_context (missing fields)
  - Oversized board_context (DoS prevention)
  - Invalid board_id in context
- [ ] Create `tests/edge_cases/test_dependency_validation.py` with tests for:
  - Out-of-bounds dependency indices
  - Self-referencing dependencies (subtask depends on itself)
  - Circular dependencies

**Success Criteria:**
- All error scenarios return appropriate HTTP status codes
- No unhandled exceptions or crashes
- Error messages are helpful for debugging

**Estimated Effort:** 6-8 hours

### Phase 5: Performance Tests (Low - Day 4-5)

**Goal**: Validate performance and scalability

**Tasks:**
- [ ] Create `tests/performance/test_concurrent_requests.py` with tests for:
  - 10 concurrent triage requests
  - Rate limit handling (429 errors)
  - Request queuing behavior
- [ ] Create `tests/performance/test_token_limits.py` with tests for:
  - Very long ticket descriptions (token budget management)
  - Context window exceeded scenarios
- [ ] Create `tests/performance/test_cache_performance.py` with tests for:
  - Cache hit rates
  - Cache invalidation
  - Cache staleness

**Success Criteria:**
- Concurrent requests don't cause race conditions
- Token budget management works correctly
- Cache provides performance benefits

**Estimated Effort:** 4-6 hours

## Acceptance Criteria

### Must Have (Blocking)
- [x] All Phase 1 (Foundation) tests pass
- [ ] All Phase 2 (Module) tests pass for TriageModule
- [ ] All Phase 2 tests pass for DecomposeModule
- [ ] All Phase 2 tests pass for DynamicMultiHopAnalyzer
- [ ] All Phase 3 (Integration) tests pass for `/api/triage` endpoint
- [ ] All Phase 3 tests pass for `/api/decompose` endpoint
- [ ] All Phase 3 tests pass for `/api/agent/analyze` endpoint
- [ ] All Phase 3 tests pass for `/api/chat` endpoint with board_context
- [ ] Timeout behavior verified (504 returned after configured timeout)
- [ ] DSPy 3.x compatibility validated (assertions, extraction)
- [ ] ChromaDB empty collection handled gracefully
- [ ] Board context flows correctly through entire stack

### Should Have (Important)
- [ ] All Phase 4 (Edge Case) tests pass
- [ ] Error messages are clear and actionable
- [ ] Malformed inputs handled with 422 status codes
- [ ] Dependency validation in decompose response
- [ ] Label normalization consistent (string → list, unwrap singles)
- [ ] Optional live API tests with `@pytest.mark.live_api` flag

### Nice to Have (Enhancements)
- [ ] All Phase 5 (Performance) tests pass
- [ ] Test coverage report with 80%+ coverage
- [ ] Performance benchmarks established
- [ ] Load testing validates concurrent request handling

## Success Metrics

### Primary Metrics
- **Test Pass Rate**: 100% of must-have tests passing
- **Test Execution Time**: Full suite runs in < 60 seconds (with mocked LLM)
- **Coverage**: 80%+ code coverage for agent modules and API routes

### Quality Metrics
- **Bug Detection**: Tests catch real issues before production
- **Regression Prevention**: Existing functionality remains stable
- **Confidence Level**: Team trusts tests enough to skip manual QA

### Business Metrics
- **Time to Production**: App ready for use once tests pass
- **Debug Time Reduction**: Systematic tests replace trial-and-error
- **User Trust**: Reliable AI features increase adoption

## Dependencies & Risks

### Dependencies
- **Python Dependencies**: `pytest`, `pytest-asyncio`, `pytest-timeout`, `pytest-mock`, `httpx`
- **DSPy Version**: Compatibility with both DSPy 2.x and 3.x
- **ChromaDB**: In-memory collection for testing
- **FastAPI TestClient**: For integration tests
- **API Keys**: Optional for live API tests (can skip with mocks)

### Risks

**High Priority:**
- **DSPy API changes**: DSPy is evolving rapidly, may introduce breaking changes
  - *Mitigation*: Pin DSPy version, add compatibility shims, monitor releases
- **Timeout coordination**: Misaligned timeouts across stack could cause flaky tests
  - *Mitigation*: Document timeout hierarchy, test timeout edge cases
- **ChromaDB state management**: Tests may interfere with each other if not isolated
  - *Mitigation*: Use fixtures with fresh ChromaDB instances, cleanup after tests

**Medium Priority:**
- **Mock brittleness**: Mocked LLM responses may not match real API behavior
  - *Mitigation*: Add optional live API tests, validate mocks against real responses
- **Test maintenance**: Large test suite requires ongoing maintenance
  - *Mitigation*: Keep tests focused, use fixtures for shared setup, document patterns

**Low Priority:**
- **Performance test variability**: Concurrent tests may have timing issues
  - *Mitigation*: Use generous timeouts, focus on correctness over exact timing

## Technical Decisions

### Why Mock LLM Responses?
- **Fast execution**: Tests run in seconds, not minutes
- **Deterministic**: No API rate limits or flaky network issues
- **Cost-effective**: Avoid API charges during development
- **Offline capable**: Can run tests without internet connection

### Why Phase-Based Approach?
- **Early wins**: Foundation tests catch utility bugs immediately
- **Incremental validation**: Each phase builds on previous successes
- **Risk management**: Critical tests first, nice-to-have tests later
- **Focus**: Team knows what to work on at each stage

### Why Separate Unit/Integration/Edge/Performance?
- **Clarity**: Easy to understand what each test category validates
- **Speed**: Can run fast unit tests during development, slow integration tests on CI
- **Maintenance**: Easier to update tests when organized by concern

## References & Research

### Internal References
- **DSPy Modules**: `/services/agent/src/agent/modules.py:108-389`
- **API Routes**: `/services/agent/src/api/routes.py:1-1002`
- **Multi-Hop Analyzer**: `/services/agent/src/agent/multihop.py`
- **ChromaDB Manager**: `/services/agent/src/db/chroma.py`
- **Existing Tests**: `/services/agent/tests/test_modules.py`, `/services/agent/tests/test_api.py`
- **Git Commits**: `35e865a` (list unwrapping), `92d667c` (timeout fixes), `8274ffc` (board context)

### External References
- **DSPy Documentation**: https://dspy-docs.vercel.app/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **pytest Best Practices**: https://docs.pytest.org/en/stable/goodpractices.html
- **ChromaDB Testing**: https://docs.trychroma.com/usage-guide

### Related Work
- **Recent Commits**: Multiple fixes for DSPy extraction and timeout issues
- **Test Plan**: `/Users/g.filippa/mystuff/kanban/docs/TEST_PLAN.md` (existing comprehensive guide)
- **DSPy Guide**: `/Users/g.filippa/mystuff/kanban/docs/dspy-guide/` (concepts and best practices)

## Critical Questions for User

Before implementation, please clarify:

### Q1: DSPy Invalid Enum Handling
**What should happen when DSPy returns invalid enum values (e.g., priority="urgent" instead of "critical")?**
- Option A: Retry with rephrased prompt (more robust, slower)
- Option B: Return 422 with validation error (clear user feedback)
- Option C: Use closest valid value (silent correction)
- Current: Returns 500 with generic error

### Q2: Timeout Synchronization
**How should timeouts be coordinated across Tauri → FastAPI → DSPy?**
- Current: Tauri may timeout before FastAPI responds
- Proposal: Tauri timeout = FastAPI timeout + 5s buffer
- Need confirmation on acceptable timeout values per operation

### Q3: ChromaDB Empty Collection
**What should happen when ChromaDB has no tickets indexed (fresh install)?**
- Option A: Fail with clear error message
- Option B: Gracefully degrade to basic (non-context-aware) modules
- Option C: Proceed with empty similar_tickets (may affect quality)
- Current: Unclear, not tested

### Q4: New Label Suggestions
**Can triage suggest new labels not in existing_labels, or must it use only existing ones?**
- Option A: New labels allowed (frontend must handle creation)
- Option B: Strict filtering to existing labels only
- Current: Appears to allow new labels, but unclear if intentional

### Q5: Partial Results on Timeout
**Should multi-hop analysis return partial results if it times out mid-execution?**
- Option A: Return partial results from completed hops
- Option B: Fail completely with 504 error
- Current: Fails completely

---

**Next Steps**: Once critical questions are answered, proceed to Phase 1 implementation.
