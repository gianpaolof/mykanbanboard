# TASK LIST - Kanban AI Phase 4 (Advanced DSPy)

> Completa le task in ordine. Marca [x] quando finito.

---

## TASK-056: DSPy Assertions per TriageModule

**File da modificare**: `services/agent/src/agent/modules.py`

**Cosa fare**:
1. Importa `dspy.Suggest` e `dspy.Assert`
2. Nel metodo `forward` di `TriageModule`, aggiungi validazioni:
   - `dspy.Suggest(priority in ['low', 'medium', 'high', 'critical'], "Priority must be valid")`
   - `dspy.Suggest(effort in ['xs', 's', 'm', 'l', 'xl'], "Effort must be valid")`
   - `dspy.Suggest(len(labels) <= 5, "Max 5 labels allowed")`
3. Wrap il modulo con `dspy.assert_transform_module` per attivare le assertions

**Pattern da seguire**:
```python
class TriageModuleWithAssertions(dspy.Module):
    def __init__(self):
        super().__init__()
        self.triage = dspy.ChainOfThought(TriageSignature)

    def forward(self, title, description):
        result = self.triage(title=title, description=description)
        dspy.Suggest(
            result.priority in ['low', 'medium', 'high', 'critical'],
            f"Priority '{result.priority}' is not valid"
        )
        return result
```

- [x] **TASK-056**: Aggiungere DSPy Assertions a TriageModule

---

## TASK-057: LLM-as-Judge per Quality Evaluation

**File da creare**: `services/agent/src/agent/judge.py`

**Cosa fare**:
1. Crea signature `JudgeTicketQuality`:
   - Input: `ticket_title, ticket_description, priority, effort, labels`
   - Output: `clarity_score (0-10), completeness_score (0-10), actionability_score (0-10), feedback`
2. Crea modulo `TicketQualityJudge` che usa `dspy.ChainOfThought`
3. Aggiungi metodo `evaluate_ticket(ticket_dict) -> dict` che ritorna scores e feedback

**Pattern**:
```python
class JudgeTicketQuality(dspy.Signature):
    """Evaluate the quality of a Kanban ticket."""
    ticket_title: str = dspy.InputField(desc="Title of the ticket")
    ticket_description: str = dspy.InputField(desc="Description of the ticket")
    priority: str = dspy.InputField(desc="Assigned priority")
    effort: str = dspy.InputField(desc="Effort estimate")
    labels: str = dspy.InputField(desc="Comma-separated labels")

    clarity_score: int = dspy.OutputField(desc="Clarity score 0-10")
    completeness_score: int = dspy.OutputField(desc="Completeness score 0-10")
    actionability_score: int = dspy.OutputField(desc="Actionability score 0-10")
    feedback: str = dspy.OutputField(desc="Improvement suggestions")


class TicketQualityJudge(dspy.Module):
    def __init__(self):
        super().__init__()
        self.judge = dspy.ChainOfThought(JudgeTicketQuality)

    def forward(self, ticket_title, ticket_description, priority, effort, labels):
        return self.judge(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            priority=priority,
            effort=effort,
            labels=labels
        )
```

- [x] **TASK-057**: Creare LLM-as-Judge TicketQualityJudge

---

## TASK-058: Endpoint /api/agent/judge

**File da modificare**: `services/agent/src/api/routes.py`

**Cosa fare**:
1. Aggiungi endpoint POST `/api/agent/judge`
2. Request body: `{"title": str, "description": str, "priority": str, "effort": str, "labels": list[str]}`
3. Response: `{"clarity_score": int, "completeness_score": int, "actionability_score": int, "feedback": str, "overall_score": float}`
4. `overall_score` = media dei 3 scores
5. Gestisci errori con try/except

**Pattern**:
```python
from pydantic import BaseModel

class JudgeRequest(BaseModel):
    title: str
    description: str
    priority: str
    effort: str
    labels: list[str]

class JudgeResponse(BaseModel):
    clarity_score: int
    completeness_score: int
    actionability_score: int
    feedback: str
    overall_score: float

@router.post("/agent/judge", response_model=JudgeResponse)
async def judge_ticket(request: JudgeRequest):
    judge = TicketQualityJudge()
    result = judge(
        ticket_title=request.title,
        ticket_description=request.description,
        priority=request.priority,
        effort=request.effort,
        labels=",".join(request.labels)
    )
    return JudgeResponse(
        clarity_score=int(result.clarity_score),
        completeness_score=int(result.completeness_score),
        actionability_score=int(result.actionability_score),
        feedback=result.feedback,
        overall_score=(int(result.clarity_score) + int(result.completeness_score) + int(result.actionability_score)) / 3
    )
```

- [x] **TASK-058**: Creare endpoint /api/agent/judge

---

## TASK-059: Multi-Hop Reasoning per Ticket Analysis

**File da creare**: `services/agent/src/agent/multihop.py`

**Cosa fare**:
1. Crea signature `AnalyzeContext` per primo hop (analizza ticket simili)
2. Crea signature `ExtractPatterns` per secondo hop (estrai pattern)
3. Crea signature `GenerateInsights` per terzo hop (genera insights)
4. Crea modulo `MultiHopTicketAnalyzer` che concatena i 3 hop
5. Metodo `analyze(ticket_title, ticket_description) -> dict` con `similar_tickets, patterns, insights, recommendations`

**Pattern**:
```python
class AnalyzeContext(dspy.Signature):
    """Analyze context from similar tickets."""
    ticket_title: str = dspy.InputField()
    ticket_description: str = dspy.InputField()
    similar_tickets: str = dspy.InputField(desc="JSON list of similar tickets")

    context_summary: str = dspy.OutputField(desc="Summary of relevant context")
    key_themes: str = dspy.OutputField(desc="Comma-separated key themes")


class ExtractPatterns(dspy.Signature):
    """Extract patterns from analyzed context."""
    context_summary: str = dspy.InputField()
    key_themes: str = dspy.InputField()

    patterns: str = dspy.OutputField(desc="Identified patterns as JSON list")
    dependencies: str = dspy.OutputField(desc="Potential dependencies")


class GenerateInsights(dspy.Signature):
    """Generate actionable insights."""
    patterns: str = dspy.InputField()
    dependencies: str = dspy.InputField()
    original_ticket: str = dspy.InputField()

    insights: str = dspy.OutputField(desc="Key insights as bullet points")
    recommendations: str = dspy.OutputField(desc="Recommended actions")
    estimated_complexity: str = dspy.OutputField(desc="low/medium/high")


class MultiHopTicketAnalyzer(dspy.Module):
    def __init__(self):
        super().__init__()
        self.hop1 = dspy.ChainOfThought(AnalyzeContext)
        self.hop2 = dspy.ChainOfThought(ExtractPatterns)
        self.hop3 = dspy.ChainOfThought(GenerateInsights)

    def forward(self, ticket_title, ticket_description, similar_tickets="[]"):
        # Hop 1: Analyze context
        ctx = self.hop1(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            similar_tickets=similar_tickets
        )
        # Hop 2: Extract patterns
        patterns = self.hop2(
            context_summary=ctx.context_summary,
            key_themes=ctx.key_themes
        )
        # Hop 3: Generate insights
        insights = self.hop3(
            patterns=patterns.patterns,
            dependencies=patterns.dependencies,
            original_ticket=f"{ticket_title}: {ticket_description}"
        )
        return {
            "context_summary": ctx.context_summary,
            "patterns": patterns.patterns,
            "insights": insights.insights,
            "recommendations": insights.recommendations,
            "complexity": insights.estimated_complexity
        }
```

- [x] **TASK-059**: Creare MultiHopTicketAnalyzer

---

## TASK-060: Endpoint /api/agent/analyze

**File da modificare**: `services/agent/src/api/routes.py`

**Cosa fare**:
1. Aggiungi endpoint POST `/api/agent/analyze`
2. Request: `{"title": str, "description": str}`
3. Response: `{"context_summary": str, "patterns": list, "insights": str, "recommendations": str, "complexity": str}`
4. Internamente cerca ticket simili via ChromaDB (se disponibile) o passa lista vuota
5. Timeout 60 secondi per query complesse

- [x] **TASK-060**: Creare endpoint /api/agent/analyze

---

## TASK-061: Best-of-N Selection per Decompose

**File da modificare**: `services/agent/src/agent/modules.py`

**Cosa fare**:
1. Crea classe `BestOfNDecompose` che genera N decomposizioni candidate
2. Definisci reward function `score_decomposition(subtasks)`:
   - +2 punti per ogni subtask con title e description
   - +1 punto se effort è valido (xs/s/m/l/xl)
   - -1 punto per subtask troppo vaghi (< 10 chars)
   - -2 punti se > 7 subtasks
3. Genera 3 candidate decomposizioni, ritorna quella con score più alto

**Pattern**:
```python
def score_decomposition(subtasks: list[dict]) -> float:
    score = 0.0
    for task in subtasks:
        if task.get("title") and task.get("description"):
            score += 2
        if task.get("effort") in ["xs", "s", "m", "l", "xl"]:
            score += 1
        if len(task.get("title", "")) < 10:
            score -= 1
    if len(subtasks) > 7:
        score -= 2
    return score


class BestOfNDecompose(dspy.Module):
    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.n_candidates = n_candidates
        self.decompose = dspy.ChainOfThought(DecomposeSignature)

    def forward(self, title, description):
        candidates = []
        for _ in range(self.n_candidates):
            result = self.decompose(title=title, description=description)
            subtasks = parse_subtasks(result.subtasks)
            score = score_decomposition(subtasks)
            candidates.append((score, result, subtasks))

        # Return best
        best = max(candidates, key=lambda x: x[0])
        return {"subtasks": best[2], "score": best[0]}
```

- [x] **TASK-061**: Implementare Best-of-N Selection per Decompose

---

## TASK-062: Caching Layer per DSPy

**File da creare**: `services/agent/src/agent/cache.py`

**Cosa fare**:
1. Crea classe `DSPyCache` con:
   - In-memory LRU cache per hot queries (max 100 items)
   - Disk cache opzionale via `diskcache` per persistenza
   - Metodo `get_or_compute(key, compute_fn)`
   - Metodo `invalidate(pattern)` per invalidare cache
2. Cache key = hash di (module_name, input_params)
3. TTL configurabile (default 1 ora)

**Pattern**:
```python
import hashlib
import json
from functools import lru_cache
from typing import Any, Callable
from datetime import datetime, timedelta

class DSPyCache:
    def __init__(self, max_memory_items: int = 100, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._memory_cache: dict[str, tuple[Any, datetime]] = {}
        self.max_items = max_memory_items

    def _make_key(self, module_name: str, **kwargs) -> str:
        data = json.dumps({"module": module_name, **kwargs}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        if key in self._memory_cache:
            value, timestamp = self._memory_cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                return value
            del self._memory_cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if len(self._memory_cache) >= self.max_items:
            # Remove oldest
            oldest = min(self._memory_cache.items(), key=lambda x: x[1][1])
            del self._memory_cache[oldest[0]]
        self._memory_cache[key] = (value, datetime.now())

    def get_or_compute(self, module_name: str, compute_fn: Callable, **kwargs) -> Any:
        key = self._make_key(module_name, **kwargs)
        cached = self.get(key)
        if cached is not None:
            return cached
        result = compute_fn()
        self.set(key, result)
        return result

    def invalidate(self, pattern: str = "") -> int:
        if not pattern:
            count = len(self._memory_cache)
            self._memory_cache.clear()
            return count
        keys_to_delete = [k for k in self._memory_cache if pattern in k]
        for k in keys_to_delete:
            del self._memory_cache[k]
        return len(keys_to_delete)


# Global cache instance
dspy_cache = DSPyCache()
```

- [x] **TASK-062**: Creare DSPyCache con LRU e TTL

---

## TASK-063: Analytics e Logging per Agent

**File da creare**: `services/agent/src/agent/analytics.py`

**Cosa fare**:
1. Crea classe `AgentAnalytics` con SQLite backend
2. Logga ogni chiamata: `module_name, input_hash, output_hash, latency_ms, tokens_used, timestamp, success`
3. Metodi:
   - `log_call(module, input, output, latency, tokens, success)`
   - `get_stats(period="day")` -> `{total_calls, avg_latency, success_rate, tokens_used}`
   - `get_module_stats(module_name)` -> stats per modulo
   - `get_hourly_breakdown()` -> lista di stats per ora

**Pattern**:
```python
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class AgentAnalytics:
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    input_hash TEXT,
                    output_hash TEXT,
                    latency_ms INTEGER,
                    tokens_used INTEGER,
                    success BOOLEAN
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_calls(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_module ON agent_calls(module_name)")

    def log_call(self, module_name: str, input_data: dict, output_data: dict,
                 latency_ms: int, tokens_used: int = 0, success: bool = True):
        input_hash = hashlib.md5(json.dumps(input_data, sort_keys=True).encode()).hexdigest()[:16]
        output_hash = hashlib.md5(json.dumps(output_data, sort_keys=True).encode()).hexdigest()[:16]

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO agent_calls (timestamp, module_name, input_hash, output_hash, latency_ms, tokens_used, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), module_name, input_hash, output_hash, latency_ms, tokens_used, success)
            )

    def get_stats(self, period: str = "day") -> dict:
        if period == "day":
            since = datetime.now() - timedelta(days=1)
        elif period == "week":
            since = datetime.now() - timedelta(weeks=1)
        else:
            since = datetime.now() - timedelta(hours=1)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    SUM(tokens_used) as total_tokens
                FROM agent_calls WHERE timestamp > ?
            """, (since.isoformat(),)).fetchone()

        return {
            "total_calls": row[0] or 0,
            "avg_latency_ms": round(row[1] or 0, 2),
            "success_rate": round(row[2] or 0, 2),
            "total_tokens": row[3] or 0
        }


# Global instance
analytics = AgentAnalytics()
```

- [x] **TASK-063**: Creare AgentAnalytics con SQLite

---

## TASK-064: Endpoint /api/agent/stats

**File da modificare**: `services/agent/src/api/routes.py`

**Cosa fare**:
1. GET `/api/agent/stats` -> stats generali (default last 24h)
2. GET `/api/agent/stats?period=week` -> stats ultima settimana
3. GET `/api/agent/stats?period=hour` -> stats ultima ora
4. Response: `{"total_calls": int, "avg_latency_ms": float, "success_rate": float, "total_tokens": int, "period": str}`

**Pattern**:
```python
from fastapi import Query

@router.get("/agent/stats")
async def get_agent_stats(period: str = Query("day", regex="^(hour|day|week)$")):
    stats = analytics.get_stats(period=period)
    return {**stats, "period": period}
```

- [x] **TASK-064**: Creare endpoint /api/agent/stats

---

## TASK-065: Proactive Suggester

**File da creare**: `services/agent/src/agent/suggester.py`

**Cosa fare**:
1. Crea signature `AnalyzeBoardState` per analisi board
2. Crea modulo `ProactiveSuggester`:
   - Input: board_state (columns, tickets per column, labels, recent activity)
   - Output: max 5 suggestions con type, message, action, priority
3. Tipi di suggestion:
   - `stale_ticket`: ticket in stesso stato > 7 giorni
   - `overloaded_column`: colonna con > 10 ticket
   - `missing_labels`: ticket senza labels
   - `similar_tickets`: ticket potenzialmente duplicati
   - `effort_mismatch`: effort alto in colonna done suggerisce split

**Pattern**:
```python
class AnalyzeBoardState(dspy.Signature):
    """Analyze Kanban board state and suggest improvements."""
    board_state: str = dspy.InputField(desc="JSON board state with columns and tickets")

    suggestions: str = dspy.OutputField(desc="JSON array of {type, message, action, priority}")


class ProactiveSuggester(dspy.Module):
    def __init__(self):
        super().__init__()
        self.analyzer = dspy.ChainOfThought(AnalyzeBoardState)

    def forward(self, board_state: dict) -> list[dict]:
        result = self.analyzer(board_state=json.dumps(board_state))
        try:
            suggestions = json.loads(result.suggestions)
            return suggestions[:5]  # Max 5
        except json.JSONDecodeError:
            return []

    def get_suggestions(self, columns: list[dict], tickets: list[dict]) -> list[dict]:
        board_state = {
            "columns": columns,
            "tickets": tickets,
            "ticket_count": len(tickets),
            "tickets_per_column": {col["id"]: sum(1 for t in tickets if t.get("column_id") == col["id"]) for col in columns}
        }
        return self.forward(board_state)
```

- [x] **TASK-065**: Creare ProactiveSuggester

---

## TASK-066: UI Agent Stats Dashboard

**File da creare**: `apps/desktop/src/components/agent-stats.tsx`

**Cosa fare**:
1. Crea componente `AgentStatsPanel` che mostra statistiche agent
2. Fetch da `GET /api/agent/stats` con periodo selezionabile (hour/day/week)
3. Mostra: total_calls, avg_latency_ms, success_rate (%), total_tokens
4. Aggiungi toggle per periodo
5. Usa stile glassmorphism coerente con il design system
6. Aggiungi icone per ogni metrica (Clock, CheckCircle, Zap, etc.)

**Dove integrare**: Sidebar o sezione dedicata nel layout principale

- [x] **TASK-066**: Creare UI Agent Stats Dashboard

---

## TASK-067: UI Ticket Quality Badge

**File da modificare**: `apps/desktop/src/components/ticket-card.tsx` o `ticket-detail.tsx`

**Cosa fare**:
1. Aggiungi bottone/icona "Quality" nel ticket detail
2. Al click, chiama `POST /api/agent/judge` con i dati del ticket
3. Mostra badge colorato con overall_score (verde >7, giallo 5-7, rosso <5)
4. Tooltip o popover con breakdown: clarity, completeness, actionability
5. Mostra feedback come suggerimento miglioramento
6. Gestisci loading state mentre l'API risponde

- [x] **TASK-067**: Creare UI Ticket Quality Badge

---

## TASK-068: UI Multi-hop Analysis Panel

**File da creare**: `apps/desktop/src/components/ticket-analysis.tsx`

**Cosa fare**:
1. Crea componente `TicketAnalysisPanel`
2. Bottone "Analyze" nel ticket detail che chiama `POST /api/agent/analyze`
3. Mostra risultati in panel espandibile:
   - Context summary
   - Patterns identificati (come chips/tags)
   - Insights (bullet list)
   - Recommendations (action items)
   - Complexity badge (low/medium/high con colori)
4. Loading skeleton durante l'analisi (può durare fino a 60s)
5. Possibilità di chiudere/nascondere il panel

- [x] **TASK-068**: Creare UI Multi-hop Analysis Panel

---

## TASK-069: UI Proactive Suggestions Widget

**File da creare**: `apps/desktop/src/components/suggestions-widget.tsx`

**Cosa fare**:
1. Crea widget `SuggestionsWidget` per la sidebar
2. Chiama `ProactiveSuggester.quick_analysis()` (lato client o nuovo endpoint)
3. Mostra lista di max 5 suggestions con:
   - Icona per tipo (stale, overloaded, missing_labels, etc.)
   - Priority badge (high=rosso, medium=giallo, low=grigio)
   - Message testuale
   - Action button se applicabile
4. Refresh automatico quando cambia lo stato della board
5. Possibilità di dismissare suggestions

**Nuovo endpoint da creare**: `GET /api/agent/suggestions` che usa `suggester.quick_analysis()`

- [x] **TASK-069**: Creare UI Proactive Suggestions Widget

---

## TASK-070: Endpoint /api/agent/suggestions

**File da modificare**: `services/agent/src/api/routes.py`

**Cosa fare**:
1. Crea endpoint `POST /api/agent/suggestions`
2. Request: `{"columns": list[dict], "tickets": list[dict]}`
3. Response: `{"suggestions": list[{type, message, action, priority}]}`
4. Usa `suggester.quick_analysis()` per risposta veloce senza LLM
5. Opzionale: parametro `?deep=true` per usare `suggester.get_suggestions()` con LLM

- [x] **TASK-070**: Creare endpoint /api/agent/suggestions

---

## TASK-071: Comprehensive Manual Test Plan

**File da creare/aggiornare**: `docs/TEST_PLAN.md`

**Cosa fare**:
1. Crea documento con test manuali per TUTTE le feature dell'app
2. Organizza per area funzionale:
   - **Board Management**: CRUD board, columns, drag & drop
   - **Ticket Management**: CRUD ticket, labels, priority, effort, due date
   - **Subtasks/Checklists**: Aggiungi, completa, elimina subtask
   - **Views**: Board, List, Timeline, Calendar
   - **AI Agent - Triage**: POST /api/triage
   - **AI Agent - Decompose**: POST /api/decompose
   - **AI Agent - Chat**: POST /api/chat
   - **AI Agent - Search**: POST /api/search (semantic)
   - **AI Agent - Daily Summary**: GET /api/daily-summary
   - **AI Agent - Parse Rule**: POST /api/parse-rule
   - **AI Agent - Judge**: POST /api/agent/judge
   - **AI Agent - Analyze**: POST /api/agent/analyze
   - **AI Agent - Stats**: GET /api/agent/stats (+ /modules, /hourly, /errors)
   - **AI Agent - Suggestions**: POST /api/agent/suggestions
   - **Automation Rules**: Crea, attiva, disattiva regole
   - **Command Palette**: ⌘K shortcuts
   - **Keyboard Shortcuts**: tutti i keybindings
3. Per ogni test: descrizione, steps, expected result, status checkbox

- [x] **TASK-071**: Creare Comprehensive Manual Test Plan

---

## Progress

| Task | Status |
|------|--------|
| TASK-056 | ✅ |
| TASK-057 | ✅ |
| TASK-058 | ✅ |
| TASK-059 | ✅ |
| TASK-060 | ✅ |
| TASK-061 | ✅ |
| TASK-062 | ✅ |
| TASK-063 | ✅ |
| TASK-064 | ✅ |
| TASK-065 | ✅ |
| TASK-066 | ✅ |
| TASK-067 | ✅ |
| TASK-068 | ✅ |
| TASK-069 | ✅ |
| TASK-070 | ✅ |
| TASK-071 | ✅ |
