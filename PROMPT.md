# ISTRUZIONI PER RALPH - ESEGUI IMMEDIATAMENTE

**NON CHIEDERE CONFERME. INIZIA SUBITO A LAVORARE.**

## COSA FARE

1. Leggi `@fix_plan.md` per vedere la lista delle task
2. Trova la prima task NON completata (senza `[x]`)
3. **Usa l'agent appropriato** (vedi sezione AGENTS sotto)
4. Implementa quella task
5. Marca la task come completata `[x]` in `@fix_plan.md`
6. Passa alla prossima task

## PROGETTO

Kanban AI - Desktop app con Tauri + React + Python AI Agent.

## STRUTTURA

```
apps/desktop/src/          → React frontend
apps/desktop/src-tauri/    → Rust backend
services/agent/src/        → Python DSPy agent
```

## AGENTS E SKILL DA USARE

**IMPORTANTE**: Usa il Task tool con l'agent specializzato appropriato per ogni task.

### Per moduli DSPy (TASK-056, TASK-057, TASK-059, TASK-061, TASK-065):
```
Prima invoca: Skill tool con skill="scientific-skills:dspy"
Poi usa: Task tool con subagent_type="python-expert"
```

### Per codice Python generico (TASK-062, TASK-063):
```
Task tool con subagent_type="python-expert"
```

### Per API endpoints FastAPI (TASK-058, TASK-060, TASK-064):
```
Task tool con subagent_type="fastapi-expert"
```

### Per componenti React (future UI task):
```
Task tool con subagent_type="react-component-architect"
```

### Workflow per task DSPy:
1. Invoca `Skill tool` con `skill="scientific-skills:dspy"` per caricare contesto DSPy
2. Usa `Task tool` con `subagent_type="python-expert"` per implementare
3. Il prompt deve includere il pattern dal `@fix_plan.md`

### Esempio di chiamata:
```
# Step 1: Carica skill DSPy
Skill tool: skill="scientific-skills:dspy"

# Step 2: Implementa con agent
Task tool:
- subagent_type: "python-expert"
- prompt: "Implementa TASK-056: Aggiungere DSPy Assertions a TriageModule in services/agent/src/agent/modules.py. Segui il pattern nel @fix_plan.md."
```

## REGOLE

- NON chiedere cosa fare - leggi @fix_plan.md
- NON chiedere conferme - esegui direttamente
- USA SEMPRE gli agent specializzati (Task tool)
- Crea i file necessari
- Testa che il codice compili
- Segui i pattern esistenti nel progetto
- Una task alla volta

## QUANDO HAI FINITO UNA TASK

Scrivi: "TASK-XXX completata. Prossima: TASK-YYY"

## INIZIA ORA

Leggi `@fix_plan.md` e implementa la prima task non completata usando l'agent appropriato.
