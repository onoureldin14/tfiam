#!/bin/bash

# Test script for OpenAI integration
set -e

echo "🧪 Testing OpenAI Integration with TFIAM"
echo "========================================"
echo ""

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
echo "🔑 OpenAI API Key Options:"
echo "1. Set environment variable: export OPENAI_API_KEY='your-key'"
echo "2. Pass directly: python main.py . --openai-key your-key"
echo "3. Skip OpenAI: python main.py . --no-openai"
echo ""

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set."
    echo ""
    echo "To test OpenAI integration, you have these options:"
    echo ""
    echo "Option 1 - Set environment variable:"
    echo "  export OPENAI_API_KEY='your-openai-api-key'"
    echo "  python main.py . --format explained"
    echo ""
    echo "Option 2 - Pass key directly:"
    echo "  python main.py . --openai-key your-openai-api-key --format explained"
    echo ""
    echo "Option 3 - Test without OpenAI (default explanations):"
    echo "  python main.py . --no-openai --format explained"
    echo ""

    # Test without OpenAI first
    echo "🧪 Testing without OpenAI (default explanations):"
    echo "Command: python main.py . --no-openai --format explained | head -30"
    echo "Output:"
    echo "-------"
    python main.py . --no-openai --format explained | head -30

else
    echo "✅ OPENAI_API_KEY is set. Testing with AI explanations..."
    echo ""
    echo "🧪 Testing with OpenAI explanations:"
    echo "Command: python main.py . --format explained | head -30"
    echo "Output:"
    echo "-------"
    python main.py . --format explained | head -30
fi

echo ""
echo "🎯 To see full output with AI explanations, run:"
echo "  python main.py . --format explained --output ai-policy.json"
echo ""
echo "📄 To see clean JSON without explanations, run:"
echo "  python main.py . --format json --output clean-policy.json"
