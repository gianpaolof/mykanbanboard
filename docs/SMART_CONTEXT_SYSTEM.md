# Piano: Smart Context System per Kanban AI

## Obiettivo

Creare un sistema di **contesto intelligente e dinamico** che fornisca all'AI esattamente le informazioni giuste al momento giusto, senza sprecare token su contesto irrilevante.

---

## Analisi Stato Attuale (Problemi Critici)

### Gap Identificati dagli Agenti

| Modulo | Cosa Riceve Ora | Cosa Dovrebbe Ricevere |
|--------|-----------------|------------------------|
| **TriageModule** | title, description, existing_labels | + project context, similar tickets, recent triages |
| **DecomposeModule** | title, description, context="" | + tech stack, related tickets, patterns |
| **DailySummary** | **LISTE VUOTE** | in_progress, blocked, due_soon tickets |
| **MultiHopAnalyzer** | similar_tickets="[]" **HARDCODED** | ChromaDB search results |
| **ActionDecider** | message, context={} | + board state, conversation history |

### Bug Critici Trovati

1. **`routes.py:668`** - `similar_tickets="[]"` hardcoded - MultiHop non funziona
2. **`routes.py:454-458`** - DailySummary riceve liste vuote - inutile
3. **No sync SQLite → ChromaDB** - ticket creati non sono ricercabili
4. **Cache esistente ma non usata** - DSPyCache mai chiamata in routes

---

## Architettura Proposta

### Context Layers (4 livelli)

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: GLOBAL PROJECT CONTEXT                            │
│  • Project name, description                                │
│  • Tech stack                                               │
│  • Conventions (labels, priorities)                         │
│  • TTL: 1 ora (raramente cambia)                           │
│  • Storage: Zustand + SQLite                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: FEATURE/MODULE CONTEXT                            │
│  • Domain detection (auth, ui, api, database, etc.)         │
│  • Related components                                       │
│  • Patterns for this domain                                 │
│  • TTL: 15 minuti                                          │
│  • Storage: Cache in-memory                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: RELATED TICKETS CONTEXT (Dynamic Retrieval)       │
│  • ChromaDB semantic search                                 │
│  • Top 3-5 similar tickets                                  │
│  • Their priority, labels, resolution                       │
│  • NO CACHE - sempre dinamico                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: CURRENT TICKET CONTEXT                            │
│  • Full ticket details                                      │
│  • Status, column, subtasks                                 │
│  • NO CACHE                                                 │
└─────────────────────────────────────────────────────────────┘
```

### Token Budget Management

```python
TokenBudget:
  total_budget: 4000 tokens
  reserved_for_response: 1000 tokens
  available: 3000 tokens

  Allocation:
    - Layer 1 (Global):   15% = ~450 tokens
    - Layer 2 (Feature):  20% = ~600 tokens
    - Layer 3 (Related):  35% = ~1050 tokens
    - Layer 4 (Current):  30% = ~900 tokens

  Overflow Strategy:
    1. Truncate layer 3 (reduce similar tickets)
    2. Summarize layer 2
    3. Never truncate layer 4 (current ticket is most important)
```

### Multi-Hop con Retrieval Dinamico

```
HOP 1: Context Gathering
  Input: ticket_title, ticket_description
  Action: ChromaDB search → top 5 similar
  Output: context_summary, key_themes, NUOVE QUERY

HOP 2: Deep Analysis
  Input: hop1 output + EXECUTE nuove query
  Action: Retrieve more specific context
  Output: dependencies, risks, complexity

HOP 3: Actionable Insights
  Input: hop2 output
  Output: priority_recommendation, effort, action_items
```

---

## Files da Creare/Modificare

### Python Agent (services/agent/src/)

| File | Azione | Descrizione |
|------|--------|-------------|
| `agent/context_types.py` | **NEW** | Dataclass per GlobalContext, FeatureContext, RelatedContext, CurrentContext, TokenBudget |
| `agent/context_manager.py` | **NEW** | ContextManager con layer assembly, budget management, caching |
| `agent/retriever.py` | **NEW** | ChromaRetriever che estende dspy.Retrieve |
| `agent/context_modules.py` | **NEW** | ContextAwareTriageModule, ContextAwareDecomposeModule |
| `agent/dynamic_multihop.py` | **NEW** | DynamicMultiHopAnalyzer con retrieval ad ogni hop |
| `db/layered_chroma.py` | **NEW** | Multi-collection ChromaDB (tickets, features, decisions, glossary) |
| `api/routes.py` | **MODIFY** | Integrare ContextManager in tutti gli endpoint |
| `api/models.py` | **MODIFY** | Aggiungere ProjectContext ai request models |

### Rust Backend (apps/desktop/src-tauri/)

| File | Azione | Descrizione |
|------|--------|-------------|
| `db/mod.rs` | **MODIFY** | Migration per project_context in boards table |
| `models.rs` | **MODIFY** | Struct ProjectContext |
| `commands.rs` | **MODIFY** | CRUD project context |
| `agent.rs` | **MODIFY** | Passare project_context nelle richieste HTTP |

### React Frontend (apps/desktop/src/)

| File | Azione | Descrizione |
|------|--------|-------------|
| `types/project.ts` | **NEW** | TypeScript types per ProjectContext |
| `stores/projectStore.ts` | **NEW** | Zustand store per project context |
| `components/settings/ProjectSettings.tsx` | **NEW** | Main settings component |
| `components/settings/ProjectWizard.tsx` | **NEW** | First-time setup wizard |
| `components/settings/project/*.tsx` | **NEW** | TechStackInput, ModulesList, LabelConventions, PriorityRules, ContextPreview |
| `components/settings/SettingsModal.tsx` | **MODIFY** | Aggiungere tab "Project" |
| `lib/tauri.ts` | **MODIFY** | API methods per project context |

---

## Flusso Dati Completo

```
USER: Crea ticket "Fix NFC timeout su Samsung"

FRONTEND (React)
│
├── boardStore.addTicket()
│   └── Optimistic update UI
│
├── api.tickets.createTicket(ticket)
│   └── Include boardId
│
└── SE AI triage abilitato:
    └── api.agent.triage(ticketId, title, desc, projectContext)
        └── projectStore.context passato

RUST (Tauri)
│
├── INSERT ticket in SQLite
│
└── POST localhost:8765/api/triage
    └── Body include project_context

PYTHON (FastAPI)
│
├── ContextManager.assemble_context()
│   │
│   ├── Layer 1: get_global_context()
│   │   └── Cache hit (1h TTL) o load da request
│   │
│   ├── Layer 2: get_feature_context()
│   │   └── detect_domain("Fix NFC timeout...") → "hardware"
│   │   └── get_feature_context_for_domain("hardware")
│   │
│   ├── Layer 3: get_related_context()
│   │   └── ChromaDB.search("Fix NFC timeout Samsung")
│   │   └── Return top 5 similar tickets with scores
│   │
│   └── Layer 4: get_current_context()
│       └── Current ticket data
│
├── apply_token_budget()
│   └── Truncate if over 3000 tokens
│
└── ContextAwareTriageModule.forward()
    │
    ├── INPUT:
    │   • title: "Fix NFC timeout su Samsung"
    │   • description: ...
    │   • project_context: "Mobile app Flutter, NFC, ..."
    │   • similar_tickets: "[T-45: NFC fails on Pixel, T-23: ...]"
    │   • feature_context: "Hardware domain, NFC patterns"
    │   • existing_labels: ["bug", "nfc", "android", "ios"]
    │
    ├── DSPy ChainOfThought
    │
    └── OUTPUT:
        • priority: "high" (progetto dice NFC = high)
        • labels: ["nfc", "android", "bug"]
        • effort: "m" (basato su ticket simili)
        • reasoning: "NFC issues are high priority per project rules..."

RETURN TO FRONTEND
│
└── Ticket aggiornato con triage AI
```

---

## Implementazione Dettagliata

### Phase 1: Python Context System (Foundation)

#### 1.1 context_types.py

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class ContextLayer(Enum):
    GLOBAL = "global"
    FEATURE = "feature"
    RELATED = "related"
    CURRENT = "current"

@dataclass
class TokenBudget:
    total_budget: int = 4000
    reserved_for_response: int = 1000
    layer_budgets: dict[ContextLayer, float] = field(default_factory=lambda: {
        ContextLayer.GLOBAL: 0.15,
        ContextLayer.FEATURE: 0.20,
        ContextLayer.RELATED: 0.35,
        ContextLayer.CURRENT: 0.30,
    })

    @property
    def available(self) -> int:
        return self.total_budget - self.reserved_for_response

    def get_layer_budget(self, layer: ContextLayer) -> int:
        return int(self.available * self.layer_budgets[layer])

@dataclass
class LabelConvention:
    label_name: str
    description: str
    when_to_use: str

@dataclass
class PriorityRule:
    condition: str
    priority: str
    reasoning: str

@dataclass
class GlobalContext:
    project_name: str
    project_description: str
    tech_stack: list[str]
    modules: list[str]
    label_conventions: list[LabelConvention]
    priority_rules: list[PriorityRule]

    def to_text(self, max_tokens: int = 450) -> str:
        text = f"""# Project: {self.project_name}
{self.project_description}

## Tech Stack
{', '.join(self.tech_stack)}

## Modules
{', '.join(self.modules)}

## Label Conventions
{chr(10).join(f"- {lc.label_name}: {lc.when_to_use}" for lc in self.label_conventions)}

## Priority Rules
{chr(10).join(f"- {pr.condition} → {pr.priority}" for pr in self.priority_rules)}
"""
        return self._truncate_to_tokens(text, max_tokens)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        # Rough estimation: 4 chars per token
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."

@dataclass
class FeatureContext:
    feature_name: str
    domain: str
    related_components: list[str]
    patterns: list[str]

    def to_text(self, max_tokens: int = 600) -> str:
        text = f"""## Domain: {self.domain}
Feature: {self.feature_name}

### Related Components
{', '.join(self.related_components)}

### Common Patterns
{chr(10).join(f"- {p}" for p in self.patterns)}
"""
        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text

@dataclass
class RelatedTicket:
    id: str
    title: str
    description: str
    priority: Optional[str]
    labels: list[str]
    column: str
    similarity_score: float

@dataclass
class RelatedContext:
    query: str
    tickets: list[RelatedTicket]
    total_found: int

    def to_text(self, max_tokens: int = 1050) -> str:
        if not self.tickets:
            return "No similar tickets found."

        lines = ["## Similar Tickets"]
        for t in self.tickets[:5]:  # Max 5
            labels_str = ", ".join(t.labels) if t.labels else "none"
            lines.append(
                f"- [{t.id}] {t.title} | priority: {t.priority or 'none'} | "
                f"labels: {labels_str} | column: {t.column} | score: {t.similarity_score:.2f}"
            )

        text = "\n".join(lines)
        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text

@dataclass
class CurrentTicketContext:
    ticket_id: str
    title: str
    description: str
    current_column: Optional[str] = None
    current_labels: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)

    def to_text(self, max_tokens: int = 900) -> str:
        text = f"""## Current Ticket
Title: {self.title}
Description: {self.description}
Column: {self.current_column or 'Not set'}
Labels: {', '.join(self.current_labels) if self.current_labels else 'None'}
"""
        if self.subtasks:
            text += f"\nSubtasks:\n{chr(10).join(f'- {s}' for s in self.subtasks)}"

        max_chars = max_tokens * 4
        return text[:max_chars] if len(text) > max_chars else text

@dataclass
class AssembledContext:
    global_ctx: GlobalContext
    feature_ctx: Optional[FeatureContext]
    related_ctx: RelatedContext
    current_ctx: CurrentTicketContext
    token_counts: dict[ContextLayer, int]
    total_tokens: int

    def to_full_text(self) -> str:
        parts = [
            self.global_ctx.to_text(self.token_counts.get(ContextLayer.GLOBAL, 450)),
        ]

        if self.feature_ctx:
            parts.append(self.feature_ctx.to_text(self.token_counts.get(ContextLayer.FEATURE, 600)))

        parts.append(self.related_ctx.to_text(self.token_counts.get(ContextLayer.RELATED, 1050)))
        parts.append(self.current_ctx.to_text(self.token_counts.get(ContextLayer.CURRENT, 900)))

        return "\n\n---\n\n".join(parts)
```

#### 1.2 context_manager.py

```python
from typing import Optional
import json
from .context_types import (
    TokenBudget, ContextLayer, GlobalContext, FeatureContext,
    RelatedContext, RelatedTicket, CurrentTicketContext, AssembledContext
)
from ..db.chroma import ChromaManager
from ..agent.cache import DSPyCache

# Domain detection keywords
DOMAIN_KEYWORDS = {
    "auth": ["login", "logout", "password", "authentication", "oauth", "jwt", "session", "token"],
    "ui": ["button", "modal", "component", "style", "css", "layout", "design", "responsive"],
    "api": ["endpoint", "rest", "graphql", "request", "response", "http", "fetch", "axios"],
    "database": ["query", "sql", "migration", "schema", "model", "orm", "table", "index"],
    "hardware": ["nfc", "bluetooth", "camera", "gps", "sensor", "device", "usb", "serial"],
    "performance": ["slow", "memory", "leak", "optimize", "cache", "latency", "timeout"],
    "security": ["vulnerability", "xss", "injection", "encryption", "certificate", "ssl"],
    "testing": ["test", "unit", "integration", "mock", "coverage", "jest", "pytest"],
}

def detect_domain(title: str, description: str) -> Optional[str]:
    """Detect the domain/feature area based on ticket content."""
    text = f"{title} {description}".lower()

    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[domain] = score

    if not scores:
        return None

    return max(scores, key=scores.get)

class ContextManager:
    def __init__(self, chroma: ChromaManager):
        self.chroma = chroma
        self.global_cache = DSPyCache(max_size=10, ttl_seconds=3600)  # 1 hour
        self.feature_cache = DSPyCache(max_size=50, ttl_seconds=900)  # 15 minutes

    def assemble_context(
        self,
        ticket_id: str,
        title: str,
        description: str,
        project_context: Optional[dict] = None,
        existing_labels: list[str] = None,
        budget: TokenBudget = None,
    ) -> AssembledContext:
        """Assemble all context layers with budget management."""
        if budget is None:
            budget = TokenBudget()

        # Layer 1: Global (from request or default)
        global_ctx = self._get_global_context(project_context)

        # Layer 2: Feature (auto-detected)
        domain = detect_domain(title, description)
        feature_ctx = self._get_feature_context(domain) if domain else None

        # Layer 3: Related (always dynamic via ChromaDB)
        related_ctx = self._get_related_context(
            query=f"{title} {description}",
            exclude_id=ticket_id
        )

        # Layer 4: Current
        current_ctx = CurrentTicketContext(
            ticket_id=ticket_id,
            title=title,
            description=description,
            current_labels=existing_labels or [],
        )

        # Calculate token counts
        token_counts = self._calculate_token_counts(
            global_ctx, feature_ctx, related_ctx, current_ctx, budget
        )

        total_tokens = sum(token_counts.values())

        return AssembledContext(
            global_ctx=global_ctx,
            feature_ctx=feature_ctx,
            related_ctx=related_ctx,
            current_ctx=current_ctx,
            token_counts=token_counts,
            total_tokens=total_tokens,
        )

    def _get_global_context(self, project_context: Optional[dict]) -> GlobalContext:
        """Get or create global context from project settings."""
        if not project_context:
            return GlobalContext(
                project_name="Unknown Project",
                project_description="No project context configured.",
                tech_stack=[],
                modules=[],
                label_conventions=[],
                priority_rules=[],
            )

        # Parse label conventions
        label_conventions = []
        for lc in project_context.get("label_conventions", []):
            if isinstance(lc, dict):
                label_conventions.append(LabelConvention(
                    label_name=lc.get("name", ""),
                    description=lc.get("description", ""),
                    when_to_use=lc.get("when_to_use", ""),
                ))

        # Parse priority rules
        priority_rules = []
        for pr in project_context.get("priority_rules", []):
            if isinstance(pr, dict):
                priority_rules.append(PriorityRule(
                    condition=pr.get("condition", ""),
                    priority=pr.get("priority", "medium"),
                    reasoning=pr.get("reasoning", ""),
                ))

        return GlobalContext(
            project_name=project_context.get("project_name", "Unknown"),
            project_description=project_context.get("description", ""),
            tech_stack=project_context.get("tech_stack", []),
            modules=project_context.get("modules", []),
            label_conventions=label_conventions,
            priority_rules=priority_rules,
        )

    def _get_feature_context(self, domain: str) -> Optional[FeatureContext]:
        """Get feature context for a detected domain."""
        # Check cache first
        cache_key = f"feature_{domain}"
        cached = self.feature_cache.get(cache_key)
        if cached:
            return cached

        # Domain-specific patterns (could be loaded from config)
        domain_patterns = {
            "auth": FeatureContext(
                feature_name="Authentication",
                domain="auth",
                related_components=["login", "session", "user"],
                patterns=[
                    "Check token expiration",
                    "Handle refresh flow",
                    "Secure password storage",
                ],
            ),
            "hardware": FeatureContext(
                feature_name="Hardware Integration",
                domain="hardware",
                related_components=["device", "driver", "firmware"],
                patterns=[
                    "Handle connection timeouts",
                    "Implement retry logic",
                    "Device-specific error handling",
                ],
            ),
            "ui": FeatureContext(
                feature_name="User Interface",
                domain="ui",
                related_components=["components", "styles", "layout"],
                patterns=[
                    "Follow design system",
                    "Ensure accessibility",
                    "Test responsive behavior",
                ],
            ),
            # Add more domains as needed
        }

        feature_ctx = domain_patterns.get(domain)
        if feature_ctx:
            self.feature_cache.set(cache_key, feature_ctx)

        return feature_ctx

    def _get_related_context(
        self,
        query: str,
        exclude_id: str,
        limit: int = 5
    ) -> RelatedContext:
        """Get related tickets from ChromaDB semantic search."""
        try:
            results = self.chroma.search(query, limit=limit + 1)  # +1 to exclude self

            tickets = []
            for r in results:
                if r.get("id") == exclude_id:
                    continue
                if len(tickets) >= limit:
                    break

                tickets.append(RelatedTicket(
                    id=r.get("id", ""),
                    title=r.get("title", ""),
                    description=r.get("description", "")[:200],  # Truncate
                    priority=r.get("metadata", {}).get("priority"),
                    labels=r.get("metadata", {}).get("labels", []),
                    column=r.get("metadata", {}).get("column", "Unknown"),
                    similarity_score=r.get("score", 0.0),
                ))

            return RelatedContext(
                query=query,
                tickets=tickets,
                total_found=len(results),
            )
        except Exception as e:
            # Return empty context on error
            return RelatedContext(query=query, tickets=[], total_found=0)

    def _calculate_token_counts(
        self,
        global_ctx: GlobalContext,
        feature_ctx: Optional[FeatureContext],
        related_ctx: RelatedContext,
        current_ctx: CurrentTicketContext,
        budget: TokenBudget,
    ) -> dict[ContextLayer, int]:
        """Calculate token allocation for each layer."""
        counts = {
            ContextLayer.GLOBAL: budget.get_layer_budget(ContextLayer.GLOBAL),
            ContextLayer.FEATURE: budget.get_layer_budget(ContextLayer.FEATURE) if feature_ctx else 0,
            ContextLayer.RELATED: budget.get_layer_budget(ContextLayer.RELATED),
            ContextLayer.CURRENT: budget.get_layer_budget(ContextLayer.CURRENT),
        }

        # Redistribute feature budget if no feature context
        if not feature_ctx:
            extra = budget.get_layer_budget(ContextLayer.FEATURE)
            counts[ContextLayer.RELATED] += extra // 2
            counts[ContextLayer.CURRENT] += extra // 2

        return counts
```

#### 1.3 context_modules.py

```python
import dspy
from typing import Literal, Optional
from .context_manager import ContextManager
from .context_types import TokenBudget

class ContextAwareTriageSignature(dspy.Signature):
    """Triage a ticket with full project context and semantic similarity."""

    title: str = dspy.InputField(desc="Ticket title")
    description: str = dspy.InputField(desc="Ticket description")
    project_context: str = dspy.InputField(desc="Project info: tech stack, conventions, priority rules")
    similar_tickets: str = dspy.InputField(desc="Similar tickets from semantic search with their priority/labels")
    feature_context: str = dspy.InputField(desc="Domain-specific patterns and related components")
    existing_labels: list[str] = dspy.InputField(desc="Available labels on the board")

    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField(
        desc="Priority based on project rules and similar tickets"
    )
    labels: list[str] = dspy.OutputField(
        desc="Labels from existing_labels that apply (max 3)"
    )
    effort_estimate: Literal["xs", "s", "m", "l", "xl"] = dspy.OutputField(
        desc="Effort estimate based on similar tickets"
    )
    reasoning: str = dspy.OutputField(
        desc="Brief explanation of triage decisions"
    )

class ContextAwareTriageModule(dspy.Module):
    """Triage module that uses assembled context from all layers."""

    def __init__(self, context_manager: ContextManager):
        super().__init__()
        self.ctx_mgr = context_manager
        self.triage = dspy.ChainOfThought(ContextAwareTriageSignature)

    def forward(
        self,
        ticket_id: str,
        title: str,
        description: str,
        project_context: Optional[dict] = None,
        existing_labels: list[str] = None,
    ):
        # Assemble all context layers
        assembled = self.ctx_mgr.assemble_context(
            ticket_id=ticket_id,
            title=title,
            description=description,
            project_context=project_context,
            existing_labels=existing_labels,
        )

        # Run triage with rich context
        result = self.triage(
            title=title,
            description=description,
            project_context=assembled.global_ctx.to_text(
                assembled.token_counts.get(ContextLayer.GLOBAL, 450)
            ),
            similar_tickets=assembled.related_ctx.to_text(
                assembled.token_counts.get(ContextLayer.RELATED, 1050)
            ),
            feature_context=(
                assembled.feature_ctx.to_text(
                    assembled.token_counts.get(ContextLayer.FEATURE, 600)
                ) if assembled.feature_ctx else "No specific domain detected."
            ),
            existing_labels=existing_labels or [],
        )

        # Validate labels are from existing set
        valid_labels = [l for l in result.labels if l in (existing_labels or [])]

        return dspy.Prediction(
            priority=result.priority,
            labels=valid_labels[:3],  # Max 3
            effort_estimate=result.effort_estimate,
            reasoning=result.reasoning,
            context_used={
                "total_tokens": assembled.total_tokens,
                "domain_detected": assembled.feature_ctx.domain if assembled.feature_ctx else None,
                "similar_tickets_found": len(assembled.related_ctx.tickets),
            },
        )

class ContextAwareDecomposeSignature(dspy.Signature):
    """Decompose a task with project awareness."""

    title: str = dspy.InputField(desc="Task title")
    description: str = dspy.InputField(desc="Task description")
    project_context: str = dspy.InputField(desc="Project tech stack and modules")
    similar_decompositions: str = dspy.InputField(desc="How similar tasks were decomposed")

    subtasks: list[dict] = dspy.OutputField(
        desc="List of subtasks with title, description, effort"
    )
    dependencies: list[str] = dspy.OutputField(
        desc="Dependencies between subtasks"
    )
    reasoning: str = dspy.OutputField(
        desc="Explanation of decomposition strategy"
    )

class ContextAwareDecomposeModule(dspy.Module):
    """Decompose module that considers project context and past decompositions."""

    def __init__(self, context_manager: ContextManager):
        super().__init__()
        self.ctx_mgr = context_manager
        self.decompose = dspy.ChainOfThought(ContextAwareDecomposeSignature)

    def forward(
        self,
        ticket_id: str,
        title: str,
        description: str,
        project_context: Optional[dict] = None,
    ):
        assembled = self.ctx_mgr.assemble_context(
            ticket_id=ticket_id,
            title=title,
            description=description,
            project_context=project_context,
        )

        # Format similar tickets as decomposition examples
        similar_decomp = "Previous similar tasks:\n"
        for t in assembled.related_ctx.tickets[:3]:
            similar_decomp += f"- {t.title} (effort: {t.priority or 'unknown'})\n"

        result = self.decompose(
            title=title,
            description=description,
            project_context=assembled.global_ctx.to_text(),
            similar_decompositions=similar_decomp,
        )

        return result
```

### Phase 2: Fix Critical Bugs

#### 2.1 Fix MultiHop (routes.py:668)

```python
# BEFORE (broken)
similar_tickets="[]"

# AFTER
@router.post("/api/agent/analyze")
async def analyze_ticket(
    request: AnalyzeRequest,
    chroma: ChromaManager = Depends(get_chroma_manager),
):
    # Get similar tickets from ChromaDB
    similar_results = chroma.search(
        f"{request.title} {request.description}",
        limit=5
    )

    similar_tickets = json.dumps([{
        "id": t["id"],
        "title": t["title"],
        "description": t.get("description", "")[:200],
        "priority": t.get("metadata", {}).get("priority"),
        "labels": t.get("metadata", {}).get("labels", []),
    } for t in similar_results])

    # Now pass real data to analyzer
    result = await run_sync_with_timeout(
        lambda: multi_hop_analyzer(
            ticket_title=request.title,
            ticket_description=request.description,
            similar_tickets=similar_tickets,  # Real data now!
        ),
        timeout=60.0,
    )
    return result
```

#### 2.2 Fix DailySummary (routes.py:454-458)

```python
# BEFORE (broken - empty lists)
return summary_module(in_progress=[], blocked=[], ...)

# AFTER - receive from frontend request
class DailySummaryRequest(BaseModel):
    in_progress: list[dict] = Field(default_factory=list)
    blocked: list[dict] = Field(default_factory=list)
    due_soon: list[dict] = Field(default_factory=list)
    recently_completed: list[dict] = Field(default_factory=list)

@router.post("/api/daily-summary")  # Changed from GET to POST
async def daily_summary(request: DailySummaryRequest):
    def run_summary():
        return summary_module(
            in_progress=[t.get("title", "") for t in request.in_progress],
            blocked=[t.get("title", "") for t in request.blocked],
            due_soon=[t.get("title", "") for t in request.due_soon],
            recently_completed=[t.get("title", "") for t in request.recently_completed],
        )

    result = await run_sync_with_timeout(run_summary, timeout=10.0)
    return DailySummaryResponse(
        greeting=result.greeting,
        focus_today=result.focus_today,
        blockers=result.blockers,
        quick_wins=result.quick_wins,
    )
```

#### 2.3 Enable ChromaDB Sync

```rust
// In commands.rs - after creating ticket
#[tauri::command]
pub async fn create_ticket(
    db: State<'_, Database>,
    ticket: TicketCreate,
) -> Result<Ticket, String> {
    let created = db.insert_ticket(&ticket)?;

    // Async sync to ChromaDB (fire and forget)
    let ticket_clone = created.clone();
    tokio::spawn(async move {
        let _ = reqwest::Client::new()
            .post("http://localhost:8765/api/index-ticket")
            .json(&serde_json::json!({
                "ticket_id": ticket_clone.id,
                "title": ticket_clone.title,
                "description": ticket_clone.description.unwrap_or_default(),
                "metadata": {
                    "priority": ticket_clone.priority,
                    "labels": ticket_clone.labels,
                    "column": ticket_clone.column_id,
                }
            }))
            .send()
            .await;
    });

    Ok(created)
}
```

**Python endpoint for indexing:**

```python
# routes.py
@router.post("/api/index-ticket")
async def index_ticket(
    request: IndexTicketRequest,
    chroma: ChromaManager = Depends(get_chroma_manager),
):
    """Index a ticket to ChromaDB for semantic search."""
    chroma.add_ticket(
        ticket_id=request.ticket_id,
        title=request.title,
        description=request.description,
        metadata=request.metadata,
    )
    return {"status": "indexed", "ticket_id": request.ticket_id}
```

---

## Ordine di Implementazione

```
FASE 1: Python Foundation (Priority: Critical)
├── 1.1 context_types.py
├── 1.2 context_manager.py
├── 1.3 retriever.py
└── 1.4 Tests

FASE 2: Fix Bugs (Priority: Critical)
├── 2.1 Fix routes.py MultiHop
├── 2.2 Fix routes.py DailySummary
└── 2.3 Enable cache in routes

FASE 3: Context-Aware Modules
├── 3.1 context_modules.py
├── 3.2 dynamic_multihop.py
└── 3.3 Integrate in routes.py

FASE 4: Rust Backend
├── 4.1 DB migration
├── 4.2 Models + Commands
└── 4.3 Pass context in HTTP calls

FASE 5: React Frontend
├── 5.1 Types + Store
├── 5.2 Settings UI
├── 5.3 Wizard
└── 5.4 Integration

FASE 6: ChromaDB Sync
├── 6.1 Index endpoint
├── 6.2 Rust sync on create/update
└── 6.3 Bulk reindex command
```

---

## Criteri di Successo

1. **Triage migliore**: Labels e priority consistenti col progetto
2. **Decompose context-aware**: Subtask che riflettono tech stack
3. **MultiHop funzionante**: Usa really similar tickets
4. **DailySummary utile**: Mostra real ticket data
5. **Token budget rispettato**: Mai over 4000 tokens
6. **Cache efficiente**: Hit rate > 80% su global/feature
7. **UI intuitiva**: Setup wizard < 2 minuti

---

## Test Plan

### Unit Tests
- [ ] Token estimation accuracy
- [ ] Domain detection (8 domains)
- [ ] Context assembly
- [ ] Budget enforcement
- [ ] Cache TTL behavior

### Integration Tests
- [ ] Full triage with context
- [ ] MultiHop with real ChromaDB
- [ ] Frontend → Rust → Python flow
- [ ] Project context persistence

### Manual Tests
- [ ] Create ticket in mobile app project → correct labels
- [ ] Search for "auth bug" → finds related auth tickets
- [ ] Daily summary shows real tickets
- [ ] Settings wizard completes successfully

---

## Fase 7: DSPy Optimization & Feedback Loop

### Stato Attuale

**Cosa abbiamo:**
- DSPy 2.5+ installato con tutte le capacità di ottimizzazione
- 8 moduli DSPy (Triage, Decompose, DailySummary, ActionDecider, RuleParser, BestOfNDecompose, MultiHop, Suggestions)
- `TicketQualityJudge` già implementato (LLM-as-Judge pattern)
- `AgentAnalytics` traccia chiamate e latenza

**Cosa manca:**
- ❌ Nessuna raccolta di feedback utente
- ❌ Nessuno storage per training data
- ❌ Nessuna pipeline di ottimizzazione
- ❌ Nessun A/B testing per prompt ottimizzati

### Architettura Feedback Loop

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
│                                                             │
│  [👍 Accept] [👎 Reject] [✏️ Edit] [⏭️ Skip]               │
│                                                             │
│  Implicit: User edits AI suggestion                         │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               FEEDBACK COLLECTION LAYER                     │
│                                                             │
│  FeedbackStore (SQLite)                                    │
│  • input: {title, description, context}                    │
│  • predicted: {priority, labels, effort}                   │
│  • actual: {priority, labels, effort}                      │
│  • feedback_type: accept|reject|edit                       │
│  • created_at: timestamp                                   │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               TRAINING DATA PIPELINE                        │
│                                                             │
│  Nightly Job (o on-demand):                                │
│  1. Query feedback con accept rate > 80%                   │
│  2. Converti in dspy.Example                               │
│  3. Split train/dev (80/20)                                │
│  4. Run optimization                                       │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               DSPy OPTIMIZATION                             │
│                                                             │
│  < 50 examples:  BootstrapFewShot                          │
│  50-200 examples: BootstrapFewShotWithRandomSearch         │
│  > 200 examples: MIPROv2 (full instruction optimization)   │
│                                                             │
│  Output: Optimized prompt saved to prompts/                │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│               A/B TESTING LAYER                             │
│                                                             │
│  - 10% traffic to new prompt                               │
│  - Compare metrics (accept rate, edit distance)            │
│  - Auto-promote if new > baseline + 5%                     │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 Schema Database per Feedback

```sql
-- SQLite migration
CREATE TABLE IF NOT EXISTS agent_feedback (
    id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,           -- 'triage', 'decompose', 'chat', etc.

    -- Input context
    input_title TEXT,
    input_description TEXT,
    input_context TEXT,                   -- JSON serialized context

    -- AI prediction
    predicted_output TEXT,                -- JSON {priority, labels, effort, etc.}
    predicted_reasoning TEXT,

    -- User action
    actual_output TEXT,                   -- JSON - what user actually used
    feedback_type TEXT NOT NULL,          -- 'accept', 'reject', 'edit', 'skip'

    -- Metrics
    edit_distance INTEGER,                -- Levenshtein distance if edited
    time_to_decision_ms INTEGER,          -- How long user took to decide

    -- Metadata
    board_id TEXT,
    ticket_id TEXT,
    created_at TEXT NOT NULL,

    -- For optimization
    used_in_training INTEGER DEFAULT 0,
    prompt_version TEXT                   -- Which prompt version was used
);

CREATE INDEX idx_feedback_module ON agent_feedback(module_name);
CREATE INDEX idx_feedback_type ON agent_feedback(feedback_type);
CREATE INDEX idx_feedback_training ON agent_feedback(used_in_training);
```

### 7.2 API Endpoints

```python
# services/agent/src/api/feedback_routes.py

from pydantic import BaseModel
from typing import Literal, Optional
from fastapi import APIRouter

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    module_name: str
    input_title: str
    input_description: str
    input_context: Optional[dict] = None
    predicted_output: dict
    predicted_reasoning: Optional[str] = None
    actual_output: dict
    feedback_type: Literal["accept", "reject", "edit", "skip"]
    time_to_decision_ms: Optional[int] = None
    board_id: Optional[str] = None
    ticket_id: Optional[str] = None

@router.post("/submit")
async def submit_feedback(request: FeedbackRequest):
    """Record user feedback on AI prediction."""
    # Calculate edit distance if edited
    edit_distance = None
    if request.feedback_type == "edit":
        edit_distance = calculate_edit_distance(
            request.predicted_output,
            request.actual_output
        )

    # Store in SQLite
    feedback_id = db.insert_feedback(
        module_name=request.module_name,
        input_title=request.input_title,
        input_description=request.input_description,
        input_context=json.dumps(request.input_context) if request.input_context else None,
        predicted_output=json.dumps(request.predicted_output),
        predicted_reasoning=request.predicted_reasoning,
        actual_output=json.dumps(request.actual_output),
        feedback_type=request.feedback_type,
        edit_distance=edit_distance,
        time_to_decision_ms=request.time_to_decision_ms,
        board_id=request.board_id,
        ticket_id=request.ticket_id,
    )

    return {"status": "recorded", "feedback_id": feedback_id}

@router.get("/stats/{module_name}")
async def get_feedback_stats(module_name: str):
    """Get feedback statistics for a module."""
    stats = db.get_feedback_stats(module_name)
    return {
        "module": module_name,
        "total": stats["total"],
        "accept_rate": stats["accepts"] / stats["total"] if stats["total"] > 0 else 0,
        "reject_rate": stats["rejects"] / stats["total"] if stats["total"] > 0 else 0,
        "edit_rate": stats["edits"] / stats["total"] if stats["total"] > 0 else 0,
        "avg_edit_distance": stats["avg_edit_distance"],
        "ready_for_optimization": stats["total"] >= 50,
    }
```

### 7.3 Metriche per Modulo

```python
# services/agent/src/agent/metrics.py

import dspy
from typing import Callable

def triage_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Metrica per TriageModule: confronta priority, labels, effort."""
    score = 0.0

    # Priority match (40% weight)
    if example.priority == prediction.priority:
        score += 0.4
    elif abs(PRIORITY_ORDER[example.priority] - PRIORITY_ORDER[prediction.priority]) == 1:
        score += 0.2  # Adjacent priority is partial credit

    # Label overlap (40% weight) - Jaccard similarity
    expected_labels = set(example.labels)
    predicted_labels = set(prediction.labels)
    if expected_labels or predicted_labels:
        jaccard = len(expected_labels & predicted_labels) / len(expected_labels | predicted_labels)
        score += 0.4 * jaccard
    else:
        score += 0.4  # Both empty = correct

    # Effort match (20% weight)
    if example.effort == prediction.effort_estimate:
        score += 0.2
    elif abs(EFFORT_ORDER[example.effort] - EFFORT_ORDER[prediction.effort_estimate]) == 1:
        score += 0.1  # Adjacent effort is partial credit

    return score

PRIORITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
EFFORT_ORDER = {"xs": 0, "s": 1, "m": 2, "l": 3, "xl": 4}


def decompose_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Metrica per DecomposeModule: qualità subtask."""
    score = 0.0

    expected_count = len(example.subtasks)
    predicted_count = len(prediction.subtasks)

    # Count similarity (30% weight)
    count_diff = abs(expected_count - predicted_count)
    if count_diff == 0:
        score += 0.3
    elif count_diff == 1:
        score += 0.2
    elif count_diff == 2:
        score += 0.1

    # Title similarity (40% weight) - best match for each expected subtask
    if expected_count > 0:
        matches = 0
        for exp_subtask in example.subtasks:
            best_sim = max(
                title_similarity(exp_subtask["title"], pred["title"])
                for pred in prediction.subtasks
            ) if prediction.subtasks else 0
            if best_sim > 0.7:
                matches += 1
        score += 0.4 * (matches / expected_count)

    # Reasoning quality (30% weight) - via LLM judge
    judge_score = ticket_quality_judge(
        title=example.title,
        description=example.description,
        decomposition=prediction.subtasks,
        reasoning=prediction.reasoning,
    )
    score += 0.3 * (judge_score / 5.0)  # Normalize 1-5 to 0-1

    return score


def chat_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Metrica per ChatModule: relevance e action correctness."""
    score = 0.0

    # Response relevance (50% weight) - embedding similarity
    response_sim = embedding_similarity(
        example.expected_response,
        prediction.response
    )
    score += 0.5 * response_sim

    # Action correctness (50% weight)
    if example.expected_action == prediction.action:
        score += 0.5
    elif prediction.action is None and example.expected_action is None:
        score += 0.5

    return score


def daily_summary_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Metrica per DailySummary: coverage e actionability."""
    score = 0.0

    # Focus items coverage (40%)
    expected_focus = set(example.expected_focus)
    predicted_focus = set(prediction.focus_today)
    if expected_focus:
        coverage = len(expected_focus & predicted_focus) / len(expected_focus)
        score += 0.4 * coverage

    # Blocker identification (30%)
    expected_blockers = set(example.expected_blockers)
    predicted_blockers = set(prediction.blockers)
    if expected_blockers:
        blocker_coverage = len(expected_blockers & predicted_blockers) / len(expected_blockers)
        score += 0.3 * blocker_coverage
    else:
        score += 0.3  # No blockers expected, none predicted = correct

    # Summary quality via judge (30%)
    judge_score = summary_quality_judge(prediction.greeting)
    score += 0.3 * (judge_score / 5.0)

    return score


def rule_parser_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Metrica per RuleParser: accuracy of parsed automation rules."""

    # Exact trigger match (40%)
    trigger_match = example.trigger == prediction.trigger

    # Condition correctness (30%)
    expected_conditions = set(tuple(c.items()) for c in example.conditions)
    predicted_conditions = set(tuple(c.items()) for c in prediction.conditions)
    condition_score = len(expected_conditions & predicted_conditions) / max(len(expected_conditions), 1)

    # Action correctness (30%)
    expected_actions = set(tuple(a.items()) for a in example.actions)
    predicted_actions = set(tuple(a.items()) for a in prediction.actions)
    action_score = len(expected_actions & predicted_actions) / max(len(expected_actions), 1)

    return (0.4 * trigger_match) + (0.3 * condition_score) + (0.3 * action_score)
```

### 7.4 Pipeline di Ottimizzazione

```python
# services/agent/src/agent/optimizer.py

import dspy
from dspy.teleprompt import BootstrapFewShot, BootstrapFewShotWithRandomSearch, MIPROv2
from .metrics import triage_metric, decompose_metric, chat_metric
from .context_modules import ContextAwareTriageModule, ContextAwareDecomposeModule

class ModuleOptimizer:
    """Ottimizza i moduli DSPy usando feedback utente."""

    def __init__(self, context_manager, db):
        self.ctx_mgr = context_manager
        self.db = db

        self.module_configs = {
            "triage": {
                "module_class": ContextAwareTriageModule,
                "metric": triage_metric,
                "min_examples": 20,
            },
            "decompose": {
                "module_class": ContextAwareDecomposeModule,
                "metric": decompose_metric,
                "min_examples": 30,
            },
        }

    def get_training_data(self, module_name: str) -> list[dspy.Example]:
        """Converte feedback in dspy.Example per training."""

        # Get accepted + edited feedback (with low edit distance)
        feedbacks = self.db.query(
            """
            SELECT * FROM agent_feedback
            WHERE module_name = ?
            AND (feedback_type = 'accept' OR (feedback_type = 'edit' AND edit_distance < 3))
            AND used_in_training = 0
            ORDER BY created_at DESC
            LIMIT 500
            """,
            (module_name,)
        )

        examples = []
        for fb in feedbacks:
            input_ctx = json.loads(fb["input_context"]) if fb["input_context"] else {}
            actual = json.loads(fb["actual_output"])

            if module_name == "triage":
                examples.append(dspy.Example(
                    title=fb["input_title"],
                    description=fb["input_description"],
                    project_context=input_ctx.get("project_context", ""),
                    similar_tickets=input_ctx.get("similar_tickets", ""),
                    existing_labels=input_ctx.get("existing_labels", []),
                    # Ground truth from user action
                    priority=actual.get("priority"),
                    labels=actual.get("labels", []),
                    effort=actual.get("effort"),
                ).with_inputs("title", "description", "project_context", "similar_tickets", "existing_labels"))

            elif module_name == "decompose":
                examples.append(dspy.Example(
                    title=fb["input_title"],
                    description=fb["input_description"],
                    project_context=input_ctx.get("project_context", ""),
                    subtasks=actual.get("subtasks", []),
                ).with_inputs("title", "description", "project_context"))

        return examples

    def optimize(self, module_name: str, force: bool = False) -> dict:
        """Esegue ottimizzazione per un modulo."""

        config = self.module_configs.get(module_name)
        if not config:
            return {"error": f"Unknown module: {module_name}"}

        examples = self.get_training_data(module_name)

        if len(examples) < config["min_examples"] and not force:
            return {
                "status": "insufficient_data",
                "current": len(examples),
                "required": config["min_examples"],
            }

        # Split train/dev
        split_idx = int(len(examples) * 0.8)
        trainset = examples[:split_idx]
        devset = examples[split_idx:]

        # Select optimizer based on data size
        if len(examples) < 50:
            optimizer = BootstrapFewShot(
                metric=config["metric"],
                max_bootstrapped_demos=3,
                max_labeled_demos=3,
            )
        elif len(examples) < 200:
            optimizer = BootstrapFewShotWithRandomSearch(
                metric=config["metric"],
                max_bootstrapped_demos=4,
                max_labeled_demos=4,
                num_candidate_programs=10,
            )
        else:
            optimizer = MIPROv2(
                metric=config["metric"],
                num_candidates=15,
                init_temperature=1.0,
            )

        # Run optimization
        module = config["module_class"](self.ctx_mgr)
        optimized = optimizer.compile(module, trainset=trainset, valset=devset)

        # Save optimized prompt
        prompt_path = f"prompts/{module_name}_optimized.json"
        optimized.save(prompt_path)

        # Evaluate on devset
        eval_score = self._evaluate(optimized, devset, config["metric"])
        baseline_score = self._evaluate(module, devset, config["metric"])

        # Mark feedback as used
        self.db.execute(
            "UPDATE agent_feedback SET used_in_training = 1 WHERE module_name = ? AND used_in_training = 0",
            (module_name,)
        )

        return {
            "status": "success",
            "examples_used": len(examples),
            "optimizer": optimizer.__class__.__name__,
            "baseline_score": baseline_score,
            "optimized_score": eval_score,
            "improvement": eval_score - baseline_score,
            "prompt_path": prompt_path,
        }

    def _evaluate(self, module, devset, metric) -> float:
        """Valuta modulo su devset."""
        scores = []
        for example in devset:
            try:
                prediction = module(**example.inputs())
                score = metric(example, prediction)
                scores.append(score)
            except Exception:
                scores.append(0.0)
        return sum(scores) / len(scores) if scores else 0.0
```

### 7.5 A/B Testing Layer

```python
# services/agent/src/agent/ab_testing.py

import random
from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class PromptVariant:
    name: str
    prompt_path: str
    traffic_percentage: float
    is_baseline: bool = False

class ABTestManager:
    """Gestisce A/B testing tra prompt baseline e ottimizzati."""

    def __init__(self, db):
        self.db = db
        self.variants: dict[str, list[PromptVariant]] = {}

    def register_variant(
        self,
        module_name: str,
        variant_name: str,
        prompt_path: str,
        traffic_percentage: float,
        is_baseline: bool = False,
    ):
        """Registra una variante per A/B testing."""
        if module_name not in self.variants:
            self.variants[module_name] = []

        self.variants[module_name].append(PromptVariant(
            name=variant_name,
            prompt_path=prompt_path,
            traffic_percentage=traffic_percentage,
            is_baseline=is_baseline,
        ))

    def select_variant(self, module_name: str) -> Optional[PromptVariant]:
        """Seleziona variante basata su traffic percentage."""
        variants = self.variants.get(module_name, [])
        if not variants:
            return None

        roll = random.random()
        cumulative = 0.0

        for variant in variants:
            cumulative += variant.traffic_percentage
            if roll < cumulative:
                return variant

        # Fallback to baseline
        return next((v for v in variants if v.is_baseline), variants[0])

    def record_variant_usage(
        self,
        module_name: str,
        variant_name: str,
        feedback_id: str,
    ):
        """Registra quale variante è stata usata per un feedback."""
        self.db.execute(
            "UPDATE agent_feedback SET prompt_version = ? WHERE id = ?",
            (variant_name, feedback_id)
        )

    def get_variant_stats(self, module_name: str) -> dict:
        """Ottiene statistiche per variante."""
        stats = {}

        for variant in self.variants.get(module_name, []):
            result = self.db.query_one(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN feedback_type = 'accept' THEN 1 ELSE 0 END) as accepts,
                    AVG(edit_distance) as avg_edit_distance
                FROM agent_feedback
                WHERE module_name = ? AND prompt_version = ?
                """,
                (module_name, variant.name)
            )

            stats[variant.name] = {
                "total": result["total"],
                "accept_rate": result["accepts"] / result["total"] if result["total"] > 0 else 0,
                "avg_edit_distance": result["avg_edit_distance"] or 0,
                "is_baseline": variant.is_baseline,
            }

        return stats

    def should_promote(self, module_name: str, candidate_name: str, threshold: float = 0.05) -> bool:
        """Determina se una variante dovrebbe essere promossa a baseline."""
        stats = self.get_variant_stats(module_name)

        baseline = next((s for n, s in stats.items() if s["is_baseline"]), None)
        candidate = stats.get(candidate_name)

        if not baseline or not candidate:
            return False

        # Require minimum samples
        if candidate["total"] < 50:
            return False

        # Candidate must beat baseline by threshold
        improvement = candidate["accept_rate"] - baseline["accept_rate"]
        return improvement > threshold
```

### 7.6 React Components per Feedback

```tsx
// apps/desktop/src/components/ai/FeedbackButtons.tsx

import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Pencil, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { agentApi } from '@/lib/tauri';

interface FeedbackButtonsProps {
  moduleName: string;
  ticketId: string;
  boardId: string;
  inputTitle: string;
  inputDescription: string;
  inputContext?: Record<string, unknown>;
  predictedOutput: Record<string, unknown>;
  predictedReasoning?: string;
  onFeedback?: (type: FeedbackType) => void;
}

type FeedbackType = 'accept' | 'reject' | 'edit' | 'skip';

export function FeedbackButtons({
  moduleName,
  ticketId,
  boardId,
  inputTitle,
  inputDescription,
  inputContext,
  predictedOutput,
  predictedReasoning,
  onFeedback,
}: FeedbackButtonsProps) {
  const [submitted, setSubmitted] = useState<FeedbackType | null>(null);
  const [startTime] = useState(Date.now());

  const submitFeedback = async (type: FeedbackType, actualOutput?: Record<string, unknown>) => {
    try {
      await agentApi.submitFeedback({
        moduleName,
        inputTitle,
        inputDescription,
        inputContext,
        predictedOutput,
        predictedReasoning,
        actualOutput: actualOutput || predictedOutput,
        feedbackType: type,
        timeToDecisionMs: Date.now() - startTime,
        boardId,
        ticketId,
      });

      setSubmitted(type);
      onFeedback?.(type);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  if (submitted) {
    return (
      <span className="text-xs text-muted-foreground">
        Feedback recorded ✓
      </span>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <Button
        size="sm"
        variant="ghost"
        onClick={() => submitFeedback('accept')}
        className="h-7 px-2"
      >
        <ThumbsUp className="h-3.5 w-3.5 mr-1" />
        Accept
      </Button>

      <Button
        size="sm"
        variant="ghost"
        onClick={() => submitFeedback('reject')}
        className="h-7 px-2"
      >
        <ThumbsDown className="h-3.5 w-3.5 mr-1" />
        Reject
      </Button>

      <Button
        size="sm"
        variant="ghost"
        onClick={() => submitFeedback('skip')}
        className="h-7 px-2"
      >
        <SkipForward className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
```

### 7.7 Files da Creare (Fase 7)

| File | Azione | Descrizione |
|------|--------|-------------|
| `agent/metrics.py` | **NEW** | Metriche per ogni modulo DSPy |
| `agent/optimizer.py` | **NEW** | Pipeline di ottimizzazione |
| `agent/ab_testing.py` | **NEW** | A/B testing manager |
| `api/feedback_routes.py` | **NEW** | API per feedback collection |
| `db/feedback_schema.sql` | **NEW** | Migration per agent_feedback table |
| `components/ai/FeedbackButtons.tsx` | **NEW** | UI per raccolta feedback |
| `lib/tauri.ts` | **MODIFY** | Aggiungere `agentApi.submitFeedback()` |

### 7.8 Ordine di Implementazione (Fase 7)

```
FASE 7: DSPy Optimization
├── 7.1 Database schema per feedback
├── 7.2 API endpoints (submit, stats)
├── 7.3 React FeedbackButtons component
├── 7.4 Metriche per modulo
├── 7.5 Optimizer con BootstrapFewShot
├── 7.6 A/B testing layer
├── 7.7 CLI per manual optimization trigger
└── 7.8 Scheduled optimization job
```

### 7.9 Criteri di Successo (Fase 7)

1. **Feedback collection**: > 50 feedback/settimana raccolti
2. **Accept rate tracking**: Dashboard mostra accept rate per modulo
3. **Optimization runs**: Almeno 1 optimization mensile
4. **Improvement**: +5% accept rate dopo prima ottimizzazione
5. **A/B testing**: Rollout sicuro senza regressioni
