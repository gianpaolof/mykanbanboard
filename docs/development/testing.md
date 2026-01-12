# Testing Guide

Comprehensive guide to testing in Kanban AI.

## Overview

Kanban AI uses multiple testing approaches:

| Component | Framework | Type |
|-----------|-----------|------|
| Frontend | Vitest + Testing Library | Unit, Integration |
| Agent | pytest | Unit, Integration |
| E2E | Playwright | End-to-end |
| Rust | Cargo test | Unit |

---

## Frontend Testing

### Setup

Tests are configured in `apps/desktop/vite.config.ts`:

```typescript
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
});
```

### Running Tests

```bash
cd apps/desktop

# Run all tests
pnpm test

# Watch mode
pnpm test:watch

# With coverage
pnpm test:coverage

# Specific file
pnpm test src/components/TicketCard.test.tsx

# Pattern matching
pnpm test -t "TicketCard"
```

### Writing Component Tests

```typescript
// src/components/TicketCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TicketCard } from './TicketCard';

const mockTicket = {
  id: '1',
  title: 'Test Ticket',
  description: 'Description',
  priority: 'high' as const,
  columnId: 'col1',
  position: 0,
  labels: [],
  comments: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

describe('TicketCard', () => {
  it('renders ticket title', () => {
    render(<TicketCard ticket={mockTicket} />);
    expect(screen.getByText('Test Ticket')).toBeInTheDocument();
  });

  it('shows priority badge', () => {
    render(<TicketCard ticket={mockTicket} />);
    expect(screen.getByTestId('priority-badge')).toHaveTextContent('high');
  });

  it('calls onSelect when clicked', () => {
    const onSelect = vi.fn();
    render(<TicketCard ticket={mockTicket} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('article'));

    expect(onSelect).toHaveBeenCalledWith('1');
  });

  it('shows labels', () => {
    const ticketWithLabels = {
      ...mockTicket,
      labels: [{ id: 'l1', name: 'bug', color: '#ff0000' }],
    };

    render(<TicketCard ticket={ticketWithLabels} />);
    expect(screen.getByText('bug')).toBeInTheDocument();
  });
});
```

### Testing Hooks

```typescript
// src/hooks/useTickets.test.ts
import { renderHook, act } from '@testing-library/react';
import { useTickets } from './useTickets';

describe('useTickets', () => {
  it('initializes with empty array', () => {
    const { result } = renderHook(() => useTickets());
    expect(result.current.tickets).toEqual([]);
  });

  it('adds ticket', () => {
    const { result } = renderHook(() => useTickets());

    act(() => {
      result.current.addTicket({
        title: 'New Ticket',
        columnId: 'col1',
      });
    });

    expect(result.current.tickets).toHaveLength(1);
    expect(result.current.tickets[0].title).toBe('New Ticket');
  });
});
```

### Testing Stores (Zustand)

```typescript
// src/stores/ticketStore.test.ts
import { useTicketStore } from './ticketStore';

describe('ticketStore', () => {
  beforeEach(() => {
    useTicketStore.getState().reset();
  });

  it('adds ticket to store', () => {
    const { addTicket, tickets } = useTicketStore.getState();

    addTicket({
      title: 'Test',
      columnId: 'col1',
    });

    expect(useTicketStore.getState().tickets).toHaveLength(1);
  });

  it('moves ticket between columns', () => {
    const { addTicket, moveTicket, tickets } = useTicketStore.getState();

    addTicket({ title: 'Test', columnId: 'col1' });
    const ticketId = useTicketStore.getState().tickets[0].id;

    moveTicket(ticketId, 'col2', 0);

    expect(useTicketStore.getState().tickets[0].columnId).toBe('col2');
  });
});
```

### Mocking Tauri

```typescript
// src/test/setup.ts
import { vi } from 'vitest';

// Mock Tauri invoke
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn((command: string, args?: unknown) => {
    switch (command) {
      case 'get_tickets':
        return Promise.resolve([]);
      case 'create_ticket':
        return Promise.resolve({ id: '1', ...args });
      default:
        return Promise.resolve(null);
    }
  }),
}));
```

---

## Agent Testing (Python)

### Setup

Tests use pytest with fixtures in `services/agent/tests/conftest.py`:

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_ticket():
    return {
        "ticket_id": "test-123",
        "title": "Test ticket",
        "description": "Test description",
    }
```

### Running Tests

```bash
cd services/agent

# All tests
uv run pytest

# Verbose
uv run pytest -v

# Specific file
uv run pytest tests/test_api.py

# Specific test
uv run pytest tests/test_api.py::test_health_check

# With coverage
uv run pytest --cov=src --cov-report=html

# Parallel
uv run pytest -n auto
```

### API Tests

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_triage_endpoint(client, mock_ticket):
    response = client.post("/api/triage", json=mock_ticket)
    assert response.status_code == 200

    data = response.json()
    assert data["priority"] in ["low", "medium", "high", "critical"]
    assert len(data["labels"]) <= 3
    assert data["effort"] in ["xs", "s", "m", "l", "xl"]

def test_triage_validation_error(client):
    # Missing required title
    response = client.post("/api/triage", json={"description": "test"})
    assert response.status_code == 422
```

### Module Tests

```python
# tests/test_modules.py
import pytest
from unittest.mock import patch, MagicMock
from src.agent.modules import TriageModule, DecomposeModule

class TestTriageModule:
    @pytest.fixture
    def module(self):
        return TriageModule()

    def test_returns_valid_priority(self, module):
        result = module(
            title="Fix critical bug",
            description="System crashes on login",
            existing_labels=["bug", "auth"]
        )

        assert result.priority in ["low", "medium", "high", "critical"]

    def test_respects_existing_labels(self, module):
        existing = ["frontend", "backend", "api"]
        result = module(
            title="Add new feature",
            description="Details",
            existing_labels=existing
        )

        # Should prefer existing labels when applicable
        for label in result.labels:
            assert label in existing or isinstance(label, str)

    def test_handles_empty_description(self, module):
        result = module(
            title="Simple task",
            description="",
            existing_labels=[]
        )

        assert result.priority is not None
        assert result.effort is not None

class TestDecomposeModule:
    @pytest.fixture
    def module(self):
        return DecomposeModule()

    def test_generates_subtasks(self, module):
        result = module(
            title="Implement auth",
            description="Add login and signup",
            context=""
        )

        assert len(result.subtasks) > 0
        assert len(result.subtasks) <= 7  # Max limit

    def test_subtask_has_required_fields(self, module):
        result = module(
            title="Build feature",
            description="Details",
            context=""
        )

        for subtask in result.subtasks:
            assert "title" in subtask
            assert "description" in subtask
            assert "effort" in subtask
```

### Mocking DSPy

```python
# tests/test_modules_mocked.py
from unittest.mock import patch, MagicMock

@patch('dspy.configure')
def test_module_with_mocked_llm(mock_configure):
    # Create mock LLM response
    mock_lm = MagicMock()
    mock_lm.return_value = MagicMock(
        priority="high",
        labels=["bug", "frontend"],
        effort="m",
        reasoning="Test reasoning"
    )

    with patch.object(TriageModule, '__call__', mock_lm):
        module = TriageModule()
        result = module(title="Test", description="Test", existing_labels=[])

        assert result.priority == "high"
```

### ChromaDB Tests

```python
# tests/test_chroma.py
import pytest
from src.db.chroma import ChromaManager

@pytest.fixture
def chroma():
    # Use temp directory for tests
    manager = ChromaManager(persist_directory="/tmp/test_chroma")
    yield manager
    manager.clear()

def test_add_and_search(chroma):
    # Add document
    chroma.add(
        id="ticket-1",
        document="Fix login bug on Safari",
        metadata={"title": "Login Bug"}
    )

    # Search
    results = chroma.search("authentication issues", limit=5)

    assert len(results) > 0
    assert results[0]["id"] == "ticket-1"

def test_update_document(chroma):
    chroma.add(id="ticket-1", document="Original text")
    chroma.update(id="ticket-1", document="Updated text")

    results = chroma.search("Updated text")
    assert results[0]["id"] == "ticket-1"
```

---

## End-to-End Testing

### Setup

E2E tests use Playwright in `apps/desktop/e2e/`:

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:5173',
  },
});
```

### Running E2E Tests

```bash
cd apps/desktop

# Run all E2E tests
pnpm test:e2e

# With UI
pnpm test:e2e --ui

# Specific test
pnpm test:e2e e2e/board.spec.ts

# Debug mode
pnpm test:e2e --debug
```

### Writing E2E Tests

```typescript
// e2e/board.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Board', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('creates new ticket', async ({ page }) => {
    // Open new ticket dialog
    await page.keyboard.press('n');

    // Fill form
    await page.fill('[data-testid="ticket-title"]', 'New Test Ticket');
    await page.fill('[data-testid="ticket-description"]', 'Description');

    // Submit
    await page.click('[data-testid="create-ticket"]');

    // Verify ticket appears
    await expect(page.locator('text=New Test Ticket')).toBeVisible();
  });

  test('drags ticket between columns', async ({ page }) => {
    // Create a ticket first
    await page.keyboard.press('n');
    await page.fill('[data-testid="ticket-title"]', 'Drag Test');
    await page.click('[data-testid="create-ticket"]');

    // Drag to next column
    const ticket = page.locator('text=Drag Test');
    const targetColumn = page.locator('[data-testid="column-in-progress"]');

    await ticket.dragTo(targetColumn);

    // Verify ticket moved
    await expect(targetColumn.locator('text=Drag Test')).toBeVisible();
  });

  test('opens command palette', async ({ page }) => {
    await page.keyboard.press('Meta+k');
    await expect(page.locator('[data-testid="command-palette"]')).toBeVisible();
  });
});
```

### E2E with AI Features

```typescript
// e2e/ai-features.spec.ts
test.describe('AI Features', () => {
  test('triages ticket automatically', async ({ page }) => {
    await page.goto('/');

    // Create ticket
    await page.keyboard.press('n');
    await page.fill('[data-testid="ticket-title"]', 'Critical bug in auth');
    await page.fill('[data-testid="ticket-description"]', 'Login fails');
    await page.click('[data-testid="create-ticket"]');

    // Wait for AI triage
    await page.waitForSelector('[data-testid="priority-badge"]', {
      timeout: 15000, // AI can be slow
    });

    // Verify priority was set
    const priority = await page.locator('[data-testid="priority-badge"]').textContent();
    expect(['high', 'critical']).toContain(priority);
  });
});
```

---

## Rust Backend Testing

### Running Tests

```bash
cd apps/desktop/src-tauri

# Run all tests
cargo test

# Specific test
cargo test test_create_ticket

# With output
cargo test -- --nocapture
```

### Writing Tests

```rust
// src-tauri/src/commands/tickets.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_ticket() {
        let data = CreateTicketRequest {
            title: "Test".to_string(),
            description: Some("Description".to_string()),
            column_id: "col1".to_string(),
            priority: None,
            labels: vec![],
            effort: None,
            due_date: None,
        };

        let result = create_ticket_sync(data);
        assert!(result.is_ok());

        let ticket = result.unwrap();
        assert_eq!(ticket.title, "Test");
    }

    #[test]
    fn test_validate_priority() {
        assert!(validate_priority("low").is_ok());
        assert!(validate_priority("invalid").is_err());
    }
}
```

---

## Test Coverage

### Frontend Coverage

```bash
cd apps/desktop
pnpm test:coverage
```

Coverage report at `coverage/index.html`.

### Agent Coverage

```bash
cd services/agent
uv run pytest --cov=src --cov-report=html
```

Coverage report at `htmlcov/index.html`.

### Coverage Targets

| Component | Target |
|-----------|--------|
| Core business logic | 80%+ |
| API endpoints | 90%+ |
| UI components | 70%+ |
| Utils/helpers | 60%+ |

---

## CI/CD Testing

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm test

  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: |
          cd services/agent
          uv sync
          uv run pytest

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm exec playwright install
      - run: pnpm test:e2e
```

---

## Best Practices

### Test Organization

```
tests/
├── unit/              # Isolated unit tests
├── integration/       # Component integration
├── e2e/               # End-to-end flows
└── fixtures/          # Shared test data
```

### Test Naming

```typescript
// Describe what is being tested
describe('TicketCard', () => {
  // Describe behavior
  it('renders ticket title', () => {});
  it('calls onSelect when clicked', () => {});
  it('shows loading state during triage', () => {});
});
```

### Avoid

- Testing implementation details
- Flaky tests (use proper waits)
- Over-mocking (test real behavior)
- Tests that depend on order

### Do

- Test user behavior
- Use meaningful assertions
- Keep tests focused
- Clean up after tests

---

## Debugging Tests

### Frontend

```bash
# Debug specific test
pnpm test --inspect-brk src/components/TicketCard.test.tsx
```

### Agent

```bash
# Debug with pdb
uv run pytest --pdb tests/test_api.py

# Verbose output
uv run pytest -vvs tests/test_api.py
```

### E2E

```bash
# Debug mode with Playwright inspector
pnpm test:e2e --debug

# Headed mode
pnpm test:e2e --headed
```

---

## Related Documentation

- [Contributing Guide](contributing.md) - Development workflow
- [Architecture](../architecture/overview.md) - System architecture
- [API Reference](../api-reference/rest-api.md) - API documentation
