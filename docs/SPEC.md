# Kanban AI - Product Specification

## Overview

**Kanban AI** è una desktop application per la gestione di ticket/task in locale, con un agent AI integrato che automatizza e assiste nella gestione del workflow.

### Target User
- Sviluppatori e tech workers
- Freelancer che gestiscono più progetti
- Chiunque voglia un kanban potente ma locale

### Value Proposition
1. **Privacy-first**: Tutti i dati restano sul tuo computer
2. **AI-powered**: L'agent capisce i tuoi task e ti aiuta
3. **Beautiful**: UI moderna ispirata a Linear
4. **Fast**: App nativa, nessun browser overhead

---

## Core Features

### 1. Kanban Board

#### 1.1 Columns
- Colonne default: Backlog, To Do, In Progress, Review, Done
- Colonne custom illimitate
- Drag & drop per riordinare colonne
- WIP limits opzionali per colonna
- Colori custom per colonna

#### 1.2 Tickets
- **Campi base:**
  - Title (required)
  - Description (markdown support)
  - Priority: Low, Medium, High, Critical
  - Effort estimate: XS, S, M, L, XL
  - Due date (optional)
  - Labels (multiple)
  - Comments
  
- **Operazioni:**
  - Create, Read, Update, Delete
  - Drag & drop tra colonne
  - Reorder within column
  - Quick edit inline
  - Full modal edit

#### 1.3 Labels
- Nome + colore
- Gestione globale
- Filtro per label

### 2. AI Agent

#### 2.1 Auto-Triage
Quando crei un nuovo ticket, l'agent può:
- Suggerire priority basata sul contenuto
- Assegnare labels rilevanti
- Stimare effort
- Spiegare il ragionamento

**Trigger:** Automatico on create, o manuale via ⌘⇧T

#### 2.2 Task Decomposition
Per ticket complessi, l'agent può:
- Analizzare la descrizione
- Proporre subtask atomici
- Suggerire dipendenze tra subtask
- Creare i subtask con un click

**Trigger:** Menu contestuale "Decompose task" o ⌘⇧D

#### 2.3 Daily Summary
Ogni giorno (o on-demand), l'agent genera:
- Top 3 priorità per oggi
- Blocchi da risolvere
- Quick wins disponibili
- Progress report

**Trigger:** Automatico all'apertura, o ⌘⇧S

#### 2.4 Chat Interface
Interfaccia conversazionale per:
- Chiedere info sui ticket
- Dare comandi naturali ("sposta X in done")
- Ricevere suggerimenti
- Brainstorming

**Trigger:** ⌘⇧A o click su AI button

#### 2.5 Semantic Search
Cerca ticket per significato, non solo keyword:
- "Trova tutti i bug di performance"
- "Cosa devo fare per il rilascio?"
- "Mostrami i task bloccati"

### 3. Views

#### 3.1 Board View (default)
- Kanban classico con colonne
- Drag & drop
- Filtri rapidi

#### 3.2 List View
- Tabella ordinabile
- Bulk actions
- Export CSV

#### 3.3 Timeline View (future)
- Gantt-like visualization
- Dependencies
- Due dates

### 4. Command Palette (⌘K)

Quick access a tutto:
- Cerca ticket
- Cambia view
- Crea nuovo ticket
- Naviga board
- Azioni AI

### 5. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| ⌘K | Command palette |
| ⌘N | New ticket |
| ⌘⇧A | AI chat |
| ⌘⇧T | AI triage |
| ⌘⇧D | Decompose task |
| ⌘⇧S | Daily summary |
| ⌘/ | Toggle sidebar |
| ⌘1 | Board view |
| ⌘2 | List view |
| ⌘3 | Timeline view |
| ⌘, | Settings |
| Esc | Close modal/palette |
| ↑↓ | Navigate tickets |
| Enter | Open ticket |
| Space | Quick preview |
| Del | Delete (with confirm) |

---

## User Interface

### Design Principles

1. **Clarity over decoration**: Ogni elemento ha uno scopo
2. **Speed**: Interazioni immediate, zero lag percepito
3. **Keyboard-first**: Tutto accessibile da tastiera
4. **Progressive disclosure**: Features avanzate non intralciano

### Visual Style

- **Theme:** Dark mode primary (light mode supportato)
- **Style:** Hybrid Linear + Glassmorphism
- **Typography:** Plus Jakarta Sans (display) + Inter (body)
- **Spacing:** 8px grid system
- **Radius:** 8-12px per cards, 6px per buttons
- **Shadows:** Subtle, usati per depth

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ ┌─────────┐  Search          [View Toggle]  [AI]  [Settings]│ ← Header
│ │         │──────────────────────────────────────────────────│
│ │ Sidebar │  Column 1    Column 2    Column 3    Column 4   │
│ │         │  ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐  │
│ │ · Board │  │ Card  │   │ Card  │   │ Card  │   │       │  │
│ │ · List  │  ├───────┤   ├───────┤   ├───────┤   │       │  │
│ │         │  │ Card  │   │ Card  │   │       │   │       │  │
│ │ Labels  │  ├───────┤   ├───────┤   │       │   │       │  │
│ │ · bug   │  │ Card  │   │       │   │       │   │       │  │
│ │ · feat  │  │       │   │       │   │       │   │       │  │
│ └─────────┘  └───────┘   └───────┘   └───────┘   └───────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### Ticket Card
```
┌────────────────────────────────┐
│ ● Critical   [bug] [frontend] │ ← Priority dot + labels
│                                │
│ Fix login redirect bug         │ ← Title
│                                │
│ 📅 Jan 15  ⏱ M  💬 3          │ ← Due date, effort, comments
└────────────────────────────────┘
```

#### Ticket Modal
```
┌────────────────────────────────────────┐
│ [x]                                    │
│                                        │
│ Fix login redirect bug                 │ ← Title (editable)
│                                        │
│ ┌────────────────────────────────────┐ │
│ │ Description (markdown)             │ │ ← Description editor
│ │                                    │ │
│ └────────────────────────────────────┘ │
│                                        │
│ Priority: [Critical ▼]                 │
│ Labels:   [bug] [frontend] [+ Add]     │
│ Effort:   [M ▼]                        │
│ Due:      [Jan 15, 2025]               │
│                                        │
│ ─────────── Activity ───────────       │
│ 💬 Comment 1...                        │
│ 💬 Comment 2...                        │
│ [Add comment...]                       │
│                                        │
│ [🤖 AI Triage] [Delete]                │
└────────────────────────────────────────┘
```

---

## Data Model

### Entities

```typescript
interface Board {
  id: string;
  name: string;
  columns: Column[];
  createdAt: Date;
  updatedAt: Date;
}

interface Column {
  id: string;
  boardId: string;
  name: string;
  position: number;
  color?: string;
  wipLimit?: number;
}

interface Ticket {
  id: string;
  columnId: string;
  title: string;
  description?: string;
  position: number;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  effort?: 'xs' | 's' | 'm' | 'l' | 'xl';
  dueDate?: Date;
  labels: Label[];
  comments: Comment[];
  createdAt: Date;
  updatedAt: Date;
}

interface Label {
  id: string;
  name: string;
  color: string;
}

interface Comment {
  id: string;
  ticketId: string;
  content: string;
  createdAt: Date;
}
```

### Storage

- **Primary:** SQLite database (local file)
- **Vectors:** ChromaDB (for semantic search)
- **Location:** `~/.kanban-ai/data/`

---

## Technical Requirements

### Performance

- App launch: < 1s
- Ticket create: < 100ms
- Drag & drop: 60fps
- AI triage: < 3s (API dependent)
- Search: < 200ms

### Compatibility

- macOS 12+
- Windows 10+
- Linux (Ubuntu 20.04+)

### Security

- No data sent to cloud (except LLM API calls)
- API keys stored in system keychain
- Optional: encrypt database at rest

---

## Future Considerations

### Cloud Sync (Phase 4)
- Optional account creation
- End-to-end encrypted sync
- Real-time collaboration

### Integrations
- GitHub issues sync
- Calendar integration
- Slack notifications

### Mobile
- Flutter or React Native app
- Sync with desktop via cloud

---

## Success Metrics

### MVP Success
- [ ] Can create and manage tickets
- [ ] Drag & drop works smoothly
- [ ] AI triage provides useful suggestions
- [ ] App feels fast and responsive

### Product-Market Fit Indicators
- Daily active usage > 5 days/week
- Tickets created per week > 10
- AI features used > 50% of sessions
- User recommends to others
