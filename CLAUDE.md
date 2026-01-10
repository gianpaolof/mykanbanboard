# Kanban AI - Project Overview

## 🎯 Project Description

Kanban AI è una desktop app per la gestione di ticket in locale con un agent AI integrato basato su DSPy. L'app combina un'interfaccia moderna stile Linear con funzionalità AI avanzate per la gestione automatica dei ticket.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 TAURI + REACT FRONTEND                      │
│  • React 18 + TypeScript                                    │
│  • Tailwind CSS + shadcn/ui (customized)                    │
│  • Framer Motion animations                                 │
│  • @dnd-kit drag & drop                                     │
│  • cmdk command palette                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │ Tauri IPC
┌──────────────────────────▼──────────────────────────────────┐
│                    RUST BACKEND (Tauri)                     │
│  • SQLite database                                          │
│  • File system operations                                   │
│  • Future: sync engine                                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP localhost:8765
┌──────────────────────────▼──────────────────────────────────┐
│                    PYTHON SIDECAR                           │
│  • FastAPI server                                           │
│  • DSPy agent (Claude/OpenAI)                               │
│  • ChromaDB vector store                                    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
kanban/
├── apps/
│   └── desktop/              # Tauri + React app
│       ├── src/              # React frontend
│       │   ├── components/   # UI components
│       │   ├── stores/       # Zustand stores
│       │   ├── hooks/        # Custom hooks
│       │   ├── lib/          # Utilities
│       │   └── types/        # TypeScript types
│       └── src-tauri/        # Rust backend
│
├── services/
│   └── agent/                # Python AI agent
│       ├── agent/            # DSPy modules
│       ├── api/              # FastAPI routes
│       └── db/               # ChromaDB setup
│
├── docs/                     # Documentation
│   ├── SPEC.md               # Product specification
│   ├── UI_DESIGN.md          # UI/UX guidelines
│   ├── AGENT_DESIGN.md       # AI agent documentation
│   └── API.md                # API reference
│
└── .claude/                  # Claude Code agents
    ├── ui-agent.md           # UI development agent
    ├── agent-agent.md        # DSPy agent development
    ├── backend-agent.md      # Tauri/Rust backend
    └── coordinator-agent.md  # Project coordination
```

## 🎨 Design System

**Style:** Hybrid Linear + Glassmorphism
- **Base:** Dark mode, high contrast, Inter Display typography
- **Cards:** Glassmorphism effect (backdrop-blur, transparency)
- **Accents:** Bold colors for priorities/labels
- **Motion:** Smooth 60fps animations, micro-interactions

**Color Palette:**
- Background: `#0a0a0b` (near-black)
- Surface: `#141415` (elevated)
- Glass: `rgba(255,255,255,0.05)` with blur
- Text: `#fafafa` (primary), `#a1a1aa` (secondary)
- Accent: `#6366f1` (indigo)
- Success: `#22c55e`
- Warning: `#eab308`
- Error: `#ef4444`

## 🛠️ Tech Stack

### Frontend
- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS 3.4
- **Components:** shadcn/ui (customized)
- **State:** Zustand
- **DnD:** @dnd-kit/core
- **Command Palette:** cmdk
- **Animation:** Framer Motion

### Backend
- **Desktop:** Tauri 2.0 (Rust)
- **Database:** SQLite (via rusqlite)
- **Agent Server:** FastAPI (Python)
- **AI Framework:** DSPy
- **Vector DB:** ChromaDB
- **LLM:** Claude API (primary), OpenAI (fallback)

## 🚀 Getting Started

```bash
# Install dependencies
cd apps/desktop && pnpm install

# Start development
pnpm tauri dev

# Start agent server (separate terminal)
cd services/agent && uv run fastapi dev
```

## 📋 Key Commands

- `⌘K` - Open command palette
- `⌘N` - New ticket
- `⌘⇧A` - Ask AI agent
- `⌘/` - Toggle sidebar
- `⌘1-4` - Switch views (Board/List/Timeline/Calendar)

## 🤖 AI Agent Capabilities

1. **Auto-triage:** Assegna automaticamente priority, labels, effort estimate
2. **Smart decompose:** Scompone task complessi in subtask
3. **Daily summary:** Genera standup summary con focus del giorno
4. **Semantic search:** Trova ticket correlati via embeddings
5. **Auto-actions:** Può creare/modificare ticket autonomamente

## 📚 Documentation

- [Product Specification](docs/SPEC.md)
- [UI Design Guidelines](docs/UI_DESIGN.md)
- [Agent Design](docs/AGENT_DESIGN.md)
- [API Reference](docs/API.md)

## 🔧 Development Agents

Usa questi agent in Claude Code per task specifici:

- **UI Agent** (`.claude/ui-agent.md`) - Sviluppo componenti React
- **Agent Agent** (`.claude/agent-agent.md`) - DSPy e AI features
- **Backend Agent** (`.claude/backend-agent.md`) - Tauri e Rust
- **Coordinator** (`.claude/coordinator-agent.md`) - Planning e overview
