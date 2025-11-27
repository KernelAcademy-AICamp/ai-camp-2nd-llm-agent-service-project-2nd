"""
Pytest configuration and shared fixtures for LEH Backend tests
Uses real PostgreSQL database from .env configuration
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from pathlib import Path

# Load .env file from project root
from dotenv import load_dotenv

# Find .env file (2 levels up from tests folder)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def test_env():
    """
    Set up test environment variables from .env file
    Uses real PostgreSQL database configuration
    """
    # Use real database configuration from .env
    test_env_vars = {
        "APP_ENV": os.getenv("APP_ENV", "local"),
        "APP_DEBUG": os.getenv("APP_DEBUG", "true"),
        "JWT_SECRET": os.getenv("JWT_SECRET", "test-secret-key-do-not-use-in-production"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql+psycopg2://leh_user:leh_password@localhost:5434/leh_db"),
        "S3_EVIDENCE_BUCKET": os.getenv("S3_EVIDENCE_BUCKET", "test-bucket"),
        "DDB_EVIDENCE_TABLE": os.getenv("DDB_EVIDENCE_TABLE", "test-evidence-table"),
        "OPENSEARCH_HOST": os.getenv("OPENSEARCH_HOST", "https://test-opensearch.local"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-openai-key"),
    }

    # Store original env vars
    original_env = {}
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_env_vars

    # Restore original env vars
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture(scope="function")
def client(test_env):
    """
    FastAPI TestClient fixture
    """
    from app.main import app
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_settings(test_env):
    """
    Mock settings object for unit tests
    """
    from app.core.config import Settings
    settings = Settings(**test_env)
    return settings


@pytest.fixture(scope="function")
def db_session(test_env):
    """
    Real database session fixture
    """
    from app.db.session import init_db, get_db
    init_db()
    session = next(get_db())
    yield session
    session.close()


@pytest.fixture(scope="function")
def mock_s3_client():
    """Mock boto3 S3 client"""
    with patch('boto3.client') as mock_boto3:
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_dynamodb_client():
    """Mock boto3 DynamoDB client"""
    with patch('boto3.resource') as mock_boto3:
        mock_resource = Mock()
        mock_boto3.return_value = mock_resource
        yield mock_resource


@pytest.fixture(scope="function")
def mock_opensearch_client():
    """Mock OpenSearch client"""
    with patch('opensearchpy.OpenSearch') as mock_os:
        mock_client = Mock()
        mock_os.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_case_data():
    """Sample case data for testing"""
    return {
        "id": "case_123",
        "title": "김○○ 이혼 사건",
        "description": "테스트 사건",
        "status": "active",
        "created_by": "user_456"
    }


@pytest.fixture
def sample_evidence_data():
    """Sample evidence metadata for testing"""
    return {
        "case_id": "case_123",
        "evidence_id": "ev_001",
        "type": "text",
        "timestamp": "2024-12-25T10:20:00Z",
        "speaker": "원고",
        "labels": ["폭언", "계속적 불화"],
        "ai_summary": "피고가 고성을 지르며 폭언함",
        "content": "테스트 증거 내용",
        "s3_key": "cases/case_123/raw/test.txt",
        "status": "done"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "id": "user_456",
        "email": "test@example.com",
        "name": "테스트 사용자",
        "role": "lawyer"
    }


@pytest.fixture
def test_user(test_env):
    """
    Create a real user in PostgreSQL database for authentication tests
    Password: correct_password123
    """
    from app.db import session as db_session_module
    from app.db.models import Base, User, Case, CaseMember
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Initialize database
    db_session_module.init_db()

    # Get a session
    db: Session = next(db_session_module.get_db())
    
    try:
        user = User(
            email="test@example.com",
            hashed_password=hash_password("correct_password123"),
            name="테스트 사용자",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        yield user

        # Cleanup - delete in correct order to respect foreign keys
        db.query(CaseMember).filter(CaseMember.user_id == user.id).delete()
        db.query(Case).filter(Case.created_by == user.id).delete()
        db.delete(user)
        db.commit()
    finally:
        db.close()

        # Drop tables after test using module-level engine
        if db_session_module.engine is not None:
            Base.metadata.drop_all(bind=db_session_module.engine)


@pytest.fixture
def auth_headers(test_user):
    """
    Generate authentication headers with JWT token for test_user
    """
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.id, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}
