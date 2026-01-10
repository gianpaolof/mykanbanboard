#!/bin/bash
# Quick start script for Kanban AI Agent

set -e

echo "=================================================="
echo "Kanban AI Agent - Quick Start"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (required)"
    echo "   - OPENAI_API_KEY (optional)"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo ""
    echo "Install uv with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync
echo "✓ Dependencies installed"
echo ""

# Start server
echo "🚀 Starting Kanban AI Agent..."
echo ""
echo "Server will be available at: http://localhost:8765"
echo "API docs: http://localhost:8765/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run fastapi dev src/main.py
