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
echo "📥 Installing dependencies..."
# Install from requirements.txt (includes all dependencies)
pip install -r requirements.txt

echo ""
echo "📥 Installing additional development tools..."
# Install additional development tools not in requirements.txt
pip install pytest pytest-cov

echo ""
echo "🔧 Setting up pre-commit hooks..."
# Check if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "⚠️  No .pre-commit-config.yaml found, skipping pre-commit setup"
fi

echo ""
echo "🧪 Testing the installation..."
# Test if the main script can be imported
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from tfiam import TerraformAnalyzer, PolicyGenerator, OpenAIAnalyzer
    print('✅ All modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "📋 Available commands:"
echo "  python3 main.py --help        # Show tfiam help"
echo "  python3 main.py . --ai        # Run with AI analysis"
echo "  pytest                        # Run tests"
echo "  black .                        # Format Python code"
echo "  isort .                        # Sort imports"
echo "  flake8 .                       # Lint Python code"
echo "  mypy .                         # Type check"
echo "  bandit .                       # Security scan"
echo ""
echo "🎉 Happy coding!"
