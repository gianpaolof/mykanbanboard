# 🏗️ Architettura Kanban AI - Guida per Principianti

Questa guida spiega l'architettura del progetto in modo semplice, anche se non conosci React, Rust o DSPy.

---

## 📱 Cos'è Questa App?

**Kanban AI** è un'app desktop per gestire ticket/task (tipo Trello/Jira) che gira sul tuo computer. Ha un assistente AI integrato che ti aiuta a organizzare il lavoro.

### Perché Desktop e Non Web?
- **Privacy**: I tuoi dati restano sul tuo PC, non vanno su server esterni
- **Velocità**: App nativa = più veloce di un sito web
- **Offline**: Funziona senza internet (tranne le chiamate AI)

---

## 🧱 I 3 Blocchi Principali

L'app è divisa in 3 parti che comunicano tra loro:

```
┌─────────────────────────────────────────────────────────┐
│  1. FRONTEND (React)                                    │
│     → Quello che vedi: bottoni, card, colonne           │
│     → Scritto in TypeScript/JavaScript                  │
└───────────────────────────┬─────────────────────────────┘
                            │ "Ehi, salva questo ticket"
                            ▼
┌─────────────────────────────────────────────────────────┐
│  2. BACKEND (Rust/Tauri)                                │
│     → Il "cervello" dell'app                            │
│     → Salva dati nel database SQLite                    │
│     → Gestisce i file sul tuo PC                        │
└───────────────────────────┬─────────────────────────────┘
                            │ "Analizza questo ticket"
                            ▼
┌─────────────────────────────────────────────────────────┐
│  3. AI AGENT (Python)                                   │
│     → L'assistente intelligente                         │
│     → Chiama Claude/OpenAI per ragionare                │
│     → Cerca ticket simili                               │
└─────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Frontend (React + TypeScript)

### Cos'è React?
React è una libreria per costruire interfacce utente. Invece di scrivere HTML a mano, scrivi "componenti" riutilizzabili.

**Esempio semplificato:**
```tsx
// Un componente = un pezzo di UI
function TicketCard({ title, priority }) {
  return (
    <div className="card">
      <span className={`dot ${priority}`} />
      <h3>{title}</h3>
    </div>
  );
}

// Lo usi così:
<TicketCard title="Fix bug login" priority="high" />
```

### Struttura delle Cartelle
```
src/
├── components/          # Pezzi di UI riutilizzabili
│   ├── ui/              # Bottoni, input, select (base)
│   ├── kanban/          # Board, Column, Card
│   ├── layout/          # Sidebar, Header
│   └── ai/              # Chat con AI
├── stores/              # Dove salvo lo "stato" dell'app
├── hooks/               # Funzioni riutilizzabili
├── types/               # Definizioni TypeScript
└── styles/              # CSS/Tailwind
```

### Librerie Usate
| Libreria | A cosa serve |
|----------|--------------|
| **React** | Costruire la UI |
| **Tailwind CSS** | Styling veloce con classi |
| **Framer Motion** | Animazioni fluide |
| **@dnd-kit** | Drag & drop delle card |
| **cmdk** | Command palette (⌘K) |
| **Zustand** | Gestione stato (tipo Redux ma più semplice) |

---

## 2️⃣ Backend (Rust + Tauri)

### Cos'è Tauri?
Tauri è il "contenitore" che trasforma la nostra app web in un'app desktop. È come Electron (quello di VS Code) ma molto più leggero.

### Cos'è Rust?
Rust è un linguaggio veloce e sicuro. Lo usiamo per:
- Leggere/scrivere sul database
- Gestire file
- Comunicare tra frontend e AI

### Come Comunicano Frontend e Backend?

**Frontend:**
```typescript
// Chiama una funzione Rust
const tickets = await invoke('get_all_tickets');
```

**Backend (Rust):**
```rust
#[tauri::command]
fn get_all_tickets() -> Vec<Ticket> {
    // Legge dal database e ritorna i ticket
    db::tickets::get_all()
}
```

### Database: SQLite
SQLite è un database che sta tutto in UN file. Niente server da installare.

**Schema semplificato:**
```sql
-- Tabella tickets
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT,      -- 'low', 'medium', 'high', 'critical'
    effort TEXT,        -- 'xs', 's', 'm', 'l', 'xl'
    column_id TEXT,
    position INTEGER,
    created_at DATETIME
);

-- Tabella columns
CREATE TABLE columns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    position INTEGER,
    color TEXT
);
```

---

## 3️⃣ AI Agent (Python + DSPy)

### Cos'è DSPy?
DSPy è un framework per costruire agenti AI in modo "programmabile". Invece di scrivere prompt lunghi, definisci cosa vuoi e lui genera i prompt.

**Esempio tradizionale (prompt engineering):**
```
"Sei un assistente che analizza ticket. Dato il titolo e descrizione,
devi assegnare una priority (low/medium/high/critical) e dei labels.
Rispondi in JSON..."
```

**Con DSPy:**
```python
class TriageTicket(dspy.Signature):
    """Analizza un ticket e assegna metadati."""
    title: str = dspy.InputField()
    description: str = dspy.InputField()
    
    priority: Literal["low", "medium", "high", "critical"] = dspy.OutputField()
    labels: list[str] = dspy.OutputField()
```

DSPy genera automaticamente il prompt migliore!

### FastAPI: Il Server dell'Agent
FastAPI è un framework Python per creare API veloci.

```python
@app.post("/api/triage")
async def triage_ticket(request: TriageRequest):
    result = agent.triage(request.title, request.description)
    return result
```

### ChromaDB: Ricerca Semantica
ChromaDB salva i ticket come "vettori" (numeri che rappresentano il significato). Questo permette di cercare per significato, non solo parole.

**Esempio:**
- Query: "problemi di performance"
- Trova: "Ottimizzare caricamento immagini" (non contiene "performance" ma è correlato!)

---

## 🔄 Come Comunicano i 3 Blocchi

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND                                                │
│  ┌────────────────┐                                      │
│  │ User clicca    │                                      │
│  │ "AI Triage"    │                                      │
│  └───────┬────────┘                                      │
│          │                                               │
│          ▼                                               │
│  invoke('triage_ticket', { ticketId: '123' })            │
└──────────────────────────────────────────────────────────┘
           │
           │ Tauri IPC (comunicazione interna)
           ▼
┌──────────────────────────────────────────────────────────┐
│  BACKEND (Rust)                                          │
│  ┌────────────────┐                                      │
│  │ 1. Legge il    │                                      │
│  │    ticket da   │                                      │
│  │    SQLite      │                                      │
│  └───────┬────────┘                                      │
│          │                                               │
│          ▼                                               │
│  HTTP POST a localhost:8765/api/triage                   │
└──────────────────────────────────────────────────────────┘
           │
           │ HTTP (localhost)
           ▼
┌──────────────────────────────────────────────────────────┐
│  AI AGENT (Python)                                       │
│  ┌────────────────┐    ┌────────────────┐               │
│  │ DSPy processa  │───▶│ Chiama Claude  │               │
│  │ la richiesta   │    │ API            │               │
│  └────────────────┘    └───────┬────────┘               │
│                                │                         │
│                                ▼                         │
│                        { priority: "high",               │
│                          labels: ["bug", "ui"] }         │
└──────────────────────────────────────────────────────────┘
```

---

## 📂 Struttura File Completa

```
kanban/
│
├── apps/desktop/                 # App Tauri + React
│   ├── src/                      # Codice React (frontend)
│   │   ├── components/
│   │   │   ├── ui/               # Button, Input, Dialog...
│   │   │   ├── kanban/           # Board, Column, TicketCard
│   │   │   ├── layout/           # Sidebar, Header, CommandPalette
│   │   │   └── ai/               # AgentChat, Suggestions
│   │   ├── stores/               # Zustand stores (stato app)
│   │   │   ├── boardStore.ts     # Stato del kanban
│   │   │   └── uiStore.ts        # Stato UI (modali, sidebar)
│   │   ├── hooks/                # React hooks custom
│   │   ├── lib/                  # Utility functions
│   │   ├── types/                # TypeScript types
│   │   ├── styles/               # CSS globali
│   │   ├── App.tsx               # Componente root
│   │   └── main.tsx              # Entry point
│   │
│   ├── src-tauri/                # Codice Rust (backend)
│   │   ├── src/
│   │   │   ├── main.rs           # Entry point Rust
│   │   │   ├── commands.rs       # Comandi chiamabili da React
│   │   │   ├── db.rs             # Operazioni database
│   │   │   └── agent.rs          # Client per Python agent
│   │   ├── Cargo.toml            # Dipendenze Rust
│   │   └── tauri.conf.json       # Config Tauri
│   │
│   ├── package.json              # Dipendenze JavaScript
│   ├── vite.config.ts            # Config build
│   ├── tailwind.config.js        # Config Tailwind
│   └── tsconfig.json             # Config TypeScript
│
├── services/agent/               # Server AI (Python)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── modules.py            # DSPy modules (Triage, Decompose...)
│   │   └── actions.py            # Azioni sui ticket
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # Endpoints FastAPI
│   ├── db/
│   │   ├── __init__.py
│   │   └── chroma.py             # ChromaDB setup
│   ├── main.py                   # Entry point FastAPI
│   ├── config.py                 # Configurazione
│   └── pyproject.toml            # Dipendenze Python
│
├── docs/                         # Documentazione
│   ├── ARCHITECTURE.md           # Questo file!
│   ├── SPEC.md                   # Specifiche prodotto
│   ├── UI_DESIGN.md              # Design system
│   ├── AGENT_DESIGN.md           # Documentazione AI
│   ├── API.md                    # Reference API
│   └── mockups/                  # Mockup HTML
│
├── .claude/                      # Prompt per Claude Code
│   ├── coordinator-agent.md
│   ├── ui-agent.md
│   ├── backend-agent.md
│   └── agent-agent.md
│
└── CLAUDE.md                     # Overview progetto
```

---

## 🚀 Come Far Partire Tutto

### Prerequisiti
```bash
# Node.js (per React)
node --version  # deve essere >= 18

# Rust (per Tauri)
rustc --version

# Python (per Agent)
python --version  # deve essere >= 3.11

# pnpm (package manager veloce)
npm install -g pnpm
```

### Avvio Sviluppo
```bash
# Terminal 1: Frontend + Tauri
cd apps/desktop
pnpm install
pnpm tauri dev

# Terminal 2: Agent Python
cd services/agent
uv venv && source .venv/bin/activate
uv pip install -e .
uvicorn main:app --reload --port 8765
```

---

## 🔑 Concetti Chiave

### State Management (Zustand)
Lo "stato" è l'insieme di dati che l'app deve ricordare:
- Quali ticket esistono
- Quale modale è aperta
- Qual è il filtro attivo

```typescript
// stores/boardStore.ts
const useBoardStore = create((set) => ({
  tickets: [],
  columns: [],
  
  addTicket: (ticket) => set((state) => ({
    tickets: [...state.tickets, ticket]
  })),
  
  moveTicket: (ticketId, toColumnId) => ...
}));
```

### Componenti React
Ogni pezzo di UI è un componente:

```tsx
// Componente semplice
function PriorityDot({ priority }: { priority: Priority }) {
  return (
    <span 
      className={cn(
        "w-2 h-2 rounded-full",
        priority === 'critical' && "bg-red-500 shadow-red-500/50",
        priority === 'high' && "bg-orange-500",
        priority === 'medium' && "bg-yellow-500",
        priority === 'low' && "bg-green-500",
      )} 
    />
  );
}
```

### Tauri Commands
Funzioni Rust chiamabili da JavaScript:

```rust
// Rust
#[tauri::command]
async fn create_ticket(title: String, description: Option<String>) -> Result<Ticket, String> {
    let ticket = Ticket::new(title, description);
    db::insert_ticket(&ticket)?;
    Ok(ticket)
}
```

```typescript
// JavaScript
const newTicket = await invoke('create_ticket', { 
  title: 'Fix bug', 
  description: 'Il login non funziona' 
});
```

---

## ❓ FAQ

### Perché Tauri e non Electron?
| | Tauri | Electron |
|---|---|---|
| Bundle size | ~5 MB | ~150+ MB |
| RAM | Bassa | Alta |
| Backend | Rust (veloce) | Node.js |
| Sicurezza | Alta | Media |

### Perché DSPy e non LangChain?
- **DSPy**: Programmatic prompting, type-safe, ottimizzabile
- **LangChain**: Più maturo ma più complesso e verboso

### Posso usare GPT invece di Claude?
Sì! Cambia la config in `services/agent/config.py`:
```python
default_model = "gpt-4o"  # invece di "claude-sonnet-4-20250514"
```

---

## 📚 Risorse per Imparare

### React
- [React Docs (italiano)](https://it.react.dev/)
- [React Tutorial Beginner](https://www.youtube.com/watch?v=Rh3tobg7hEo)

### Tauri
- [Tauri Docs](https://tauri.app/v1/guides/)
- [Tauri + React Tutorial](https://www.youtube.com/watch?v=kRoGYgAuZQE)

### Rust (base)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)

### DSPy
- [DSPy Docs](https://dspy-docs.vercel.app/)
- [DSPy Tutorial](https://www.youtube.com/watch?v=41EfOY0Ldkc)

### Tailwind CSS
- [Tailwind Docs](https://tailwindcss.com/docs)
- [Tailwind Cheat Sheet](https://nerdcave.com/tailwind-cheat-sheet)
