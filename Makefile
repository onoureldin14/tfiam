# TFIAM Makefile

.PHONY: help install test clean lint format demo dev-setup

help: ## Show this help message
	@echo "TFIAM - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv: ## Create virtual environment
	@if [ ! -d "venv" ]; then \
		echo "📦 Creating virtual environment..."; \
		python3 -m venv venv; \
		echo "✅ Virtual environment created"; \
		echo "💡 Activate it with: source venv/bin/activate"; \
	else \
		echo "📦 Virtual environment already exists"; \
	fi

install: ## Install dependencies
	@if [ -d "venv" ]; then \
		echo "📦 Installing to virtual environment..."; \
		./venv/bin/pip install -r requirements.txt; \
	else \
		echo "📦 Installing to system Python..."; \
		pip install -r requirements.txt; \
	fi

dev-setup: ## Set up development environment
	@echo "🚀 Setting up TFIAM Development Environment"
	@if [ ! -d "venv" ]; then \
		echo "📦 Creating virtual environment..."; \
		python3 -m venv venv; \
		echo "✅ Virtual environment created"; \
	else \
		echo "📦 Virtual environment already exists"; \
	fi
	@echo "📥 Installing dependencies..."
	./venv/bin/pip install -r requirements.txt
	@echo "📥 Installing additional development tools..."
	./venv/bin/pip install pytest pytest-cov
	@echo "🔧 Setting up pre-commit hooks..."
	@if [ -f ".pre-commit-config.yaml" ]; then \
		./venv/bin/pre-commit install; \
		echo "✅ Pre-commit hooks installed"; \
	else \
		echo "⚠️  No .pre-commit-config.yaml found, skipping pre-commit setup"; \
	fi
	@echo "🧪 Testing the installation..."
	@./venv/bin/python -c "import sys; sys.path.insert(0, 'src'); from tfiam import TerraformAnalyzer, PolicyGenerator, OpenAIAnalyzer; print('✅ All modules imported successfully')"
	@echo ""
	@echo "✅ Development environment setup complete!"
	@echo ""
	@echo "📋 Available commands:"
	@echo "  source venv/bin/activate    # Activate virtual environment"
	@echo "  python3 main.py --help     # Show tfiam help"
	@echo "  python3 main.py . --ai     # Run with AI analysis"
	@echo "  pytest                     # Run tests"
	@echo "  black .                    # Format Python code"
	@echo "  isort .                    # Sort imports"
	@echo "  flake8 .                   # Lint Python code"
	@echo "  mypy .                     # Type check"
	@echo "  bandit .                   # Security scan"
	@echo ""
	@echo "🎉 Happy coding!"

test: ## Run tests
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest tests/ -v; \
	else \
		python -m pytest tests/ -v; \
	fi

test-coverage: ## Run tests with coverage
	@if [ -d "venv" ]; then \
		./venv/bin/python -m pytest tests/ --cov=src --cov-report=html --cov-report=term; \
	else \
		python -m pytest tests/app --cov=src --cov-report=html --cov-report=term; \
	fi

lint: ## Run linting
	@if [ -d "venv" ]; then \
		./venv/bin/flake8 src/ tests/; \
		./venv/bin/mypy src/; \
		./venv/bin/bandit -r src/; \
	else \
		flake8 src/ tests/; \
		mypy src/; \
		bandit -r src/; \
	fi

format: ## Format code
	@if [ -d "venv" ]; then \
		./venv/bin/black src/ tests/; \
		./venv/bin/isort src/ tests/; \
	else \
		black src/ tests/; \
		isort src/ tests/; \
	fi

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/

demo: ## Run demo
	./scripts/demo.sh

demo-futuristic: ## Run futuristic demo
	./scripts/demo-futuristic.sh

interactive: ## Run in interactive mode
	@if [ -d "venv" ]; then \
		./venv/bin/python main.py; \
	else \
		python main.py; \
	fi

test-examples: ## Test with example files
	python main.py examples/ -no-ai --quiet
	python main.py examples/ -no-ai --quiet

install-homebrew: ## Install via Homebrew
	./scripts/install.sh

check: lint test ## Run linting and tests

all: clean install dev-setup test ## Clean, install, setup dev environment, and test
