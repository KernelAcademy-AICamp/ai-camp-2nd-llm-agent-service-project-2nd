"""
Pytest configuration and shared fixtures for LEH Backend tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import os
import uuid


def pytest_collection_modifyitems(config, items):
    """
    Skip tests marked with @pytest.mark.requires_aws when AWS credentials are not available
    """
    skip_aws = pytest.mark.skip(
        reason="AWS credentials not configured (requires_aws marker)"
    )
    for item in items:
        if "requires_aws" in item.keywords:
            # Check if real AWS credentials are available
            if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
                item.add_marker(skip_aws)


def pytest_configure(config):
    """
    Configure environment for pytest.

    IMPORTANT (Issue #39 fix): Always use SQLite for tests to ensure:
    - No accidental modification of production/development database
    - Fast test execution
    - Complete test isolation
    """
    # ALWAYS force SQLite for tests - prevents connecting to production PostgreSQL
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    os.environ["TESTING"] = "true"

    # Set other test defaults (always set these to override any .env values)
    defaults = {
        "APP_ENV": "local",
        "APP_DEBUG": "true",
        "JWT_SECRET": "test-secret-key-for-ci-pipeline-32chars",
        "S3_EVIDENCE_BUCKET": "test-bucket",
        "S3_PRESIGNED_URL_EXPIRE_SECONDS": "300",  # Force default per SECURITY_COMPLIANCE.md
        "DDB_EVIDENCE_TABLE": "test-evidence-table",
        "QDRANT_HOST": "",  # Empty = in-memory mode for tests
        "OPENAI_API_KEY": "test-openai-key",
    }
    # Force test defaults (critical values that must be isolated from .env)
    force_defaults = ["S3_PRESIGNED_URL_EXPIRE_SECONDS", "DATABASE_URL", "JWT_SECRET"]
    for key, value in defaults.items():
        if key in force_defaults or not os.environ.get(key):
            os.environ[key] = value

    # DO NOT load .env file - we want complete isolation from production config


# ============================================
# Auto-use AWS Mocking Fixtures
# ============================================

@pytest.fixture(scope="session", autouse=True)
def mock_aws_services():
    """
    Mock all AWS services (S3, DynamoDB) at session level
    to prevent tests from requiring real AWS credentials

    Note: dynamo.py uses boto3.client (not boto3.resource)
    """
    # Mock DynamoDB client (low-level API)
    mock_dynamodb_client = MagicMock()
    mock_dynamodb_client.query.return_value = {"Items": []}
    mock_dynamodb_client.scan.return_value = {"Items": []}
    mock_dynamodb_client.get_item.return_value = {}  # No Item = not found
    mock_dynamodb_client.put_item.return_value = {}
    mock_dynamodb_client.delete_item.return_value = {}

    # Mock S3 client
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/presigned-url"
    mock_s3_client.generate_presigned_post.return_value = {
        "url": "https://test-bucket.s3.amazonaws.com",
        "fields": {"key": "test-key"}
    }

    def mock_boto3_client(service_name, **kwargs):
        """Return appropriate mock based on service"""
        if service_name == 's3':
            return mock_s3_client
        elif service_name == 'dynamodb':
            return mock_dynamodb_client
        else:
            return MagicMock()

    # Also support resource API for any code that might use it
    mock_boto3_resource = MagicMock()
    mock_table = MagicMock()
    mock_table.query.return_value = {"Items": []}
    mock_table.scan.return_value = {"Items": []}
    mock_table.get_item.return_value = {"Item": None}
    mock_table.put_item.return_value = {}
    mock_boto3_resource.return_value.Table.return_value = mock_table

    # Patch boto3 at both global and module level to ensure mocks work everywhere
    with patch('boto3.client', mock_boto3_client), \
         patch('boto3.resource', mock_boto3_resource), \
         patch('app.utils.s3.boto3.client', mock_boto3_client), \
         patch('app.utils.dynamo.boto3.client', mock_boto3_client):
        yield {
            "s3": mock_s3_client,
            "dynamodb": mock_dynamodb_client,
            "dynamodb_table": mock_table,
        }


@pytest.fixture(scope="session")
def test_env():
    """
    Set up test environment variables and initialize database

    Respects CI environment variables if already set (e.g., DATABASE_URL from GitHub Actions)
    For local development, uses SQLite database
    """
    import os as os_module

    # Clean up any existing test database (for local SQLite)
    if os_module.path.exists("./test.db"):
        os_module.remove("./test.db")

    # Default test values - only used if not already set in environment
    # Use SQLite for local testing, PostgreSQL for CI
    defaults = {
        "APP_ENV": "local",
        "APP_DEBUG": "true",
        "JWT_SECRET": "test-secret-key-do-not-use-in-production",
        "DATABASE_URL": "sqlite:///./test.db",  # Local default, CI overrides this
        "S3_EVIDENCE_BUCKET": "test-bucket",
        "DDB_EVIDENCE_TABLE": "test-evidence-table",
        "QDRANT_HOST": "",  # Empty = in-memory mode for tests
        "OPENAI_API_KEY": "test-openai-key",
    }

    # Store original env vars and set defaults only if not already set
    original_env = {}
    test_env_vars = {}
    for key, default_value in defaults.items():
        original_env[key] = os.environ.get(key)
        # Use existing env var if set, otherwise use default
        if os.environ.get(key):
            test_env_vars[key] = os.environ[key]
        else:
            os.environ[key] = default_value
            test_env_vars[key] = default_value

    # Patch global settings
    from app.core.config import settings
    original_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = test_env_vars["DATABASE_URL"]

    # Initialize database and create tables for all tests
    from app.db.session import init_db, engine
    from app.db.models import Base
    init_db()

    yield test_env_vars

    # Drop tables and cleanup
    if engine is not None:
        Base.metadata.drop_all(bind=engine)

    # Restore global settings
    settings.DATABASE_URL = original_db_url

    # Restore original env vars
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value

    # Clean up test database file (for local SQLite)
    if os_module.path.exists("./test.db"):
        os_module.remove("./test.db")


@pytest.fixture(scope="function")
def client(test_env):
    """
    FastAPI TestClient fixture

    Creates a fresh TestClient for each test function.
    Automatically uses test environment variables.
    """
    # Import here to ensure test_env is loaded first
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_settings(test_env):
    """
    Mock settings object for unit tests

    Returns a settings object with test values.
    """
    from app.core.config import Settings

    settings = Settings(**test_env)
    return settings


@pytest.fixture(scope="function")
def mock_db_session():
    """
    Mock database session

    Use this for testing database operations without real DB.
    """
    session = Mock()
    yield session
    session.close()


@pytest.fixture(scope="function")
def mock_s3_client():
    """
    Mock boto3 S3 client
    """
    with patch('boto3.client') as mock_boto3:
        mock_client = Mock()
        mock_boto3.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_dynamodb_client():
    """
    Mock boto3 DynamoDB client
    """
    with patch('boto3.resource') as mock_boto3:
        mock_resource = Mock()
        mock_boto3.return_value = mock_resource
        yield mock_resource


@pytest.fixture(scope="function")
def mock_qdrant_client():
    """
    Mock Qdrant client
    """
    with patch('qdrant_client.QdrantClient') as mock_qdrant:
        mock_client = Mock()
        mock_qdrant.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_openai_client():
    """
    Mock OpenAI client
    """
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_case_data():
    """
    Sample case data for testing
    """
    return {
        "id": "case_123",
        "title": "김○○ 이혼 사건",
        "description": "테스트 사건",
        "status": "active",
        "created_by": "user_456"
    }


@pytest.fixture
def sample_evidence_data():
    """
    Sample evidence metadata for testing
    """
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
    """
    Sample user data for testing
    """
    return {
        "id": "user_456",
        "email": "test@example.com",
        "name": "테스트 사용자",
        "role": "lawyer"
    }


@pytest.fixture
def test_user(test_env):
    """
    Create a real user in the database for authentication tests

    Password: correct_password123

    Issue #39 fix: Uses unique email per test to prevent duplicate key errors
    """
    from app.db.session import get_db
    from app.db.models import User, Case, CaseMember, InviteToken
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Generate unique email for each test run to prevent conflicts
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"test_{unique_id}@example.com"

    # Database is already initialized by test_env fixture
    # Create user
    db: Session = next(get_db())
    try:
        user = User(
            email=unique_email,
            hashed_password=hash_password("correct_password123"),
            name="테스트 사용자",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        yield user

        # Cleanup - delete in correct order to respect foreign keys
        # Delete invite tokens first
        db.query(InviteToken).filter(InviteToken.created_by == user.id).delete()
        # Delete case_members
        db.query(CaseMember).filter(CaseMember.user_id == user.id).delete()
        # Delete cases created by user
        db.query(Case).filter(Case.created_by == user.id).delete()
        # Delete user
        db.delete(user)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_headers(test_user):
    """
    Generate authentication headers with JWT token for test_user

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.core.security import create_access_token

    # Create JWT token for test user
    token = create_access_token(data={"sub": test_user.id, "role": test_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def admin_user(test_env):
    """
    Create admin user in the database for admin tests

    Password: admin_password123

    Issue #39 fix: Uses unique email per test to prevent duplicate key errors
    """
    from app.db.session import get_db, init_db
    from app.db.models import User
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Generate unique email for each test run to prevent conflicts
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"admin_{unique_id}@example.com"

    # Initialize database
    init_db()

    # Create admin user
    db: Session = next(get_db())
    try:
        admin = User(
            email=unique_email,
            hashed_password=hash_password("admin_password123"),
            name="Admin User",
            role="admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        yield admin

        # Cleanup
        from app.db.models import Case, CaseMember, InviteToken
        # Delete invite tokens created by admin
        db.query(InviteToken).filter(InviteToken.created_by == admin.id).delete()
        # Delete case_members
        db.query(CaseMember).filter(CaseMember.user_id == admin.id).delete()
        # Delete cases
        db.query(Case).filter(Case.created_by == admin.id).delete()
        # Delete admin user
        db.delete(admin)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def admin_auth_headers(admin_user):
    """
    Generate authentication headers with JWT token for admin_user

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.core.security import create_access_token

    # Create JWT token for admin user
    token = create_access_token(data={"sub": admin_user.id, "role": admin_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def client_user(test_env):
    """
    Create a client user in the database for client portal tests

    Password: client_password123

    US4 Tests (T055-T060)
    """
    from app.db.session import get_db
    from app.db.models import User, Case, CaseMember, InviteToken
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Generate unique email for each test run to prevent conflicts
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"client_{unique_id}@test.com"

    # Create client user
    db: Session = next(get_db())
    try:
        user = User(
            email=unique_email,
            hashed_password=hash_password("client_password123"),
            name="테스트 의뢰인",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        yield user

        # Cleanup - delete in correct order to respect foreign keys
        db.query(InviteToken).filter(InviteToken.created_by == user.id).delete()
        db.query(CaseMember).filter(CaseMember.user_id == user.id).delete()
        db.query(Case).filter(Case.created_by == user.id).delete()
        db.delete(user)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client_auth_headers(client_user):
    """
    Generate authentication headers with JWT token for client_user

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.core.security import create_access_token

    # Create JWT token for client user
    token = create_access_token(data={"sub": client_user.id, "role": client_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture
def test_case_with_client(test_env, client_user, test_user):
    """
    Create a case with client as a member for client portal tests

    Creates:
    - A case owned by test_user (lawyer)
    - client_user added as MEMBER

    US4 Tests (T055-T060)
    """
    from app.db.session import get_db
    from app.db.models import Case, CaseMember, Evidence
    from sqlalchemy.orm import Session

    db: Session = next(get_db())
    try:
        # Create case
        case = Case(
            title="테스트 이혼 소송",
            description="의뢰인 테스트용 케이스",
            status="active",
            created_by=test_user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Add lawyer as OWNER
        owner_member = CaseMember(
            case_id=case.id,
            user_id=test_user.id,
            role="owner"
        )
        db.add(owner_member)

        # Add client as MEMBER
        client_member = CaseMember(
            case_id=case.id,
            user_id=client_user.id,
            role="member"
        )
        db.add(client_member)
        db.commit()

        yield case

        # Cleanup - delete evidence first (foreign key constraint)
        db.query(Evidence).filter(Evidence.case_id == case.id).delete()
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def detective_user(test_env):
    """
    Create a detective user in the database for detective portal tests

    Password: detective_password123

    US5 Tests (T077-T084)
    """
    from app.db.session import get_db
    from app.db.models import User, Case, CaseMember, InviteToken, InvestigationRecord
    from app.core.security import hash_password
    from sqlalchemy.orm import Session

    # Generate unique email for each test run to prevent conflicts
    unique_id = uuid.uuid4().hex[:8]
    unique_email = f"detective_{unique_id}@test.com"

    # Create detective user
    db: Session = next(get_db())
    try:
        user = User(
            email=unique_email,
            hashed_password=hash_password("detective_password123"),
            name="테스트 탐정",
            role="detective"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        yield user

        # Cleanup - delete in correct order to respect foreign keys
        db.query(InviteToken).filter(InviteToken.created_by == user.id).delete()
        db.query(CaseMember).filter(CaseMember.user_id == user.id).delete()
        db.query(Case).filter(Case.created_by == user.id).delete()
        # Clean up investigation records if the model exists
        try:
            db.query(InvestigationRecord).filter(InvestigationRecord.detective_id == user.id).delete()
        except Exception:
            pass  # Model may not have detective_id field
        db.delete(user)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def detective_auth_headers(detective_user):
    """
    Generate authentication headers with JWT token for detective_user

    Returns:
        dict: Headers with Authorization Bearer token
    """
    from app.core.security import create_access_token

    # Create JWT token for detective user
    token = create_access_token(data={"sub": detective_user.id, "role": detective_user.role})

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================
# Calendar Test Fixtures (US7 - T125-T140)
# ============================================

@pytest.fixture
def lawyer_user(test_user):
    """
    Alias for test_user as lawyer - used in calendar tests

    Returns:
        User: Lawyer user object
    """
    return test_user


@pytest.fixture
def lawyer_token(auth_headers):
    """
    Get JWT token string for lawyer user

    Returns:
        str: JWT token string (without 'Bearer ' prefix)
    """
    # Extract token from auth_headers
    bearer_header = auth_headers.get("Authorization", "")
    if bearer_header.startswith("Bearer "):
        return bearer_header[7:]
    return bearer_header


@pytest.fixture
def client_token(client_auth_headers):
    """
    Get JWT token string for client user

    Returns:
        str: JWT token string (without 'Bearer ' prefix)
    """
    # Extract token from auth_headers
    bearer_header = client_auth_headers.get("Authorization", "")
    if bearer_header.startswith("Bearer "):
        return bearer_header[7:]
    return bearer_header


@pytest.fixture
def db_session(test_env):
    """
    Database session for direct DB operations in tests

    Returns:
        Session: SQLAlchemy session
    """
    from app.db.session import get_db
    from sqlalchemy.orm import Session

    db: Session = next(get_db())
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_case(test_env, test_user):
    """
    Create a test case for calendar tests

    Returns:
        Case: Test case object
    """
    from app.db.session import get_db
    from app.db.models import Case, CaseMember
    from sqlalchemy.orm import Session

    db: Session = next(get_db())
    try:
        # Create case
        case = Case(
            title="캘린더 테스트 케이스",
            description="캘린더 일정 테스트용",
            status="active",
            created_by=test_user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Add owner as case member
        member = CaseMember(
            case_id=case.id,
            user_id=test_user.id,
            role="owner"
        )
        db.add(member)
        db.commit()

        yield case

        # Cleanup
        from app.db.models import CalendarEvent
        db.query(CalendarEvent).filter(CalendarEvent.case_id == case.id).delete()
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.commit()
    finally:
        db.close()
