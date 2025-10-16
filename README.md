# TFIAM - Terraform IAM Permission Analyzer

A powerful, modular tool that scans Terraform repositories and recommends IAM permissions with AI-powered explanations for complete resource management.

## 🌟 Features

- 🔍 **Smart Analysis**: Automatically scans Terraform files to identify AWS resources
- 🤖 **AI Explanations**: Uses OpenAI to provide detailed explanations for each permission set
- 📋 **Comprehensive Coverage**: Supports 40+ AWS services with detailed permissions
- 🎯 **Scoped Permissions**: Generates resource-specific ARNs with dynamic account and region placeholders
- 🏗️ **Modular Architecture**: Clean, maintainable codebase with proper separation of concerns
- 📊 **Multiple Output Formats**: JSON policy output and detailed Markdown reports
- 🏠 **Homebrew Integration**: Easy installation via Homebrew

## 📁 Project Structure

```text
tf-ai-permssions/
├── src/tfiam/           # Main package (modular architecture)
│   ├── core/            # Core business logic
│   │   ├── models.py         # Data models (IAMStatement, TerraformResource)
│   │   ├── analyzer.py       # Terraform analysis logic (397 lines)
│   │   ├── policy_generator.py # IAM policy generation (74 lines)
│   │   └── openai_analyzer.py # AI integration (65 lines)
│   ├── utils/           # Utility functions
│   │   ├── aws_permissions.py # Comprehensive AWS permissions (704 lines)
│   │   └── arn_builder.py    # ARN building utilities (80 lines)
│   └── cli/             # CLI components
│       └── cyber_cli.py      # Cyberpunk-themed interface (94 lines)
├── tests/               # Comprehensive test suite
│   ├── test_analyzer.py      # Tests for TerraformAnalyzer
│   ├── test_policy_generator.py # Tests for PolicyGenerator
│   └── test_utils.py         # Tests for utility modules
├── scripts/             # Utility scripts
│   ├── demo.sh              # Basic demonstration script
│   ├── demo-futuristic.sh   # Enhanced demonstration with cyberpunk theme
│   ├── install.sh           # Installation script for Homebrew
│   ├── setup-dev.sh         # Development environment setup
│   ├── test_openai.sh       # OpenAI integration testing
│   └── tfiam.rb             # Homebrew formula for distribution
├── examples/            # Example Terraform files
│   ├── test_example.tf      # Comprehensive example with various AWS services
│   ├── test_grouping.tf     # Tests resource grouping and ARN generation
│   ├── test_with_variables.tf # Tests variable and local resolution
│   └── test_dynamic.tf      # Tests dynamic permission generation for new AWS services
├── docs/                # Documentation
│   ├── CHANGELOG.md         # Project changelog and version history
│   └── PROJECT_STRUCTURE.md # Detailed project architecture and structure
├── main.py              # Clean entry point (133 lines)
├── Makefile             # Common tasks
├── pytest.ini          # Test configuration
└── requirements.txt     # Dependencies
```

## 🏗️ Architecture

### Core Modules (`src/tfiam/core/`)

- **`models.py`**: Data classes for IAM statements and Terraform resources
- **`analyzer.py`**: Main Terraform analysis engine with dynamic permission mapping
- **`policy_generator.py`**: IAM policy generation and report creation
- **`openai_analyzer.py`**: OpenAI integration for AI-powered explanations

### Utility Modules (`src/tfiam/utils/`)

- **`aws_permissions.py`**: Comprehensive AWS service permissions mapping
- **`arn_builder.py`**: ARN construction utilities for specific and wildcard resources

### CLI Components (`src/tfiam/cli/`)

- **`cyber_cli.py`**: Cyberpunk-themed terminal interface with colors and formatting

## 🚀 Benefits of Modular Structure

1. **Modularity**: Each component has a single responsibility
2. **Maintainability**: Easy to find and modify specific functionality
3. **Testability**: Individual modules can be tested in isolation
4. **Extensibility**: New features can be added without affecting existing code
5. **Readability**: Clean separation of concerns makes code easier to understand

## 📊 Code Size Comparison

- **Original `main.py`**: ~1,150 lines (monolithic)
- **New `main.py`**: 133 lines (clean entry point)
- **Total modular code**: 1,496 lines across 11 focused files

## 🚀 Quick Start

### Installation

```bash
# Via Homebrew (recommended)
brew install yourusername/tfiam/tfiam

# Manual installation
git clone https://github.com/yourusername/tfiam.git
cd tfiam
pip3 install -r requirements.txt
```

### Basic Usage

```bash
# Interactive mode (no arguments required)
python main.py

# Analyze a Terraform directory
python main.py ./my-terraform-project

# With AI explanations (requires OpenAI API key)
python main.py ./my-terraform-project -ai

# Skip AI explanations (default)
python main.py ./my-terraform-project -no-ai

# Quiet mode with custom output directory
python main.py ./my-terraform-project --output-dir policies --quiet
```

### Examples

```bash
# Interactive mode with examples
python main.py

# Test with included examples
python main.py examples/ -no-ai

# Test with comprehensive example
python main.py examples/test_example.tf -no-ai

# Test with variables and locals
python main.py examples/test_with_variables.tf -no-ai

# Test dynamic permissions
python main.py examples/test_dynamic.tf -no-ai

# Analyze specific file with AI
python main.py examples/test_example.tf -ai

# Get help
python main.py --help
```

## 🛠️ Development

### Quick Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/tfiam.git
cd tfiam
make dev-setup
```

### Available Commands

```bash
make help              # Show all available commands
make test              # Run tests
make test-coverage     # Run tests with coverage
make lint              # Run linting
make format            # Format code
make clean             # Clean temporary files
make demo              # Run demo
make test-examples     # Test with example files
make check             # Run linting and tests
make all               # Full setup and test
```

### Manual Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Test specific module
python -m pytest tests/test_analyzer.py -v

# Test examples
make test-examples
```

Each module can be tested independently:

```python
from src.tfiam.core.analyzer import TerraformAnalyzer
from src.tfiam.utils.aws_permissions import AWS_PERMISSIONS
from src.tfiam.cli.cyber_cli import CyberCLI
```

## 📊 Code Quality

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Bandit**: Security linting
- **pytest**: Testing framework

Run all quality checks:

```bash
make check
```

## 🎯 Supported AWS Services

TFIAM supports 40+ AWS services including:

**Compute**: EC2, Lambda, ECS, EKS, Batch, Fargate
**Storage**: S3, EBS, EFS, FSx
**Database**: RDS, DynamoDB, ElastiCache, Redshift
**Networking**: VPC, Route53, CloudFront, API Gateway
**Security**: IAM, KMS, Secrets Manager, WAF
**Monitoring**: CloudWatch, CloudTrail, X-Ray
**Management**: CloudFormation, Systems Manager, Organizations
**Analytics**: Kinesis, Athena, EMR
**AI/ML**: SageMaker, Comprehend, Rekognition

## 📋 Output Formats

### JSON Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Bucket",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket"
      ]
    }
  ]
}
```

### Markdown Report

Detailed analysis with AI explanations, security notes, and service breakdowns.

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for AI explanations

### Command Line Options

- `-ai`: Enable AI explanations (requires OpenAI API key)
- `-no-ai`: Skip AI analysis (default)
- `--output-dir DIR`: Output directory (default: tfiam-output)
- `--quiet, -q`: Minimal output
- `--help, -h`: Show help message

### Interactive Mode

When run without arguments, TFIAM enters interactive mode and guides you through:

- Directory selection
- AI analysis preference
- Output directory configuration
- Quiet mode setting
- OpenAI API key management (if needed)
- Future command generation

## 📚 Scripts Directory

This directory contains various utility scripts for TFIAM:

### Scripts

- **`demo.sh`** - Basic demonstration script
- **`demo-futuristic.sh`** - Enhanced demonstration with cyberpunk theme
- **`install.sh`** - Installation script for Homebrew
- **`setup-dev.sh`** - Development environment setup
- **`test_openai.sh`** - OpenAI integration testing
- **`tfiam.rb`** - Homebrew formula for distribution

### Usage

```bash
# Development Setup
./scripts/setup-dev.sh

# Demo
./scripts/demo.sh
./scripts/demo-futuristic.sh

# OpenAI Testing
./scripts/test_openai.sh

# Installation
./scripts/install.sh
```

## 📖 Examples Directory

This directory contains example Terraform files for testing TFIAM:

### Example Files

- **`test_example.tf`** - Comprehensive example with various AWS services
- **`test_grouping.tf`** - Tests resource grouping and ARN generation
- **`test_with_variables.tf`** - Tests variable and local resolution
- **`test_dynamic.tf`** - Tests dynamic permission generation for new AWS services

### Services Covered

These examples cover:

- EC2 (VPC, Subnets, Instances, Security Groups)
- S3 (Buckets, Objects)
- RDS (Instances, Subnet Groups)
- Lambda (Functions)
- IAM (Roles, Policies, Users)
- CloudWatch (Log Groups, Alarms)
- Route53 (Zones, Records)
- WAF v2 (Web ACLs, Rule Groups)
- CloudFront (Distributions)
- EKS (Clusters, Node Groups)
- DynamoDB (Tables)
- ElastiCache (Clusters)
- API Gateway (APIs, Resources)
- Step Functions (State Machines)

## 🔄 Migration

- Original functionality preserved 100%
- All existing features work identically
- Backward compatibility maintained
- Enhanced with comprehensive AWS permissions

The CLI interface remains exactly the same:

```bash
python main.py ./terraform-dir --no-openai --quiet
python main.py ./terraform-dir --openai-key sk-xxx
python main.py --help
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make check`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS for comprehensive IAM documentation
- OpenAI for AI-powered explanations
- The Terraform community for inspiration

---

## Made with ❤️ for the DevOps community
