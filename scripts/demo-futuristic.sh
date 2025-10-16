#!/bin/bash

# Futuristic Demo Script for TFIAM
# This script showcases the new cyberpunk-style CLI interface

set -e

echo "🚀 TFIAM Futuristic Demo"
echo "========================"
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
echo "🎯 Demo 1: Full Futuristic Experience"
echo "====================================="
echo ""

# Run with full futuristic interface
echo "Command: python main.py . --no-openai"
echo ""
python main.py . --no-openai

echo ""
echo "🎯 Demo 2: Quiet Mode"
echo "===================="
echo ""

# Run in quiet mode
echo "Command: python main.py . --no-openai --quiet"
echo ""
python main.py . --no-openai --quiet

echo ""
echo "🎯 Demo 3: Custom Output Directory"
echo "================================="
echo ""

# Run with custom output directory
echo "Command: python main.py . --no-openai --output-dir ./demo-output"
echo ""
python main.py . --no-openai --output-dir ./demo-output

echo ""
echo "📁 Generated Files:"
echo "=================="
echo ""

if [ -d "tfiam-output" ]; then
    echo "Standard output directory (tfiam-output/):"
    ls -la tfiam-output/
    echo ""
fi

if [ -d "demo-output" ]; then
    echo "Demo output directory (demo-output/):"
    ls -la demo-output/
    echo ""
fi

echo "🎉 Demo completed!"
echo ""
echo "💡 Key Features Demonstrated:"
echo "  ✅ Futuristic cyberpunk-style CLI interface"
echo "  ✅ Colorful terminal output with Unicode box drawing"
echo "  ✅ Multiple JSON output files with different purposes"
echo "  ✅ Quiet mode for automation/scripting"
echo "  ✅ Custom output directories"
echo "  ✅ Comprehensive analysis reports"
echo ""
echo "🔧 Try these commands:"
echo "  python main.py --help                    # See all options"
echo "  python main.py . --openai-key YOUR_KEY   # With AI explanations"
echo "  python main.py . --quiet                 # Minimal output"
echo "  python main.py . --output-dir ./custom   # Custom directory"
