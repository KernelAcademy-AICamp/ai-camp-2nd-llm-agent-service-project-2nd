"""
Pytest configuration for AI Worker tests.
Loads environment variables from .env file before tests run.
"""

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"\n[conftest] Loaded environment from {env_file}")
else:
    print(f"\n[conftest] Warning: {env_file} not found")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure environment variables are loaded for all tests"""
    # Verify critical environment variables
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'OPENAI_API_KEY',
    ]
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        pytest.skip(f"Missing required environment variables: {missing}")
    
    yield
