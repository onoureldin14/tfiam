#!/usr/bin/env python3
"""
TFIAM - Terraform IAM Permission Analyzer (Standalone)
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "src"))

# Import and run main
if __name__ == "__main__":
    from main import main

    main()
