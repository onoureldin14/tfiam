"""Data models for TFIAM."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class IAMStatement:
    """Represents an IAM policy statement."""

    sid: str
    effect: str
    action: List[str]
    resource: List[str]
    explanation: str = ""


@dataclass
class TerraformResource:
    """Represents a Terraform resource."""

    type: str
    name: str
    resource_name: Optional[str] = None
    file_path: str = ""
    properties: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
