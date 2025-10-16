#!/bin/bash

# Development setup script for TFIAM
# This script sets up the development environment with pre-commit hooks

set -e

echo "🚀 Setting up TFIAM Development Environment"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created"
else
    echo "📦 Activating existing virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "📥 Installing development dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "🧪 Testing pre-commit hooks..."
pre-commit run --all-files

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  pre-commit run --all-files    # Run all hooks on all files"
echo "  pre-commit run --files FILE   # Run hooks on specific file"
echo "  pre-commit autoupdate         # Update hook versions"
echo "  black .                       # Format Python code"
echo "  isort .                       # Sort imports"
echo "  flake8 .                      # Lint Python code"
echo "  mypy .                        # Type check"
echo "  bandit .                      # Security scan"
echo ""
echo "🎉 Happy coding!"
