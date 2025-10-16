"""Core functionality for TFIAM."""

from .analyzer import TerraformAnalyzer
from .models import IAMStatement, TerraformResource
from .openai_analyzer import OpenAIAnalyzer
from .policy_generator import PolicyGenerator

__all__ = [
    "TerraformAnalyzer",
    "PolicyGenerator",
    "OpenAIAnalyzer",
    "IAMStatement",
    "TerraformResource",
]
