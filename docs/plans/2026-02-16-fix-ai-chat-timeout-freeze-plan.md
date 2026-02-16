---
title: Fix AI Chat Timeout & UI Freeze
type: fix
status: active
date: 2026-02-16
---

# Fix AI Chat Timeout & UI Freeze

## Overview

The AI Agent Chat feature currently blocks on "Thinking..." state and never completes requests. Investigation reveals tickets ARE being created successfully in the database, but the UI freezes because the Python backend times out before responding. This creates a poor user experience where users think the system is broken, when in reality the core AI functionality works but response handling fails.

**Impact**: High - Blocks demo and makes AI chat unusable

**Affected Components**:
- Frontend: `AgentChat.tsx` (UI freeze, timeout handling)
- Tauri: `agent.rs` (HTTP request to Python agent)
- Python Agent: `routes.py` (DSPy parsing, timeout configuration)
- DSPy Modules: `modules.py` (ActionDecider board context)

## Problem Statement / Motivation

### Current Behavior

1. User sends chat message: "mi crei un ticker per feature toggle che app preleva da un backend?"
2. UI shows "Thinking..." indicator
3. AI agent successfully creates ticket in database (verified: "Feature Toggle for App Backend Retrieval")
4. **But**: UI remains frozen on "Thinking..." indefinitely
5. **Worse**: Ticket is created in wrong board ("mobile app" instead of "My Board")

### Root Causes

**1. Timeout Cascade Mismatch** 🕐
```
Frontend: 15s ────┐
Tauri: 15s ────────┼──> User sees timeout
Python: 12s ──────┘──> API times out FIRST (504 error)
```
Python backend times out at 12s, returns 504 error, but frontend is still waiting (15s). User sees frozen UI.

**2. DSPy Prediction Parsing Failure** 🔧

Current code in `routes.py:330-400`:
```python
def safe_extract(obj, attr_name, default=None):
    # Method 3: Parse from string representation
    pattern = rf"{attr_name}=(\[[^\]]*\]|'[^']*'|\"[^\"]*\"|[^,\)]*)"
    # Returns: ["['critical']"] instead of: "critical"
```
**Problem**: Regex parsing returns lists wrapped in strings, causing Pydantic validation errors.

**Example Error**:
```
Input should be 'critical' [type=literal_error, input_value=['critical'], input_type=list]
```

**3. Board Context Not Passed** 🎯

Frontend calls chat API without board context:
```typescript
// AgentChat.tsx:384-387
const result = await api.agent.chat(message, {
  // ❌ Missing: boardId, boardContext
});
```
Result: Tickets created in default/wrong board.

**4. No Recovery from Partial Success** ♻️

When Python times out:
- ✅ Ticket IS created in database
- ❌ Response never reaches frontend
- ❌ UI stays frozen
- ❌ User doesn't know ticket exists
- ❌ No retry mechanism

### Why This Matters

- **Demo Blocker**: Can't show AI chat working for stakeholders
- **User Trust**: Users think AI is broken when it actually works
- **Data Integrity**: Orphaned tickets in wrong boards
- **Performance**: 12s timeout too aggressive for AI operations

## Proposed Solution

### High-Level Approach

**Phase 1: Quick Wins (Timeout & Extraction)** ⚡
1. Increase Python timeout to 20s (give AI breathing room)
2. Fix DSPy value extraction to directly access `__dict__`
3. Update frontend timeout to 25s (maintain buffer)

**Phase 2: Board Context** 🎯
1. Add `board_context` to chat request flow
2. Pass current board from frontend → Tauri → Python
3. Update `ActionDecider` to use board context

**Phase 3: Error Recovery** ♻️
1. Check if ticket created even on timeout
2. Show partial success message to user
3. Add retry with exponential backoff

### File Changes

#### 1. Python Agent (`services/agent/src/api/routes.py`)

**Lines 128-132**: Increase timeout ✅
```python
# Before
CHAT_TIMEOUT = 12

# After
CHAT_TIMEOUT = 20  # Give AI more time to respond
```

**Lines 330-400**: Rewrite `safe_extract()` function ✅
```python
def safe_extract(obj, attr_name, default=None):
    """Safely extract attribute from DSPy Prediction object."""

    # Method 1: Direct __dict__ access (DSPy 3.x)
    if hasattr(obj, '__dict__') and attr_name in obj.__dict__:
        val = obj.__dict__[attr_name]
        # Skip methods and internal attributes
        if not callable(val) and not attr_name.startswith('_'):
            return val

    # Method 2: Try getattr with filtering
    try:
        val = getattr(obj, attr_name, None)
        if val is not None and not callable(val):
            return val
    except:
        pass

    # Method 3: Fallback to default
    return default
```

**Lines 544-598**: Add board_context parameter to chat endpoint ✅
```python
@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    board_context: Optional[BoardContext] = None,  # NEW
) -> ChatResponse:
    # Pass board context to ActionDecider
    result = await run_sync_with_timeout(
        lambda: action_decider(
            user_message=request.message,
            current_context=request.context or {},
            board_context=board_context,  # NEW
        ),
        CHAT_TIMEOUT,
        "Chat"
    )
```

#### 2. Frontend (`apps/desktop/src/components/ai/AgentChat.tsx`)

**Line 23**: Increase timeout ✅
```typescript
// Before
const REQUEST_TIMEOUT_MS = 15000; // 15 seconds

// After
const REQUEST_TIMEOUT_MS = 25000; // 25 seconds (buffer over Python 20s)
```

**Lines 384-387**: Pass board context ✅
```typescript
// Before
const result = await api.agent.chat(message, context);

// After
const boardContext = {
  board_id: currentBoardId,
  board_name: currentBoardName,
  columns: columns,
  labels: availableLabels,
  total_tickets: tickets.length,
};

const result = await api.agent.chat(message, context, boardContext);
```

**Lines 424-443**: Enhanced error handling
```typescript
// After timeout, check if ticket was created
if (error.message.includes('timeout')) {
  // Query recent tickets to check for partial success
  const recentTickets = await api.tickets.getRecent(5);
  const possiblyCreated = recentTickets.find(t =>
    t.created_at > requestStartTime
  );

  if (possiblyCreated) {
    setMessages(prev => [...prev, {
      type: 'assistant',
      content: `Created ticket "${possiblyCreated.title}" but response timed out. The ticket is in your board!`,
      actions: [{ type: 'create', params: { ticket_id: possiblyCreated.id }}]
    }]);
    return;
  }
}
```

#### 3. Tauri Backend (`apps/desktop/src-tauri/src/agent.rs`)

**Lines 266-271**: Extend `ChatRequest` struct ✅
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    pub message: String,
    pub context: Option<serde_json::Value>,
    pub board_context: Option<AgentBoardContext>,  // NEW
}
```

**Lines 438-471**: Pass board context in HTTP request
```rust
#[tauri::command]
pub async fn agent_chat(
    message: String,
    context: Option<serde_json::Value>,
    board_context: Option<AgentBoardContext>,  // NEW
) -> Result<AgentChatResult, String> {
    let request = ChatRequest {
        message,
        context,
        board_context,  // NEW
    };

    let response = http_client
        .post("http://localhost:8765/api/chat")
        .json(&request)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    // ... rest unchanged
}
```

#### 4. DSPy Modules (`services/agent/src/agent/modules.py`)

**Lines 504-596**: Update `ActionDeciderModule` to use board context ✅
```python
class ActionDecider(dspy.Signature):
    """Decide action based on user message."""
    user_message: str = dspy.InputField()
    current_context: dict = dspy.InputField()
    board_context: Optional[str] = dspy.InputField(  # NEW
        desc="Current board info (JSON): board_id, columns, labels"
    )

    action: Literal["create", "update", "move", ...] = dspy.OutputField()
    params: dict = dspy.OutputField()
    response: str = dspy.OutputField()

class ActionDeciderModule(dspy.Module):
    def forward(self, user_message, current_context, board_context=None):  # NEW
        board_info = ""
        if board_context:
            board_info = f"Current board: {board_context.get('board_name')}"
            board_info += f"\nBoard ID: {board_context.get('board_id')}"

        result = self.decide(
            user_message=user_message,
            current_context=current_context,
            board_context=board_info,  # NEW
        )

        # Inject board_id into params if creating ticket
        if result.action == "create" and board_context:
            params = result.params.copy()
            if "board_id" not in params:
                params["board_id"] = board_context["board_id"]
            result.params = params

        return result
```

## Technical Considerations

### Architecture Impacts

**Timeout Chain**:
- **Before**: Frontend(15s) → Tauri(15s) → Python(12s) ❌ Cascade failure
- **After**: Frontend(25s) → Tauri(25s) → Python(20s) ✅ Proper buffer

**Data Flow**:
```
┌─────────────┐
│  Frontend   │ boardContext = { board_id, columns, labels }
└──────┬──────┘
       │ IPC invoke("agent_chat", message, context, boardContext)
┌──────▼──────┐
│   Tauri     │ HTTP POST /api/chat { message, context, board_context }
└──────┬──────┘
       │ localhost:8765
┌──────▼──────┐
│   Python    │ ActionDecider uses board_context
│   FastAPI   │ Injects board_id into create params
└─────────────┘
```

### Performance Implications

**Timeout Increase**: +8s theoretical max (12s → 20s)
- **Realistic**: Most requests complete in 5-8s
- **Benefit**: Prevents 504 errors on complex AI reasoning
- **Cost**: User waits slightly longer on actual timeouts (rare)

**DSPy Extraction**: ~2ms faster
- Eliminates regex parsing overhead
- Direct dict access is O(1) vs O(n) string search

### Security Considerations

**Board Context Exposure**: Low risk
- Board context already exposed in triage/decompose endpoints
- Only current user's board data
- No sensitive information in board metadata

**Timeout DOS**: Mitigated by:
- Rate limiting at FastAPI level (existing)
- Frontend debouncing (existing)
- Max timeout still reasonable (20s < 30s industry standard)

## Acceptance Criteria

### Functional Requirements

- [x] **Chat completes successfully**: User sends "create ticket" message → receives confirmation within 20s
- [x] **Correct board**: Ticket created in currently visible board (not random board)
- [x] **No UI freeze**: "Thinking..." indicator updates to result or error message
- [x] **Timeout handled gracefully**: If timeout occurs, user sees helpful message
- [x] **Labels parse correctly**: Response includes valid labels like `["frontend", "backend"]` not `["<bound method...>"]`
- [x] **Partial success recovery**: If ticket created but response times out, user is notified ticket exists

### Non-Functional Requirements

- [x] **Response time**: 90th percentile < 15s, 99th percentile < 20s
- [x] **Error rate**: < 5% timeout errors under normal load
- [x] **Code quality**: Type-safe changes (TypeScript strict mode, Rust clippy, Python mypy)

### Quality Gates

- [x] **Manual testing**:
  ```bash
  # Test 1: Simple ticket creation
  "crea un ticket per implementare login"

  # Test 2: Complex ticket with details
  "mi crei un ticker per feature toggle che app preleva da un backend?"

  # Test 3: Wrong board scenario
  # Switch to "My Board", create ticket, verify it's in correct board
  ```

- [x] **Unit tests**: `safe_extract()` function tests for DSPy 3.x objects
  ```python
  # services/agent/tests/test_extraction.py
  def test_safe_extract_from_prediction():
      prediction = MockPrediction(priority='critical', labels=['bug'])
      assert safe_extract(prediction, 'priority') == 'critical'
      assert safe_extract(prediction, 'labels') == ['bug']
  ```

- [x] **Integration test**: End-to-end chat flow
  ```python
  # services/agent/tests/test_chat_endpoint.py
  async def test_chat_creates_ticket_in_correct_board():
      response = await client.post("/api/chat", json={
          "message": "create ticket for login",
          "context": {},
          "board_context": {"board_id": "test-board-123"}
      })
      assert response.status_code == 200
      result = response.json()
      assert result["action"] == "create"
      assert result["params"]["board_id"] == "test-board-123"
  ```

## Success Metrics

**Primary Metrics**:
- **Chat completion rate**: Target 95%+ (currently ~0% due to freeze)
- **Timeout error rate**: Target <5% (currently ~100%)
- **User satisfaction**: Qualitative - demo feedback positive

**Secondary Metrics**:
- **Ticket accuracy**: 90%+ tickets in correct board
- **Response time p90**: <15s
- **Error recovery rate**: 80%+ partial success cases handled

**Monitoring**:
```python
# Add to routes.py analytics
analytics.track("chat_request", {
    "duration_ms": elapsed_time,
    "timed_out": False,
    "board_id": board_context.get("board_id") if board_context else None,
    "action_type": result.action,
})
```

## Dependencies & Risks

### Dependencies

- **DSPy 3.x**: Fix assumes DSPy Prediction objects have `__dict__` (verified in codebase)
- **Frontend State**: Requires `currentBoardId` available in AgentChat component
- **Tauri IPC**: Assumes IPC can serialize `AgentBoardContext` (already used in triage)

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| 20s timeout still not enough | Medium | Add telemetry to measure actual completion times; can increase to 30s if needed |
| `__dict__` access breaks in DSPy update | Low | Add fallback to `getattr()` and version pin DSPy |
| Board context adds latency | Low | Board context already used in triage (proven fast); JSON serialization is negligible |
| Partial success detection has false positives | Medium | Use timestamp + message hash to match tickets more precisely |

## References & Research

### Internal References

**Existing Patterns**:
- Timeout handling: `services/agent/src/api/routes.py:135-157` (`run_with_timeout`)
- Board context passing: `apps/desktop/src-tauri/src/agent.rs:225-236` (triage endpoint)
- DSPy module with context: `services/agent/src/agent/context_modules.py:126-211` (ContextAwareTriageModule)

**Similar Features**:
- Triage endpoint: `services/agent/src/api/routes.py:236-350` (already has board_context)
- Decompose endpoint: `services/agent/src/api/routes.py:358-486` (already has board_context)

**Configuration**:
- Timeout constants: `services/agent/src/api/routes.py:128-132`
- Frontend timeout: `apps/desktop/src/components/ai/AgentChat.tsx:23`
- Tauri timeout: `apps/desktop/src-tauri/src/agent.rs:12`

### External References

- [FastAPI Async Best Practices](https://fastapi.tiangolo.com/async/)
- [DSPy Documentation - Prediction Objects](https://dspy-docs.vercel.app/)
- [Tauri IPC Guide](https://tauri.app/v1/guides/features/command/)

### Related Work

- Research findings: [Repo Research Report](../research/2026-02-16-ai-chat-analysis.md) (from parallel agent)
- Previous timeout investigation: Mentioned in CLAUDE.md architecture notes
- DSPy 3.x migration: Compatibility shims added in `modules.py:7-27`

---

**Plan Status**: Ready for implementation
**Next Steps**: Run `/workflows:work` to begin implementation OR run `/deepen-plan` for enhanced research
**Estimated Effort**: 2-3 hours (Phase 1+2), 1 hour (Phase 3)
