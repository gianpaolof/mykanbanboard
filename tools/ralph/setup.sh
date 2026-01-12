#!/bin/bash

# Ralph Project Setup Script - Global Version
set -e

PROJECT_NAME=${1:-"my-project"}
RALPH_HOME="$HOME/.ralph"

echo "🚀 Setting up Ralph project: $PROJECT_NAME"

# Create project directory in current location
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create structure
mkdir -p {specs/stdlib,src,examples,logs,docs/generated}

# Copy templates from Ralph home
cp "$RALPH_HOME/templates/PROMPT.md" .
cp "$RALPH_HOME/templates/fix_plan.md" @fix_plan.md
cp "$RALPH_HOME/templates/AGENT.md" @AGENT.md
cp -r "$RALPH_HOME/templates/specs/"* specs/ 2>/dev/null || true

# Initialize git
git init
echo "# $PROJECT_NAME" > README.md
git add .
git commit -m "Initial Ralph project setup"

echo "✅ Project $PROJECT_NAME created!"
echo "Next steps:"
echo "  1. Edit PROMPT.md with your project requirements"
echo "  2. Update specs/ with your project specifications"  
echo "  3. Run: ralph --monitor"
echo "  4. Monitor: ralph-monitor (if running manually)"
