# Practical Examples

Questa pagina mostra esempi pratici di utilizzo dei moduli DSPy in Kanban AI.

## Example 1: Auto-Triage di un Nuovo Ticket

### Scenario

Un utente crea un ticket con titolo e descrizione. L'agent deve assegnare automaticamente priority, labels e effort estimate.

### Codice

```python
from agent.modules import TriageModule

# Inizializza il modulo
triage = TriageModule()

# Input dal ticket
ticket = {
    "title": "Login fails intermittently on mobile Safari",
    "description": """
    Users report that login sometimes fails on iOS Safari.
    Steps to reproduce:
    1. Open app on iPhone Safari
    2. Enter credentials
    3. Click login
    4. Sometimes see "Network error" even with good connection

    Affects ~5% of mobile users based on analytics.
    """,
}

# Labels esistenti nel board (per consistenza)
existing_labels = ["bug", "auth", "frontend", "mobile", "ios", "android", "ux"]

# Esegui triage
result = triage(
    title=ticket["title"],
    description=ticket["description"],
    existing_labels=existing_labels
)

# Output
print(f"Priority: {result.priority}")
print(f"Labels: {result.labels}")
print(f"Effort: {result.effort_estimate}")
print(f"Reasoning: {result.reasoning}")
```

### Output Atteso

```
Priority: high
Labels: ["bug", "auth", "mobile"]
Effort: m
Reasoning: This is a high priority bug affecting user authentication
on a significant platform (5% of mobile users). The intermittent nature
suggests a race condition or network handling issue that will require
investigation and testing across multiple scenarios.
```

---

## Example 2: Decomposizione di un Task Complesso

### Scenario

Un task e troppo grande per essere completato in una sessione. L'agent lo scompone in subtask gestibili.

### Codice

```python
from agent.modules import BestOfNDecompose

# Inizializza con 3 candidati
decompose = BestOfNDecompose(n_candidates=3)

# Task complesso
task = {
    "title": "Implement user settings page",
    "description": """
    Create a new settings page where users can:
    - Update profile information (name, email, avatar)
    - Change password
    - Manage notification preferences
    - Set theme (light/dark mode)
    - Configure keyboard shortcuts
    - Export/import data

    Should be mobile responsive and follow existing design system.
    """
}

# Contesto del board
context = """
Existing components: Button, Input, Toggle, Modal, Avatar
Design system: Tailwind + shadcn/ui
State management: Zustand
API: FastAPI backend with /api/users endpoint
"""

# Esegui decomposizione
result = decompose(
    title=task["title"],
    description=task["description"],
    context=context
)

# Output
print(f"Generated {result['candidates_evaluated']} candidates")
print(f"Best score: {result['score']}")
print("\nSubtasks:")
for i, subtask in enumerate(result['subtasks'], 1):
    print(f"\n{i}. {subtask['title']} ({subtask.get('effort', '?')})")
    print(f"   {subtask.get('description', '')}")

print(f"\nDependencies: {result['dependencies']}")
```

### Output Atteso

```
Generated 3 candidates
Best score: 12.0

Subtasks:

1. Create settings page layout and navigation (s)
   Setup page structure with tabs/sections for different settings areas

2. Implement profile settings section (m)
   Form for name, email, avatar upload with validation

3. Implement password change flow (s)
   Current password verification, new password with confirmation

4. Implement notification preferences (s)
   Toggle controls for email, push, in-app notifications

5. Implement theme selector (xs)
   Light/dark mode toggle with system preference detection

6. Implement keyboard shortcuts configuration (m)
   List of shortcuts with customization modal

7. Implement data export/import (m)
   JSON export of user data, import with validation

Dependencies: [(2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)]
```

---

## Example 3: Daily Summary

### Scenario

All'apertura dell'app, l'agent genera un summary personalizzato della giornata.

### Codice

```python
from agent.modules import DailySummaryModule
from datetime import datetime, timedelta

# Inizializza
summary_module = DailySummaryModule()

# Dati dal board
in_progress = [
    {"id": "1", "title": "Fix Safari login bug", "priority": "high"},
    {"id": "2", "title": "Update API docs", "priority": "medium"},
]

blocked = [
    {"id": "3", "title": "Integrate payment provider", "blocker": "Waiting for API keys"},
]

due_soon = [
    {"id": "4", "title": "Release v2.0", "due_date": (datetime.now() + timedelta(days=2)).isoformat()},
]

recently_completed = [
    {"id": "5", "title": "Add dark mode", "completed_at": datetime.now().isoformat()},
]

# Genera summary
result = summary_module(
    in_progress=in_progress,
    blocked=blocked,
    due_soon=due_soon,
    recently_completed=recently_completed
)

# Output
print(result.greeting)
print("\nFocus today:")
for item in result.focus_today:
    print(f"  - {item}")

print("\nBlockers:")
for item in result.blockers:
    print(f"  - {item}")

print("\nQuick wins:")
for item in result.quick_wins:
    print(f"  - {item}")
```

### Output Atteso

```
Good morning! You have 2 tasks in progress and a release coming up in 2 days.

Focus today:
  - Complete the Safari login bug fix (high priority)
  - Prepare for v2.0 release (due in 2 days)
  - Follow up on payment provider API keys

Blockers:
  - Payment integration is blocked waiting for API keys - consider reaching out

Quick wins:
  - API docs update is almost done, could be completed today
```

---

## Example 4: Chat Interface con Action Decider

### Scenario

L'utente interagisce via chat. L'agent capisce l'intento e decide l'azione.

### Codice

```python
from agent.modules import ActionDeciderModule

# Inizializza
decider = ActionDeciderModule()

# Contesto corrente
context = {
    "current_view": "board",
    "selected_ticket": None,
    "filters": {"status": "all"},
    "recent_tickets": [
        {"id": "1", "title": "Fix login bug", "status": "in_progress"},
        {"id": "2", "title": "Add dark mode", "status": "done"},
    ]
}

# Vari messaggi utente
messages = [
    "Crea un ticket per aggiungere la ricerca full-text",
    "Sposta il bug del login in done",
    "Cosa devo fare oggi?",
    "Trova tutti i ticket con label 'bug'",
    "Scomponi il ticket di ricerca in subtask",
]

for message in messages:
    result = decider(
        user_message=message,
        current_context=context
    )

    print(f"\nUser: {message}")
    print(f"Action: {result.action}")
    print(f"Params: {result.params}")
    print(f"Response: {result.response}")
```

### Output Atteso

```
User: Crea un ticket per aggiungere la ricerca full-text
Action: create
Params: {"title": "Add full-text search", "labels": ["feature", "search"]}
Response: Ho creato il ticket "Add full-text search" con label feature e search.

User: Sposta il bug del login in done
Action: move
Params: {"ticket_id": "1", "column": "done"}
Response: Ho spostato "Fix login bug" in Done. Ottimo lavoro!

User: Cosa devo fare oggi?
Action: summarize
Params: {}
Response: Lasciami analizzare il tuo board...

User: Trova tutti i ticket con label 'bug'
Action: search
Params: {"query": "label:bug"}
Response: Sto cercando i ticket con label bug...

User: Scomponi il ticket di ricerca in subtask
Action: decompose
Params: {"ticket_id": "new_ticket_id"}
Response: Analizzo il ticket per scomporlo in subtask gestibili...
```

---

## Example 5: Parsing di Automation Rules

### Scenario

L'utente crea regole di automazione in linguaggio naturale.

### Codice

```python
from agent.modules import RuleParserModule

# Inizializza
parser = RuleParserModule()

# Contesto del board
board_context = {
    "columns": ["Backlog", "Todo", "In Progress", "Review", "Done"],
    "labels": ["bug", "feature", "urgent", "documentation", "tech-debt"],
    "priorities": ["low", "medium", "high", "critical"]
}

# Regole in linguaggio naturale
rules = [
    "When a ticket is moved to Done, add the 'completed' label",
    "When a new bug is created, set priority to high",
    "When a ticket's due date is within 2 days, add the 'urgent' label",
    "When priority is changed to critical, notify the team",
]

for rule in rules:
    result = parser(
        natural_language=rule,
        board_context=board_context
    )

    print(f"\nRule: {rule}")
    print(f"Name: {result.rule_name}")
    print(f"Trigger: {result.trigger_type} - {result.trigger_config}")
    print(f"Action: {result.action_type} - {result.action_config}")
    print(f"Confidence: {result.confidence}")
```

### Output Atteso

```
Rule: When a ticket is moved to Done, add the 'completed' label
Name: Add completed on done
Trigger: ticket_moved - {"column_name": "Done"}
Action: add_label - {"label_name": "completed"}
Confidence: 0.95

Rule: When a new bug is created, set priority to high
Name: High priority for bugs
Trigger: ticket_created - {"label_contains": "bug"}
Action: set_priority - {"priority": "high"}
Confidence: 0.88

Rule: When a ticket's due date is within 2 days, add the 'urgent' label
Name: Urgent label for due soon
Trigger: due_date_approaching - {"days_before": 2}
Action: add_label - {"label_name": "urgent"}
Confidence: 0.92

Rule: When priority is changed to critical, notify the team
Name: Notify on critical
Trigger: priority_changed - {"new_priority": "critical"}
Action: notify - {"message": "Ticket is now critical"}
Confidence: 0.90
```

---

## Example 6: Valutazione Qualita Ticket

### Scenario

Prima di salvare un ticket, l'agent valuta se e ben scritto.

### Codice

```python
from agent.judge import TicketQualityJudge

# Inizializza
judge = TicketQualityJudge()

# Ticket da valutare
tickets = [
    {
        "title": "Fix bug",
        "description": "There's a bug",
        "priority": "high",
        "effort": "m",
        "labels": ["bug"]
    },
    {
        "title": "Implement OAuth2 authentication with Google",
        "description": """
        Add Google OAuth2 login option to complement existing email/password auth.

        Requirements:
        - Google Sign-In button on login page
        - Handle OAuth2 callback
        - Create user account if first login
        - Link to existing account if email matches

        Tech notes:
        - Use @react-oauth/google library
        - Backend endpoint: POST /api/auth/google
        - Store refresh token securely
        """,
        "priority": "medium",
        "effort": "l",
        "labels": ["feature", "auth", "oauth"]
    }
]

for ticket in tickets:
    result = judge.evaluate_ticket(ticket)

    print(f"\nTicket: {ticket['title']}")
    print(f"Clarity: {result['clarity_score']}/10")
    print(f"Completeness: {result['completeness_score']}/10")
    print(f"Actionability: {result['actionability_score']}/10")
    print(f"Overall: {result['overall_score']:.1f}/10")
    print(f"Feedback: {result['feedback']}")
```

### Output Atteso

```
Ticket: Fix bug
Clarity: 2/10
Completeness: 1/10
Actionability: 2/10
Overall: 1.7/10
Feedback: This ticket is too vague to be actionable:
- What bug? What component/feature is affected?
- Steps to reproduce?
- Expected vs actual behavior?
- Any error messages or logs?
Consider adding these details before assigning.

Ticket: Implement OAuth2 authentication with Google
Clarity: 9/10
Completeness: 9/10
Actionability: 8/10
Overall: 8.7/10
Feedback: Well-written ticket with clear requirements and technical context.
Minor suggestions:
- Add acceptance criteria checklist
- Specify error handling requirements
- Consider adding a link to Google OAuth2 docs
```

---

## Example 7: ReAct Agent per Query Complesse

### Scenario

L'utente fa una domanda che richiede piu passaggi per rispondere.

### Codice

```python
from agent.react_agent import KanbanReActAgent

# Inizializza con max 5 iterazioni
agent = KanbanReActAgent(max_iters=5)

# Query complessa
question = """
Find all high priority bugs from the last week that are still open,
and suggest which one I should work on first based on dependencies.
"""

result = agent(question=question)

print("Answer:", result["answer"])
print("\nTrajectory:")
for step in result["trajectory"]:
    print(f"  Thought: {step.get('thought', '')}")
    print(f"  Action: {step.get('action', '')}")
    print(f"  Result: {step.get('observation', '')[:100]}...")
    print()
```

### Output Atteso

```
Answer: I found 3 high priority bugs from the last week. I recommend
starting with "Fix authentication token refresh" (#42) because it's
blocking 2 other tickets and affects the most users.

Trajectory:
  Thought: I need to search for high priority bugs from the last week
  Action: search_tickets(query="priority:high label:bug created:>7d")
  Result: [{"id": "42", "title": "Fix auth token refresh"}, {"id": "45"...

  Thought: Now I need to check which tickets are still open
  Action: search_tickets(query="priority:high label:bug status:open")
  Result: [{"id": "42", "title": "Fix auth token refresh", "status": "op...

  Thought: Let me check dependencies for these tickets
  Action: get_board_context()
  Result: {"dependencies": {"42": [], "45": ["42"], "48": ["42"]}}...

  Thought: Ticket 42 is blocking others, so it should be done first
  Action: None (ready to answer)
  Result: ...
```

---

## Running the Examples

Tutti gli esempi possono essere eseguiti dalla directory `services/agent`:

```bash
cd services/agent

# Setup environment
uv sync

# Run examples
uv run python examples/basic_usage.py
```

Assicurati di aver configurato le variabili d'ambiente:

```bash
export ANTHROPIC_API_KEY="your-key"
# oppure
export OPENAI_API_KEY="your-key"
```
