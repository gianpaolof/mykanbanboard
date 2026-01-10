# Kanban AI - Agent Design Document

## Overview

L'agent AI di Kanban AI è progettato per essere un assistente proattivo nella gestione dei task. Non è un semplice chatbot, ma un sistema che comprende il contesto del tuo lavoro e può agire autonomamente quando appropriato.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │  Agent Chat UI  │  │  Inline Actions │                  │
│  └────────┬────────┘  └────────┬────────┘                  │
│           │                    │                            │
│           └──────────┬─────────┘                            │
│                      │                                      │
└──────────────────────┼──────────────────────────────────────┘
                       │ Tauri IPC
┌──────────────────────┼──────────────────────────────────────┐
│                      │        Rust Backend                  │
│              ┌───────▼───────┐                              │
│              │ Agent Proxy   │                              │
│              └───────┬───────┘                              │
└──────────────────────┼──────────────────────────────────────┘
                       │ HTTP localhost:8765
┌──────────────────────┼──────────────────────────────────────┐
│                      │        Python Sidecar                │
│              ┌───────▼───────┐                              │
│              │   FastAPI     │                              │
│              └───────┬───────┘                              │
│                      │                                      │
│  ┌───────────────────┼───────────────────────────────┐     │
│  │                   │      DSPy Agent               │     │
│  │  ┌────────────────▼────────────────┐              │     │
│  │  │        Action Decider           │              │     │
│  │  └────────────────┬────────────────┘              │     │
│  │                   │                               │     │
│  │    ┌──────────────┼──────────────┐               │     │
│  │    │              │              │               │     │
│  │  ┌─▼──┐       ┌───▼───┐    ┌────▼────┐         │     │
│  │  │Triage│     │Decompose│  │Summarize│         │     │
│  │  └────┘       └───────┘    └─────────┘         │     │
│  │                                                  │     │
│  └──────────────────────────────────────────────────┘     │
│                      │                                      │
│  ┌───────────────────┼───────────────────────────────┐     │
│  │              ChromaDB                             │     │
│  │           (Vector Store)                          │     │
│  └───────────────────────────────────────────────────┘     │
│                      │                                      │
│  ┌───────────────────▼───────────────────────────────┐     │
│  │              LLM Provider                         │     │
│  │   Claude API (primary) / OpenAI (fallback)        │     │
│  └───────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## DSPy Framework

### Why DSPy?

1. **Programmatic Prompting**: Definisci *cosa* vuoi, non *come* chiederlo
2. **Type Safety**: Signature con tipi Python per input/output
3. **Composability**: Moduli componibili come funzioni
4. **Optimization**: Può auto-ottimizzare prompt con esempi
5. **Testability**: Facile da testare e validare

### Core Concepts

```python
# Signature: definisce input/output di un task
class MySignature(dspy.Signature):
    input_field: str = dspy.InputField(desc="Description")
    output_field: str = dspy.OutputField(desc="Description")

# Module: implementa la logica
class MyModule(dspy.Module):
    def __init__(self):
        self.predictor = dspy.ChainOfThought(MySignature)
    
    def forward(self, **inputs):
        return self.predictor(**inputs)

# Execution
module = MyModule()
result = module(input_field="value")
```

## Agent Capabilities

### 1. Triage (Auto-categorization)

**Scopo:** Assegnare automaticamente metadati a nuovi ticket

**Input:**
- `title`: Titolo del ticket
- `description`: Descrizione (opzionale)
- `existing_labels`: Labels già usate nel board (per consistenza)

**Output:**
- `priority`: low | medium | high | critical
- `labels`: Lista di max 3 labels
- `effort_estimate`: xs | s | m | l | xl
- `reasoning`: Spiegazione delle scelte

**Signature:**
```python
class TriageTicket(dspy.Signature):
    """Analizza un ticket e assegna metadati appropriati.
    
    Criteri per priority:
    - critical: Blocca produzione/utenti, richiede fix immediato
    - high: Importante, impatta significativamente, entro 1-2 giorni
    - medium: Standard, pianificabile normalmente
    - low: Nice-to-have, può aspettare
    
    Criteri per effort:
    - xs: < 1 ora, fix rapido
    - s: 1-4 ore, mezza giornata
    - m: 1-2 giorni, task standard
    - l: 3-5 giorni, feature complessa
    - xl: > 1 settimana, epic
    """
    title: str = dspy.InputField()
    description: str = dspy.InputField()
    existing_labels: list[str] = dspy.InputField()
    
    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField()
    labels: list[str] = dspy.OutputField()
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField()
    reasoning: str = dspy.OutputField()
```

### 2. Decomposition (Task Breakdown)

**Scopo:** Scomporre task complessi in subtask gestibili

**Input:**
- `title`: Titolo del task
- `description`: Descrizione dettagliata
- `context`: Info dal board (altri ticket, labels, etc.)

**Output:**
- `subtasks`: Lista di {title, description, effort}
- `dependencies`: Coppie di indici che indicano dipendenze

**Signature:**
```python
class DecomposeTask(dspy.Signature):
    """Scomponi un task in subtask atomici e actionable.
    
    Ogni subtask deve essere:
    - Completabile in una singola sessione di lavoro
    - Verificabile (criteri di done chiari)
    - Il più indipendente possibile
    
    Output 3-7 subtask per task tipico.
    """
    title: str = dspy.InputField()
    description: str = dspy.InputField()
    context: str = dspy.InputField()
    
    subtasks: list[dict] = dspy.OutputField()
    dependencies: list[tuple[int, int]] = dspy.OutputField()
```

### 3. Daily Summary

**Scopo:** Generare un riepilogo giornaliero con priorità

**Input:**
- `in_progress`: Ticket attualmente in lavorazione
- `blocked`: Ticket bloccati
- `due_soon`: Ticket con deadline vicina
- `recently_completed`: Completati di recente

**Output:**
- `greeting`: Saluto personalizzato
- `focus_today`: Top 3 priorità
- `blockers`: Blocchi da risolvere
- `wins`: Quick wins suggeriti

### 4. Semantic Search

**Scopo:** Trovare ticket correlati per significato

**Come funziona:**
1. Ogni ticket viene embeddato (titolo + descrizione)
2. Query viene embeddata
3. Similarity search in ChromaDB
4. Ranking dei risultati

**Embedding Model:**
- Primary: `text-embedding-3-small` (OpenAI)
- Alternative: `voyage-2` (Anthropic)

### 5. Chat Interface

**Scopo:** Interazione conversazionale con l'agent

**Capabilities:**
- Rispondere a domande sui ticket
- Eseguire comandi naturali
- Suggerire azioni
- Brainstorming

**Action Decider:**
```python
class ActionDecider(dspy.Signature):
    """Decide quale azione eseguire basandosi sul messaggio.
    
    Actions:
    - create_ticket: "crea un ticket per X"
    - update_ticket: "cambia priority di X a high"
    - move_ticket: "sposta X in done"
    - search_tickets: "trova ticket su Y"
    - summarize: "cosa devo fare oggi?"
    - none: risposta conversazionale senza azione
    """
    user_message: str = dspy.InputField()
    current_context: dict = dspy.InputField()
    
    action: str = dspy.OutputField()
    params: dict = dspy.OutputField()
    response: str = dspy.OutputField()
```

## API Endpoints

### POST /api/triage
```json
// Request
{
  "ticket_id": "uuid",
  "title": "Fix login bug",
  "description": "Users can't login on Safari"
}

// Response
{
  "priority": "high",
  "labels": ["bug", "auth", "browser"],
  "effort": "s",
  "reasoning": "Login issues are critical for user access..."
}
```

### POST /api/chat
```json
// Request
{
  "message": "Cosa devo fare oggi?",
  "context": {
    "tickets": [...],
    "current_view": "board"
  }
}

// Response
{
  "action": "summarize",
  "params": {},
  "response": "Buongiorno! Oggi ti consiglio di..."
}
```

### POST /api/decompose
```json
// Request
{
  "ticket_id": "uuid"
}

// Response
{
  "subtasks": [
    {"title": "Setup auth flow", "description": "...", "effort": "m"},
    {"title": "Add login form", "description": "...", "effort": "s"},
    ...
  ],
  "dependencies": [[1, 0], [2, 1]]
}
```

### GET /api/daily-summary
```json
// Response
{
  "greeting": "Buongiorno!",
  "focus_today": [
    "Completare il fix del login bug",
    "Review della PR di Marco",
    "Preparare demo per domani"
  ],
  "blockers": [
    "Il ticket #123 è bloccato in attesa di design"
  ],
  "wins": [
    "Potresti chiudere il ticket #456, manca solo il test"
  ]
}
```

### GET /api/search
```json
// Request
{
  "query": "problemi di performance",
  "limit": 5
}

// Response
{
  "results": [
    {
      "id": "uuid",
      "title": "Ottimizzare query database",
      "score": 0.92,
      "explanation": "Match per 'performance' e 'ottimizzare'"
    },
    ...
  ]
}
```

## Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class AgentSettings(BaseSettings):
    # LLM Configuration
    anthropic_api_key: str
    openai_api_key: str | None = None
    default_model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "gpt-4o-mini"
    
    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Database
    chroma_path: str = "./data/chroma"
    chroma_collection: str = "tickets"
    
    # Behavior
    auto_triage_enabled: bool = True
    max_decompose_subtasks: int = 7
    search_results_limit: int = 10
    
    # Rate Limiting
    max_requests_per_minute: int = 20
    
    class Config:
        env_file = ".env"
```

## Error Handling

```python
from enum import Enum

class AgentError(Exception):
    pass

class ErrorCode(Enum):
    LLM_ERROR = "llm_error"
    RATE_LIMITED = "rate_limited"
    INVALID_INPUT = "invalid_input"
    NOT_FOUND = "not_found"
    INTERNAL = "internal_error"

class AgentException(AgentError):
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

# Usage
@app.exception_handler(AgentException)
async def agent_exception_handler(request, exc: AgentException):
    return JSONResponse(
        status_code=400 if exc.code != ErrorCode.INTERNAL else 500,
        content={
            "error": exc.code.value,
            "message": exc.message,
            "details": exc.details
        }
    )
```

## Testing Strategy

### Unit Tests
```python
def test_triage_urgent_ticket():
    agent = KanbanAgent()
    result = agent.auto_triage(
        {"title": "URGENTE: Server down", "description": "Production non risponde"},
        existing_labels=["bug", "urgent", "infra"]
    )
    assert result["priority"] in ["high", "critical"]
    assert "urgent" in result["labels"] or "infra" in result["labels"]
```

### Integration Tests
```python
@pytest.mark.integration
async def test_full_triage_flow():
    async with AsyncClient(app=app) as client:
        response = await client.post("/api/triage", json={
            "ticket_id": "test-123",
            "title": "Add dark mode",
            "description": "Users want dark mode option"
        })
        assert response.status_code == 200
        data = response.json()
        assert "priority" in data
        assert "labels" in data
```

### Evaluation with DSPy
```python
def triage_metric(example, prediction):
    # Check if priority is reasonable
    priority_score = 1 if prediction.priority in ["low", "medium", "high", "critical"] else 0
    
    # Check labels relevance
    label_score = len(set(prediction.labels) & set(example.expected_labels)) / len(example.expected_labels)
    
    return (priority_score + label_score) / 2

# Optimize
optimizer = dspy.BootstrapFewShot(metric=triage_metric)
optimized_triage = optimizer.compile(agent.triage, trainset=train_examples)
```

## Future Enhancements

### Phase 2
- [ ] Agent memory (ricorda preferenze utente)
- [ ] Proactive suggestions ("Hai 3 ticket scaduti...")
- [ ] Learning from feedback (ottimizzazione continua)

### Phase 3
- [ ] Multi-board awareness
- [ ] Integration con calendar
- [ ] Stima migliorata con historical data

### Phase 4
- [ ] Collaborative features (per team)
- [ ] Custom agent personalities
- [ ] Plugin system per custom actions
