"""
TFIAM - Terraform IAM Permission Analyzer

A tool that scans Terraform repositories and recommends IAM permissions
with OpenAI-powered explanations for complete resource management.
"""

__version__ = "1.0.0"
__author__ = "TFIAM Team"
__description__ = "Terraform IAM Permission Analyzer"

from .cli.cyber_cli import CyberCLI, print_cyberpunk_help
from .core.analyzer import TerraformAnalyzer
from .core.openai_analyzer import OpenAIAnalyzer
from .core.policy_generator import PolicyGenerator

__all__ = [
    "TerraformAnalyzer",
    "PolicyGenerator",
    "OpenAIAnalyzer",
    "CyberCLI",
    "print_cyberpunk_help",
]
