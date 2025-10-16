# TFIAM Makefile

.PHONY: help install test clean lint format demo dev-setup

help: ## Show this help message
	@echo "TFIAM - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev-setup: ## Set up development environment
	./scripts/setup-dev.sh

test: ## Run tests
	python -m pytest tests/ -v

test-coverage: ## Run tests with coverage
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: ## Run linting
	flake8 src/ tests/
	mypy src/
	bandit -r src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

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
	python main.py

test-examples: ## Test with example files
	python main.py examples/ -no-ai --quiet
	python main.py examples/ -no-ai --quiet

install-homebrew: ## Install via Homebrew
	./scripts/install.sh

check: lint test ## Run linting and tests

all: clean install dev-setup test ## Clean, install, setup dev environment, and test
