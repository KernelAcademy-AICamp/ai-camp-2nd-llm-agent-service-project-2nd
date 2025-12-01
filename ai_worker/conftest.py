"""
Pytest configuration for LEH AI Worker
Adds project root to Python path for imports
"""

import os
import sys
from pathlib import Path

import pytest

# Add the project root directory to Python path
# This allows imports like "from src.parsers import ..."
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# ========== Test Environment Setup ==========

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up environment variables for testing.
    Uses mock/test values for external services.
    """
    # Set test environment variables if not already set
    test_env_vars = {
        "QDRANT_URL": os.environ.get("QDRANT_URL", "http://localhost:6333"),
        "QDRANT_API_KEY": os.environ.get("QDRANT_API_KEY", "test-api-key"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "test-openai-key"),
        "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "test-access-key"),
        "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "test-secret-key"),
        "AWS_REGION": os.environ.get("AWS_REGION", "us-east-1"),
        "VECTOR_SIZE": os.environ.get("VECTOR_SIZE", "1536"),
    }

    for key, value in test_env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    yield

    # Cleanup not needed - environment is process-scoped
