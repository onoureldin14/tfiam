#!/bin/bash

# TFIAM Installer
# This script installs the tfiam tool via Homebrew

set -e

echo "🚀 Installing TFIAM - Terraform IAM Permission Analyzer..."
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install Homebrew first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
    echo "After installing Homebrew, run this script again."
    exit 1
fi

echo "✅ Homebrew is installed"

# Check if Python 3.11 is available
if ! brew list python@3.11 &> /dev/null; then
    echo "📦 Installing Python 3.11..."
    brew install python@3.11
    echo "✅ Python 3.11 installed"
else
    echo "✅ Python 3.11 is already installed"
fi

echo ""
echo "📥 Adding TFIAM tap..."
brew tap onoureldin14/tfiam

echo ""
echo "📥 Installing tfiam..."
brew install onoureldin14/tfiam/tfiam

echo ""
# Verify installation
if command -v tfiam &> /dev/null; then
    echo "✅ Installation successful!"
    echo ""
    echo "🎉 tfiam is now ready to use!"
    echo ""
    echo "📋 Quick start examples:"
    echo "  tfiam /path/to/your/terraform/repo"
    echo "  tfiam . --ai"
    echo "  tfiam --help"
    echo ""
    echo "🤖 For AI-powered analysis:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo "  tfiam . --ai"
    echo ""
    echo "🔧 Cache management:"
    echo "  tfiam . --ai --no-cache    # Clear AI cache"
    echo ""
    echo "📖 For more information:"
    echo "  https://github.com/onoureldin14/tfiam"
else
    echo "❌ Installation failed. Please check the error messages above."
    echo ""
    echo "🔍 Troubleshooting:"
    echo "  1. Make sure you have internet connection"
    echo "  2. Try running: brew update"
    echo "  3. Check if the tap exists: brew tap onoureldin14/tfiam"
    echo "  4. Try manual installation: brew install onoureldin14/tfiam/tfiam"
    exit 1
fi
