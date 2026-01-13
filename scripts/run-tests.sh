#!/bin/bash

set -e

echo "Running tests for Receipt Processor Lambda..."

# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
echo "Running code quality checks..."
black --check src tests
flake8 src tests --max-line-length=100 --exclude=__pycache__
pylint src --max-line-length=100

# Run unit tests with coverage
echo "Running unit tests..."
pytest tests/unit -v --cov=src --cov-report=html --cov-report=term-missing

# Run integration tests (if any)
if [ -d "tests/integration" ] && [ "$(ls -A tests/integration/*.py 2>/dev/null)" ]; then
    echo "Running integration tests..."
    pytest tests/integration -v
fi

echo "All tests passed!"
