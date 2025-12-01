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


# ========== Pytest Configuration ==========

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """
    Skip integration tests in CI environment unless explicitly requested.
    Integration tests require Qdrant, DynamoDB, OpenAI API etc.
    """
    if os.environ.get("CI") and not os.environ.get("RUN_INTEGRATION_TESTS"):
        skip_integration = pytest.mark.skip(
            reason="Skipping integration tests in CI (set RUN_INTEGRATION_TESTS=1 to run)"
        )
        for item in items:
            # Skip tests that require external services
            test_file = str(item.fspath)

            # Skip test files that are integration tests
            integration_patterns = [
                "test_integration_e2e",
                "test_case_isolation",
                "test_storage_manager",
                "test_search_engine",
                "test_handler",  # Handler tests mock storage and require specific setup
            ]

            for pattern in integration_patterns:
                if pattern in test_file:
                    item.add_marker(skip_integration)
                    break


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
        "DYNAMODB_TABLE": os.environ.get("DYNAMODB_TABLE", "leh_evidence_test"),
    }

    for key, value in test_env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    yield

    # Cleanup not needed - environment is process-scoped
