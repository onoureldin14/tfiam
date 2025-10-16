#!/bin/bash

# Demo script for TFIAM - Terraform IAM Permission Analyzer
# This script demonstrates the tool's capabilities

set -e

echo "🚀 TFIAM - Terraform IAM Permission Analyzer Demo"
echo "================================================"
echo ""

# Check if the script exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the project directory."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

echo ""
echo "🔍 Analyzing example Terraform configuration..."
echo ""

# Run the analysis without OpenAI (for demo purposes)
echo "Command: python main.py . --no-openai"
echo "Output:"
echo "-------"
python main.py . --no-openai

echo ""
echo "📄 Generating JSON policy output..."
echo ""

# Generate JSON output
echo "Command: python main.py . --format json --output demo-policy.json"
python main.py . --format json --output demo-policy.json

echo "✅ JSON policy saved to demo-policy.json"
echo ""

# Show help
echo "📖 Available options:"
echo "Command: python main.py --help"
echo "Output:"
echo "-------"
python main.py --help

echo ""
echo "🎉 Demo completed!"
echo ""
echo "💡 Tips:"
echo "  - Set OPENAI_API_KEY environment variable for AI explanations"
echo "  - Use --output flag to save policies to files"
echo "  - Use --format json for clean JSON output"
echo "  - Use --no-openai to skip AI explanations"
echo ""
echo "🔧 After installation via Homebrew, use: tfiam instead of python main.py"
