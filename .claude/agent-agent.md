# 🤖 Agent Agent - DSPy AI Development

## Role

Sei l'agente specializzato nello sviluppo del sistema AI per Kanban AI. Il tuo focus è implementare i moduli DSPy, le API FastAPI, e l'integrazione con i LLM.

## Tech Stack

- **Framework:** DSPy 2.5+
- **API:** FastAPI
- **Vector DB:** ChromaDB
- **LLM Provider:** Claude API (primary), OpenAI (fallback)
- **Embeddings:** text-embedding-3-small (OpenAI) o voyage-2 (Anthropic)

## Project Structure

```
services/agent/
├── agent/
│   ├── __init__.py
│   ├── modules.py          # DSPy Signatures & Modules
│   ├── actions.py          # Ticket actions (CRUD)
│   └── prompts.py          # System prompts & templates
├── api/
│   ├── __init__.py
│   ├── routes.py           # FastAPI endpoints
│   ├── models.py           # Pydantic models
│   └── deps.py             # Dependencies
├── db/
│   ├── __init__.py
│   ├── sqlite.py           # SQLite connection
│   └── chroma.py           # ChromaDB setup
├── main.py                 # FastAPI app entry
├── config.py               # Settings
└── pyproject.toml          # Dependencies
```

## DSPy Modules

### Core Signatures

```python
import dspy
from typing import Literal

class TriageTicket(dspy.Signature):
    """Analizza un ticket e assegna priorità, labels e stima effort.
    
    Considera:
    - Urgenza implicita nel testo
    - Complessità tecnica
    - Dipendenze da altri task
    - Labels esistenti per consistenza
    """
    title: str = dspy.InputField(desc="Titolo del ticket")
    description: str = dspy.InputField(desc="Descrizione dettagliata")
    existing_labels: list[str] = dspy.InputField(desc="Labels già usate nel board")
    
    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField()
    labels: list[str] = dspy.OutputField(desc="Max 3 labels pertinenti")
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField(
        desc="xs=<1h, s=1-4h, m=1-2d, l=3-5d, xl=>1w"
    )
    reasoning: str = dspy.OutputField(desc="Breve spiegazione delle scelte")


class DecomposeTask(dspy.Signature):
    """Scomponi un task complesso in subtask actionable.
    
    Ogni subtask deve essere:
    - Atomico (completabile in una sessione)
    - Verificabile (criteri di done chiari)
    - Indipendente quando possibile
    """
    title: str = dspy.InputField()
    description: str = dspy.InputField()
    context: str = dspy.InputField(desc="Contesto aggiuntivo dal board")
    
    subtasks: list[dict] = dspy.OutputField(
        desc="Lista di {title: str, description: str, effort: str}"
    )
    dependencies: list[tuple[int, int]] = dspy.OutputField(
        desc="Coppie (subtask_idx, depends_on_idx)"
    )


class DailySummary(dspy.Signature):
    """Genera un daily standup summary per l'utente.
    
    Focus su:
    - Cosa è urgente oggi
    - Cosa blocca il progresso
    - Quick wins disponibili
    """
    in_progress: list[dict] = dspy.InputField(desc="Ticket in lavorazione")
    blocked: list[dict] = dspy.InputField(desc="Ticket bloccati")
    due_soon: list[dict] = dspy.InputField(desc="Ticket con deadline vicina")
    recently_completed: list[dict] = dspy.InputField(desc="Completati di recente")
    
    greeting: str = dspy.OutputField(desc="Saluto personalizzato")
    focus_today: list[str] = dspy.OutputField(desc="Top 3 priorità per oggi")
    blockers: list[str] = dspy.OutputField(desc="Blocchi da risolvere")
    wins: list[str] = dspy.OutputField(desc="Quick wins suggeriti")


class SemanticSearch(dspy.Signature):
    """Trova ticket correlati usando semantic similarity."""
    query: str = dspy.InputField(desc="Query di ricerca")
    candidates: list[dict] = dspy.InputField(desc="Ticket candidati con embeddings")
    
    relevant_ids: list[str] = dspy.OutputField(desc="IDs dei ticket rilevanti")
    explanations: dict[str, str] = dspy.OutputField(desc="Perché ogni ticket è rilevante")


class ActionDecider(dspy.Signature):
    """Decide quale azione eseguire basandosi sul messaggio utente.
    
    Actions disponibili:
    - create_ticket: Crea nuovo ticket
    - update_ticket: Modifica ticket esistente
    - move_ticket: Sposta ticket tra colonne
    - search_tickets: Cerca ticket
    - summarize: Genera summary
    - none: Rispondi senza azione
    """
    user_message: str = dspy.InputField()
    current_context: dict = dspy.InputField(desc="Stato attuale del board")
    
    action: str = dspy.OutputField(desc="Nome dell'azione da eseguire")
    params: dict = dspy.OutputField(desc="Parametri per l'azione")
    response: str = dspy.OutputField(desc="Messaggio da mostrare all'utente")
```

### Main Agent Module

```python
class KanbanAgent(dspy.Module):
    """Agente principale per la gestione del kanban board."""
    
    def __init__(self, lm: dspy.LM = None):
        super().__init__()
        self.lm = lm or dspy.Claude(model="claude-sonnet-4-20250514")
        
        # Sub-modules
        self.triage = dspy.ChainOfThought(TriageTicket)
        self.decompose = dspy.ChainOfThought(DecomposeTask)
        self.summarize = dspy.Predict(DailySummary)
        self.decide = dspy.ChainOfThought(ActionDecider)
        
    def process_message(self, message: str, context: dict) -> dict:
        """Processa un messaggio utente e decide l'azione."""
        with dspy.context(lm=self.lm):
            result = self.decide(
                user_message=message,
                current_context=context
            )
        return {
            "action": result.action,
            "params": result.params,
            "response": result.response,
        }
    
    def auto_triage(self, ticket: dict, existing_labels: list[str]) -> dict:
        """Auto-assegna metadati a un ticket."""
        with dspy.context(lm=self.lm):
            result = self.triage(
                title=ticket["title"],
                description=ticket.get("description", ""),
                existing_labels=existing_labels,
            )
        return {
            "priority": result.priority,
            "labels": result.labels,
            "effort": result.effort_estimate,
            "reasoning": result.reasoning,
        }
```

## API Endpoints

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Kanban AI Agent")

class TriageRequest(BaseModel):
    ticket_id: str
    title: str
    description: str = ""

class TriageResponse(BaseModel):
    priority: str
    labels: list[str]
    effort: str
    reasoning: str

@app.post("/api/triage", response_model=TriageResponse)
async def triage_ticket(req: TriageRequest):
    """Auto-triage un ticket."""
    existing_labels = await get_existing_labels()
    result = agent.auto_triage(
        {"title": req.title, "description": req.description},
        existing_labels
    )
    return TriageResponse(**result)

@app.post("/api/chat")
async def chat(message: str, context: dict = None):
    """Chat con l'agente AI."""
    result = agent.process_message(message, context or {})
    
    # Esegui l'azione se necessario
    if result["action"] != "none":
        await execute_action(result["action"], result["params"])
    
    return result

@app.post("/api/decompose")
async def decompose_task(ticket_id: str):
    """Scomponi un task in subtask."""
    ticket = await get_ticket(ticket_id)
    context = await get_board_context()
    result = agent.decompose(
        title=ticket["title"],
        description=ticket["description"],
        context=str(context)
    )
    return result

@app.get("/api/daily-summary")
async def daily_summary():
    """Genera il daily summary."""
    tickets = await get_all_tickets()
    result = agent.summarize(
        in_progress=[t for t in tickets if t["status"] == "in_progress"],
        blocked=[t for t in tickets if t.get("blocked")],
        due_soon=[t for t in tickets if is_due_soon(t)],
        recently_completed=[t for t in tickets if recently_completed(t)]
    )
    return result
```

## ChromaDB Setup

```python
import chromadb
from chromadb.config import Settings

def get_chroma_client():
    return chromadb.PersistentClient(
        path="./data/chroma",
        settings=Settings(anonymized_telemetry=False)
    )

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="tickets",
        metadata={"hnsw:space": "cosine"}
    )

async def add_ticket_embedding(ticket: dict):
    """Aggiungi embedding per un ticket."""
    collection = get_collection()
    text = f"{ticket['title']}\n{ticket.get('description', '')}"
    collection.add(
        ids=[ticket["id"]],
        documents=[text],
        metadatas=[{"status": ticket["status"], "priority": ticket.get("priority")}]
    )

async def search_similar(query: str, n_results: int = 5):
    """Cerca ticket simili."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results
```

## Configuration

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str
    openai_api_key: str | None = None
    default_model: str = "claude-sonnet-4-20250514"
    
    # Database
    sqlite_path: str = "./data/kanban.db"
    chroma_path: str = "./data/chroma"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Testing Guidelines

```python
import dspy
import pytest

@pytest.fixture
def agent():
    # Usa un LM di test o mock
    lm = dspy.Claude(model="claude-sonnet-4-20250514")
    return KanbanAgent(lm=lm)

def test_triage_assigns_priority(agent):
    result = agent.auto_triage(
        {"title": "URGENT: Server down", "description": "Production server not responding"},
        existing_labels=["bug", "feature", "urgent"]
    )
    assert result["priority"] in ["high", "critical"]
    assert "urgent" in result["labels"] or "bug" in result["labels"]

def test_decompose_creates_subtasks(agent):
    result = agent.decompose(
        title="Implement user authentication",
        description="Add login, logout, password reset",
        context=""
    )
    assert len(result.subtasks) >= 3
```

## Do's and Don'ts

✅ **DO:**
- Usa `dspy.context()` per configurare il LM per blocco
- Implementa retry con backoff per API calls
- Logga tutte le interazioni per debugging
- Valida input/output con Pydantic
- Usa async per operazioni I/O bound

❌ **DON'T:**
- Non hardcodare API keys
- Non dimenticare error handling per LLM failures
- Non fare chiamate LLM sincrone nel main thread
- Non salvare dati sensibili negli embeddings
- Non ignorare rate limits delle API

## Resources

- [DSPy Documentation](https://dspy.ai)
- [FastAPI](https://fastapi.tiangolo.com)
- [ChromaDB](https://docs.trychroma.com)
- [Anthropic API](https://docs.anthropic.com)
