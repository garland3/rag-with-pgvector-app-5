#!/bin/bash

set -e

echo "🚀 Starting devcontainer setup..."

# Start PostgreSQL
echo "📦 Starting PostgreSQL..."
docker compose up -d postgres

# Run application setup
echo "🔧 Running application setup..."
./scripts/setup.sh

# Install Claude Code
echo "🤖 Installing Claude Code..."
if ! command -v claude &> /dev/null; then
    echo "Installing Claude Code CLI via npm..."
    npm install -g @anthropic-ai/claude-code
    echo "✅ Claude Code installed successfully!"
else
    echo "✅ Claude Code already installed"
fi

# Verify installation
echo "🔍 Verifying installations..."
python --version
docker --version
node --version
npm --version
psql --version 2>/dev/null || echo "⚠️  psql not found in PATH"

if command -v claude &> /dev/null; then
    claude --version
    echo "✅ Claude Code is ready to use!"
    echo "💡 Tip: Run 'claude' to start Claude Code in interactive mode"
else
    echo "⚠️  Claude Code installation failed"
fi

echo "🎉 Devcontainer setup complete!"