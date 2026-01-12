# Assertions & Validation

DSPy Assertions permettono di validare l'output dei moduli LLM e far riprovare automaticamente quando i vincoli non sono rispettati.

## Tipi di Assertions

### dspy.Assert (Hard Constraints)

**Comportamento**: Se il vincolo fallisce, l'LLM riprova con feedback.

```python
dspy.Assert(
    condition,      # Espressione booleana
    message         # Feedback per l'LLM se fallisce
)
```

**Esempio**:

```python
result = self.predictor(...)

dspy.Assert(
    result.priority in ["low", "medium", "high", "critical"],
    f"Priority '{result.priority}' non valida. Usa: low, medium, high, critical"
)
```

Se `result.priority` e "urgent", l'LLM riceve il messaggio di errore e riprova.

### dspy.Suggest (Soft Constraints)

**Comportamento**: Se il vincolo fallisce, logga un warning ma continua.

```python
dspy.Suggest(
    condition,      # Espressione booleana
    message         # Warning message
)
```

**Esempio**:

```python
dspy.Suggest(
    len(result.labels) <= 3,
    f"Troppe labels ({len(result.labels)}). Preferire max 3 per chiarezza."
)
```

Se ci sono 5 labels, viene loggato un warning ma l'esecuzione continua.

## Quando Usare Assert vs Suggest

| Scenario | Usa |
|----------|-----|
| Output deve essere in un set fisso | Assert |
| Tipo di dato deve essere corretto | Assert |
| Struttura dati richiesta | Assert |
| Preferenze di stile | Suggest |
| Best practices | Suggest |
| Limiti soft (es. lunghezza) | Suggest |

## Pattern Comuni

### Validazione Enum/Literal

```python
VALID_PRIORITIES = ("low", "medium", "high", "critical")

dspy.Assert(
    result.priority in VALID_PRIORITIES,
    f"Priority '{result.priority}' invalida. Valori ammessi: {VALID_PRIORITIES}"
)
```

### Validazione Tipo

```python
dspy.Assert(
    isinstance(result.labels, list),
    "Labels deve essere una lista di stringhe"
)

dspy.Assert(
    all(isinstance(label, str) for label in result.labels),
    "Ogni label deve essere una stringa"
)
```

### Validazione Range

```python
dspy.Assert(
    0 <= result.score <= 10,
    f"Score {result.score} fuori range. Deve essere 0-10."
)
```

### Validazione Struttura Dict

```python
for i, subtask in enumerate(result.subtasks):
    dspy.Assert(
        isinstance(subtask, dict) and "title" in subtask,
        f"Subtask {i} deve essere un dict con almeno 'title'"
    )
```

### Validazione Condizionale

```python
if result.action == "create":
    dspy.Assert(
        "title" in result.params,
        "L'azione 'create' richiede 'title' nei parametri"
    )
elif result.action == "move":
    dspy.Assert(
        "ticket_id" in result.params or "column" in result.params,
        "L'azione 'move' richiede 'ticket_id' o 'column'"
    )
```

### Validazione Numerica

```python
try:
    confidence = float(result.confidence)
    dspy.Assert(
        0.0 <= confidence <= 1.0,
        f"Confidence {confidence} deve essere tra 0.0 e 1.0"
    )
except (TypeError, ValueError):
    dspy.Assert(
        False,
        f"Confidence deve essere un numero, ricevuto: {result.confidence}"
    )
```

## Assertions in Kanban AI

### TriageModule

```python
def forward(self, title, description, existing_labels):
    result = self.triage(...)

    # Hard constraints - retry if failed
    dspy.Assert(
        result.priority in VALID_PRIORITIES,
        f"Priority '{result.priority}' invalida"
    )
    dspy.Assert(
        result.effort_estimate in VALID_EFFORTS,
        f"Effort '{result.effort_estimate}' invalido"
    )
    dspy.Assert(
        isinstance(result.labels, list),
        "Labels deve essere una lista"
    )

    # Soft constraints - warn but continue
    dspy.Suggest(
        len(result.labels) <= 3,
        f"Troppe labels ({len(result.labels)})"
    )
    dspy.Suggest(
        len(result.reasoning) >= 20,
        "Il reasoning dovrebbe essere piu dettagliato"
    )

    return result
```

### DecomposeModule

```python
def forward(self, title, description, context):
    result = self.decompose(...)

    # Validate list structure
    dspy.Assert(
        isinstance(result.subtasks, list),
        "Subtasks deve essere una lista"
    )
    dspy.Assert(
        len(result.subtasks) >= 2,
        f"Servono almeno 2 subtasks, ricevuti {len(result.subtasks)}"
    )
    dspy.Assert(
        len(result.subtasks) <= 10,
        f"Troppi subtasks ({len(result.subtasks)}). Massimo 10."
    )

    # Validate each subtask
    for i, subtask in enumerate(result.subtasks):
        dspy.Assert(
            isinstance(subtask, dict) and "title" in subtask,
            f"Subtask {i} deve avere 'title'"
        )
        if "effort" in subtask:
            dspy.Assert(
                subtask["effort"] in VALID_EFFORTS,
                f"Subtask {i} effort invalido"
            )

    # Soft constraints
    dspy.Suggest(
        3 <= len(result.subtasks) <= 7,
        f"Range ottimale e 3-7 subtasks"
    )

    return result
```

### TicketQualityJudge

```python
def forward(self, ticket_title, ticket_description, priority, effort, labels):
    result = self.judge(...)

    # Validate scores are in range
    dspy.Assert(
        0 <= int(result.clarity_score) <= 10,
        f"Clarity score deve essere 0-10"
    )
    dspy.Assert(
        0 <= int(result.completeness_score) <= 10,
        f"Completeness score deve essere 0-10"
    )
    dspy.Assert(
        0 <= int(result.actionability_score) <= 10,
        f"Actionability score deve essere 0-10"
    )

    # Soft constraint for feedback quality
    dspy.Suggest(
        len(result.feedback) >= 20,
        "Il feedback dovrebbe essere piu dettagliato"
    )

    return result
```

## Best Practices

### 1. Messaggi Chiari

```python
# Buono - spiega cosa e sbagliato e cosa e atteso
dspy.Assert(
    result.priority in VALID_PRIORITIES,
    f"Priority '{result.priority}' non riconosciuta. "
    f"Valori validi: {', '.join(VALID_PRIORITIES)}"
)

# Cattivo - poco informativo
dspy.Assert(result.priority in VALID_PRIORITIES, "Invalid priority")
```

### 2. Ordine delle Validazioni

Valida prima le strutture base, poi i dettagli:

```python
# 1. Prima: tipo corretto
dspy.Assert(isinstance(result.subtasks, list), "...")

# 2. Poi: lunghezza
dspy.Assert(len(result.subtasks) >= 2, "...")

# 3. Infine: contenuto di ogni elemento
for subtask in result.subtasks:
    dspy.Assert("title" in subtask, "...")
```

### 3. Usa Suggest per Preferenze

```python
# Assert per requisiti
dspy.Assert(result.title, "Il titolo e obbligatorio")

# Suggest per preferenze
dspy.Suggest(len(result.title) <= 100, "Titoli corti sono preferibili")
```

### 4. Gestisci Eccezioni

```python
try:
    score = float(result.confidence)
except (TypeError, ValueError) as e:
    dspy.Assert(False, f"Confidence non e un numero valido: {e}")
```

## Debugging

Per vedere quando le assertions falliscono e causano retry:

```python
import logging
logging.getLogger("dspy").setLevel(logging.DEBUG)
```

Output:

```
DEBUG:dspy:Assertion failed: Priority 'urgent' non valida
DEBUG:dspy:Retrying with feedback...
DEBUG:dspy:Attempt 2/3
DEBUG:dspy:Assertion passed
```
