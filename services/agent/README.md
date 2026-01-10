# Kanban AI Agent

DSPy-based AI agent for intelligent task management.

## Features

- **Auto-Triage**: Automatically assign priority, labels, and effort estimates to tickets
- **Task Decomposition**: Break down complex tasks into actionable subtasks
- **Daily Summary**: Generate personalized work summaries
- **Semantic Search**: Find related tickets using vector embeddings
- **Chat Interface**: Natural language interaction with action detection

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Anthropic API key (required)
- OpenAI API key (optional, for embeddings and fallback)

### Installation

```bash
# Install dependencies with uv
uv sync

# Create .env file
cp .env.example .env

# Add your API keys to .env
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

### Running the Server

```bash
# Development mode with auto-reload
uv run fastapi dev src/main.py

# Production mode
uv run uvicorn src.main:app --host 127.0.0.1 --port 8765
```

The server will start at `http://localhost:8765`

## API Endpoints

### Health Check
```bash
GET /api/health
```

### Auto-Triage
```bash
POST /api/triage
Content-Type: application/json

{
  "ticket_id": "uuid",
  "title": "Fix login bug",
  "description": "Users can't login on Safari",
  "existing_labels": ["bug", "auth"]
}
```

### Task Decomposition
```bash
POST /api/decompose
Content-Type: application/json

{
  "ticket_id": "uuid",
  "title": "Build authentication system",
  "description": "Implement user auth with OAuth",
  "context": "Using FastAPI backend"
}
```

### Chat
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What should I focus on today?",
  "context": {
    "tickets": [...],
    "current_view": "board"
  }
}
```

### Semantic Search
```bash
POST /api/search
Content-Type: application/json

{
  "query": "performance issues",
  "limit": 5
}
```

### Daily Summary
```bash
GET /api/daily-summary
```

## Project Structure

```
services/agent/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── modules.py         # DSPy modules (Triage, Decompose, etc.)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic models for API
│   │   └── routes.py          # FastAPI routes
│   ├── db/
│   │   ├── __init__.py
│   │   └── chroma.py          # ChromaDB integration
│   ├── __init__.py
│   ├── config.py              # Configuration with pydantic-settings
│   └── main.py                # FastAPI application
├── tests/                      # Unit and integration tests
├── data/                       # ChromaDB storage (created on first run)
├── pyproject.toml             # Project configuration
└── README.md
```

## DSPy Modules

### TriageModule
Automatically categorizes tickets with:
- Priority (low, medium, high, critical)
- Labels (max 3, prefers existing ones)
- Effort estimate (xs, s, m, l, xl)
- Reasoning for decisions

### DecomposeModule
Breaks down tasks into:
- Actionable subtasks
- Dependencies between subtasks
- Effort estimates per subtask

### DailySummaryModule
Generates daily summaries with:
- Personalized greeting
- Top 3 priorities
- Blockers to address
- Quick wins

### ActionDeciderModule
Chat interface that:
- Detects user intent
- Decides which action to take
- Provides natural language responses

## Configuration

Environment variables (`.env`):

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=claude-sonnet-4-20250514
FALLBACK_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Server
PORT=8765
HOST=127.0.0.1
DEBUG=false

# ChromaDB
CHROMA_PATH=./data/chroma
CHROMA_COLLECTION=tickets

# Behavior
AUTO_TRIAGE_ENABLED=true
MAX_DECOMPOSE_SUBTASKS=7
SEARCH_RESULTS_LIMIT=10
MAX_REQUESTS_PER_MINUTE=20
```

## Development

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_triage.py
```

### Code Quality
```bash
# Format code
uv run ruff format src/

# Lint code
uv run ruff check src/

# Type checking
uv run mypy src/
```

## Architecture

The agent uses DSPy for structured prompting:

1. **Signatures** define input/output schemas with type safety
2. **Modules** implement the logic using ChainOfThought or other predictors
3. **LM Configuration** uses Claude Sonnet as primary, GPT-4 as fallback
4. **Vector Store** uses ChromaDB for semantic search

## Integration with Kanban AI

The agent runs as a sidecar service alongside the Tauri desktop app:

```
Frontend (React)
    ↓ Tauri IPC
Rust Backend
    ↓ HTTP (localhost:8765)
Python Agent (FastAPI)
```

## License

MIT
