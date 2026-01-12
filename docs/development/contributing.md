# Contributing Guide

Welcome to Kanban AI! This guide will help you get started as a contributor.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Node.js 18+** (for frontend)
- **Rust 1.70+** (for Tauri backend)
- **Python 3.12+** (for AI agent)
- **pnpm** (package manager)
- **uv** (Python package manager)
- **Git**

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/kanban.git
   cd kanban
   ```

2. **Install Frontend Dependencies**
   ```bash
   cd apps/desktop
   pnpm install
   ```

3. **Install Agent Dependencies**
   ```bash
   cd services/agent
   uv sync
   ```

4. **Configure Environment**
   ```bash
   # Frontend (apps/desktop)
   cp .env.example .env

   # Agent (services/agent)
   cp .env.example .env
   # Add your API key
   ```

5. **Start Development**
   ```bash
   # Terminal 1: Start agent
   cd services/agent
   uv run fastapi dev

   # Terminal 2: Start desktop app
   cd apps/desktop
   pnpm tauri dev
   ```

---

## Project Structure

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
│           ├── src/          # Rust source
│           └── Cargo.toml    # Rust dependencies
│
├── services/
│   └── agent/                # Python AI agent
│       ├── src/
│       │   ├── agent/        # DSPy modules
│       │   ├── api/          # FastAPI routes
│       │   └── db/           # ChromaDB
│       └── tests/            # Python tests
│
├── docs/                     # Documentation (MkDocs)
└── .claude/                  # Claude Code agents
```

---

## Development Workflow

### Branch Naming

```
feature/short-description
fix/issue-number-description
docs/what-changed
refactor/what-changed
```

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(agent): add semantic search endpoint
fix(ui): resolve drag-drop flickering
docs: update installation guide
```

### Pull Request Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

3. **Push and create PR**
   ```bash
   git push -u origin feature/my-feature
   ```

4. **Fill PR template**
   - Describe changes
   - Link related issues
   - Add screenshots if UI changes

5. **Request review**
   - At least one approval required
   - CI must pass

---

## Code Standards

### TypeScript (Frontend)

- Use TypeScript strictly (no `any`)
- Follow ESLint configuration
- Use functional components
- Prefer hooks over class components

```typescript
// Good
interface Props {
  ticket: Ticket;
  onSelect: (id: string) => void;
}

export function TicketCard({ ticket, onSelect }: Props) {
  return (
    <div onClick={() => onSelect(ticket.id)}>
      {ticket.title}
    </div>
  );
}

// Avoid
export function TicketCard(props: any) { ... }
```

### Python (Agent)

- Follow PEP 8
- Use type hints
- Write docstrings
- Use Pydantic for validation

```python
# Good
def triage_ticket(
    title: str,
    description: str,
) -> TriageResult:
    """
    Automatically triage a ticket.

    Args:
        title: Ticket title
        description: Ticket description

    Returns:
        TriageResult with priority, labels, effort
    """
    ...

# Avoid
def triage_ticket(title, description):
    ...
```

### Rust (Backend)

- Follow Rust conventions
- Use `Result` for error handling
- Document public APIs
- Write tests

```rust
/// Creates a new ticket in the database.
///
/// # Arguments
/// * `data` - The ticket creation data
///
/// # Returns
/// * `Result<Ticket, Error>` - The created ticket or error
pub fn create_ticket(data: CreateTicketRequest) -> Result<Ticket, Error> {
    ...
}
```

---

## Testing

### Frontend Tests

```bash
cd apps/desktop
pnpm test              # Run tests
pnpm test:watch        # Watch mode
pnpm test:coverage     # Coverage report
```

### Agent Tests

```bash
cd services/agent
uv run pytest                  # All tests
uv run pytest tests/test_api.py  # Specific file
uv run pytest -v               # Verbose
uv run pytest --cov            # Coverage
```

### E2E Tests

```bash
cd apps/desktop
pnpm test:e2e
```

### Writing Tests

**Frontend (Vitest):**
```typescript
import { render, screen } from '@testing-library/react';
import { TicketCard } from './TicketCard';

describe('TicketCard', () => {
  it('renders ticket title', () => {
    render(<TicketCard ticket={mockTicket} />);
    expect(screen.getByText('My Ticket')).toBeInTheDocument();
  });
});
```

**Agent (pytest):**
```python
import pytest
from src.agent.modules import TriageModule

def test_triage_returns_valid_priority():
    module = TriageModule()
    result = module(title="Fix bug", description="Details")
    assert result.priority in ["low", "medium", "high", "critical"]
```

---

## Adding Features

### Frontend Component

1. Create component in `src/components/`
2. Add TypeScript types
3. Write tests
4. Export from index
5. Use in parent component

### API Endpoint

1. Add route in `services/agent/src/api/routes.py`
2. Create Pydantic models in `models.py`
3. Implement business logic
4. Write tests
5. Update documentation

### Tauri Command

1. Add command in `src-tauri/src/commands/`
2. Register in `main.rs`
3. Create TypeScript types
4. Call from frontend

---

## Documentation

### Running Docs Locally

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Open http://localhost:8000

### Writing Documentation

- Use Markdown
- Add code examples
- Include screenshots for UI
- Cross-link related pages

### Doc Structure

```
docs/
├── index.md              # Home
├── getting-started/      # Setup guides
├── user-guide/           # User documentation
├── architecture/         # Technical architecture
├── api-reference/        # API docs
├── dspy-guide/           # DSPy documentation
└── development/          # Contributor guides
```

---

## Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Write clear descriptions
- Respond to feedback promptly
- Update tests and docs

### For Reviewers

- Be constructive and kind
- Focus on:
  - Correctness
  - Performance
  - Security
  - Maintainability
- Approve when satisfied

### Review Checklist

- [ ] Code follows style guide
- [ ] Tests pass and cover changes
- [ ] Documentation updated
- [ ] No security issues
- [ ] Performance considered
- [ ] Backwards compatible

---

## Release Process

1. **Version bump**
   ```bash
   pnpm version patch|minor|major
   ```

2. **Update changelog**
   - Add new features
   - Document fixes
   - Note breaking changes

3. **Create release PR**
   - Title: `Release v1.2.3`
   - Include changelog

4. **After merge**
   - Tag release
   - Build artifacts
   - Update documentation

---

## Getting Help

### Resources

- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api-reference/rest-api.md)
- [DSPy Guide](../dspy-guide/introduction.md)

### Communication

- **Issues**: Bug reports and feature requests
- **Discussions**: Questions and ideas
- **Discord**: Real-time chat (link in README)

### When Stuck

1. Check existing issues
2. Search documentation
3. Ask in discussions
4. Reach out on Discord

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- Project README

Thank you for contributing to Kanban AI!
