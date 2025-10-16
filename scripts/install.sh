#!/bin/bash

# TFIAM Installer
# This script installs the tfiam tool via Homebrew

set -e

echo "🚀 Installing TFIAM - Terraform IAM Permission Analyzer..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check if Python 3.11 is available
if ! brew list python@3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    brew install python@3.11
fi

# Install the tool
echo "📥 Installing tfiam..."
brew install --formula tfiam.rb

# Verify installation
if command -v tfiam &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "🎉 tfiam is now ready to use!"
    echo ""
    echo "Quick start:"
    echo "  tfiam /path/to/your/terraform/repo"
    echo ""
    echo "For AI explanations, set your OpenAI API key:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    echo "For more options:"
    echo "  tfiam --help"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
