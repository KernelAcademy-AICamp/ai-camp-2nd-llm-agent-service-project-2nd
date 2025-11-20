"""
Pytest configuration for LEH AI Worker
Adds project root to Python path for imports
"""

import sys
from pathlib import Path

# Add the project root directory to Python path
# This allows imports like "from src.parsers import ..."
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
