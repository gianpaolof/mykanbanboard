.PHONY: help install dev test lint format clean run examples

help: ## Show this help message
	@echo "Kanban AI Agent - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing dependencies..."
	uv sync

dev: ## Install with dev dependencies
	@echo "Installing with dev dependencies..."
	uv sync --all-extras

test: ## Run tests
	@echo "Running tests..."
	uv run pytest

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	uv run pytest --cov=src --cov-report=html --cov-report=term

lint: ## Run linter
	@echo "Running linter..."
	uv run ruff check src/ tests/

lint-fix: ## Run linter with auto-fix
	@echo "Running linter with auto-fix..."
	uv run ruff check src/ tests/ --fix

format: ## Format code
	@echo "Formatting code..."
	uv run ruff format src/ tests/ examples/

type-check: ## Run type checker
	@echo "Running type checker..."
	uv run mypy src/

check: lint type-check ## Run all checks (lint + type-check)

clean: ## Clean generated files
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

run: ## Run the server in development mode
	@echo "Starting server..."
	uv run fastapi dev src/main.py

run-prod: ## Run the server in production mode
	@echo "Starting server (production)..."
	uv run uvicorn src.main:app --host 127.0.0.1 --port 8765

examples: ## Run basic usage examples
	@echo "Running examples..."
	uv run python examples/basic_usage.py

setup-env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "✓ .env created. Please edit it with your API keys."; \
	else \
		echo "⚠️  .env already exists"; \
	fi

health-check: ## Check if server is running
	@echo "Checking server health..."
	@curl -s http://localhost:8765/api/health | python -m json.tool || echo "❌ Server not running"

api-docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@python -c "import webbrowser; webbrowser.open('http://localhost:8765/docs')"

build: ## Build distribution package
	@echo "Building package..."
	uv build

all: clean install lint test ## Clean, install, lint, and test
