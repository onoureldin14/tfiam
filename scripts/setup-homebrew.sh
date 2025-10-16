#!/bin/bash

# TFIAM Homebrew Tap Setup Script
# This script helps you set up a Homebrew tap for TFIAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🍺 TFIAM Homebrew Tap Setup${NC}"
echo -e "${CYAN}=============================${NC}"

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew is not installed. Please install Homebrew first:${NC}"
    echo -e "${YELLOW}   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Homebrew is installed${NC}"

# Check if we're in the right directory
if [ ! -f "tfiam.rb" ]; then
    echo -e "${RED}❌ tfiam.rb not found. Please run this script from the TFIAM project root directory.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found tfiam.rb formula${NC}"

# Step 1: Create a Homebrew tap repository
echo -e "\n${BLUE}Step 1: Setting up Homebrew tap repository${NC}"

TAP_DIR="homebrew-tfiam"

if [ -d "$TAP_DIR" ]; then
    echo -e "${YELLOW}⚠️  Tap directory already exists. Updating...${NC}"
    cd "$TAP_DIR"
    git pull origin main || true
    cd ..
else
    echo -e "${CYAN}Creating new tap repository...${NC}"

    # Create the tap directory
    mkdir -p "$TAP_DIR"
    cd "$TAP_DIR"

    # Initialize git repository
    git init
    git remote add origin "https://github.com/onoureldin14/homebrew-tfiam.git"

    # Create initial README
    cat > README.md << EOF
# Homebrew TFIAM Tap

This is the Homebrew tap for TFIAM - Terraform IAM Permission Analyzer.

## Installation

\`\`\`bash
brew tap onoureldin14/tfiam
brew install tfiam
\`\`\`

## Usage

\`\`\`bash
tfiam --help
\`\`\`

## Links

- [TFIAM Repository](https://github.com/onoureldin14/tfiam)
- [Documentation](https://github.com/onoureldin14/tfiam#readme)
EOF

    cd ..
fi

# Step 2: Copy the formula to the tap
echo -e "\n${BLUE}Step 2: Copying formula to tap${NC}"
cp tfiam.rb "$TAP_DIR/tfiam.rb"
echo -e "${GREEN}✅ Formula copied to tap directory${NC}"

# Step 3: Create installation script
echo -e "\n${BLUE}Step 3: Creating installation script${NC}"
cat > "$TAP_DIR/install.sh" << 'EOF'
#!/bin/bash
# TFIAM Installation Script

echo "🍺 Installing TFIAM via Homebrew..."

# Add the tap
brew tap onoureldin14/tfiam

# Install TFIAM
brew install tfiam

echo "✅ TFIAM installed successfully!"
echo ""
echo "Usage:"
echo "  tfiam --help          # Show help"
echo "  tfiam ./terraform-dir # Analyze Terraform directory"
echo "  tfiam ./terraform-dir -ai # With AI explanations"
echo ""
echo "For more information, visit: https://github.com/onoureldin14/tfiam"
EOF

chmod +x "$TAP_DIR/install.sh"
echo -e "${GREEN}✅ Installation script created${NC}"

# Step 4: Instructions for publishing
echo -e "\n${BLUE}Step 4: Publishing instructions${NC}"
echo -e "${YELLOW}To publish your Homebrew tap:${NC}"
echo ""
echo -e "${CYAN}1. Create the GitHub repository:${NC}"
echo -e "   Go to https://github.com/new"
echo -e "   Repository name: ${GREEN}homebrew-tfiam${NC}"
echo -e "   Description: Homebrew tap for TFIAM - Terraform IAM Permission Analyzer"
echo -e "   Make it ${GREEN}Public${NC}"
echo ""
echo -e "${CYAN}2. Push the tap repository:${NC}"
echo -e "   ${YELLOW}cd $TAP_DIR${NC}"
echo -e "   ${YELLOW}git add .${NC}"
echo -e "   ${YELLOW}git commit -m \"Initial tap setup for TFIAM\"${NC}"
echo -e "   ${YELLOW}git branch -M main${NC}"
echo -e "   ${YELLOW}git push -u origin main${NC}"
echo ""
echo -e "${CYAN}3. Test the installation:${NC}"
echo -e "   ${YELLOW}brew tap onoureldin14/tfiam${NC}"
echo -e "   ${YELLOW}brew install tfiam${NC}"
echo ""
echo -e "${CYAN}4. Update the main TFIAM repository README:${NC}"
echo -e "   Add installation instructions pointing to the tap"

# Step 5: Create a test script
echo -e "\n${BLUE}Step 5: Creating test script${NC}"
cat > "$TAP_DIR/test.sh" << 'EOF'
#!/bin/bash
# Test script for TFIAM installation

echo "🧪 Testing TFIAM installation..."

# Test if tfiam is installed
if command -v tfiam &> /dev/null; then
    echo "✅ TFIAM is installed"

    # Test help command
    if tfiam --help &> /dev/null; then
        echo "✅ Help command works"
    else
        echo "❌ Help command failed"
    fi

    # Test version
    echo "📋 TFIAM version:"
    tfiam --help | head -5

else
    echo "❌ TFIAM is not installed"
    echo "Run: brew install tfiam"
fi
EOF

chmod +x "$TAP_DIR/test.sh"
echo -e "${GREEN}✅ Test script created${NC}"

echo -e "\n${GREEN}🎉 Homebrew tap setup complete!${NC}"
echo -e "${CYAN}Next steps:${NC}"
echo -e "1. Follow the publishing instructions above"
echo -e "2. Create the GitHub repository: ${GREEN}homebrew-tfiam${NC}"
echo -e "3. Push the contents of the ${GREEN}$TAP_DIR${NC} directory"
echo -e "4. Test the installation"
echo ""
echo -e "${YELLOW}Tap directory created at: ${GREEN}$TAP_DIR${NC}"
echo -e "${YELLOW}Formula file: ${GREEN}$TAP_DIR/tfiam.rb${NC}"
