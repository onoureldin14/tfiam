#!/bin/bash

# Development setup script for TFIAM
# This script sets up the development environment with pre-commit hooks

set -e

# Change to the project root directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Setting up TFIAM Development Environment"
echo "=========================================="
echo ""

# Change to project root
cd "$PROJECT_ROOT"
echo "📁 Working directory: $(pwd)"

# Verify we're in the right place
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found in project root"
    echo "   Make sure you're running this from the TFIAM project directory"
    echo "   Expected location: $PROJECT_ROOT"
    exit 1
fi

echo "✅ Found project files"
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
