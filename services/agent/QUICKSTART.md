# Kanban AI Agent - Quick Start

## 1. Setup Environment

```bash
# Navigate to agent directory
cd services/agent

# Create .env file from example
cp .env.example .env
```

## 2. Configure API Keys

Edit `.env` and add your API keys:

```bash
# Required for DSPy modules
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Optional for embeddings and fallback
OPENAI_API_KEY=sk-your-key-here
```

## 3. Install Dependencies

Using uv (recommended):

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync
```

Or using pip:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## 4. Start the Server

Development mode with auto-reload:

```bash
uv run fastapi dev src/main.py
```

Production mode:

```bash
uv run uvicorn src.main:app --host 127.0.0.1 --port 8765
```

The server will be available at: `http://localhost:8765`

## 5. Test the API

### Check Health

```bash
curl http://localhost:8765/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "kanban-agent"
}
```

### Test Auto-Triage

```bash
curl -X POST http://localhost:8765/api/triage \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "test-123",
    "title": "Fix login bug on Safari",
    "description": "Users cannot login when using Safari browser",
    "existing_labels": ["bug", "auth", "browser"]
  }'
```

Expected response:
```json
{
  "priority": "high",
  "labels": ["bug", "auth", "urgent"],
  "effort": "s",
  "reasoning": "Login issues affect user access and should be prioritized..."
}
```

### Test Task Decomposition

```bash
curl -X POST http://localhost:8765/api/decompose \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "test-456",
    "title": "Build authentication system",
    "description": "Implement OAuth with social providers",
    "context": "FastAPI backend with PostgreSQL"
  }'
```

### Test Chat

```bash
curl -X POST http://localhost:8765/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What should I focus on today?",
    "context": {
      "tickets": [],
      "current_view": "board"
    }
  }'
```

## 6. Integration with Tauri App

The Python agent runs as a sidecar process alongside the Tauri desktop app:

1. The Tauri backend starts the Python server on startup
2. Frontend communicates via Tauri IPC to Rust backend
3. Rust backend forwards requests to Python agent via HTTP

```
React Frontend
    ↓ Tauri IPC
Rust Backend (Tauri)
    ↓ HTTP localhost:8765
Python Agent (FastAPI)
    ↓ API calls
Claude API / OpenAI API
```

## Troubleshooting

### Import Error: dspy not found

```bash
# Reinstall dependencies
uv sync --refresh
```

### ChromaDB Permission Error

```bash
# Ensure data directory is writable
mkdir -p data/chroma
chmod 755 data/chroma
```

### API Key Error

```bash
# Verify .env file exists and contains valid keys
cat .env | grep API_KEY
```

### Port Already in Use

```bash
# Change port in .env
PORT=8766

# Or kill existing process
lsof -ti:8765 | xargs kill -9
```

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [AGENT_DESIGN.md](../../docs/AGENT_DESIGN.md) for architecture details
3. Explore the API at `http://localhost:8765/docs` (FastAPI auto-generated docs)
4. Run tests: `uv run pytest`

## Development Workflow

```bash
# Install dev dependencies
uv sync --all-extras

# Format code
uv run ruff format src/

# Lint
uv run ruff check src/ --fix

# Type check
uv run mypy src/

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Production Deployment

For production use with the Tauri app:

```bash
# Build standalone binary
uv build

# Or use uvicorn with process manager
uv run uvicorn src.main:app \
  --host 127.0.0.1 \
  --port 8765 \
  --workers 1 \
  --no-access-log
```

Note: The Tauri app will handle starting/stopping the Python sidecar automatically.
