#!/bin/bash

set -e

echo "🧪 Running test suite..."

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements-test.txt

# Setup test database
echo "🗄️ Setting up test database..."
./scripts/setup-test-db.sh

# Set PYTHONPATH for imports
export PYTHONPATH=.

# Set testing environment variables
export TESTING=true
export BYPASS_AUTH=true

# Run tests with different options based on arguments
if [ "$1" = "unit" ]; then
    echo "🔬 Running unit tests only..."
    pytest -m "unit" --tb=short
elif [ "$1" = "api" ]; then
    echo "🌐 Running API tests only..."
    pytest -m "api" --tb=short
elif [ "$1" = "auth" ]; then
    echo "🔐 Running auth tests only..."
    pytest -m "auth" --tb=short
elif [ "$1" = "coverage" ]; then
    echo "📊 Running tests with coverage report..."
    pytest --cov=. --cov-report=html --cov-report=term-missing
elif [ "$1" = "ci" ]; then
    echo "🤖 Running CI test suite..."
    pytest --tb=short --maxfail=5 -q
else
    echo "🎯 Running full test suite..."
    pytest
fi

echo "✅ Test run completed!"