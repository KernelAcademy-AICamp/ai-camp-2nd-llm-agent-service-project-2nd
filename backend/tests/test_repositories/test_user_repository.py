"""
Tests for UserRepository
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from app.repositories.user_repository import UserRepository
from app.db.models import User, UserRole, UserStatus


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    session = Mock()
    session.add = Mock()
    session.flush = Mock()
    session.query = Mock()
    return session


@pytest.fixture
def user_repository(mock_session):
    """Create UserRepository with mocked session"""
    return UserRepository(mock_session)


@pytest.fixture
def sample_user():
    """Sample User instance"""
    user = Mock(spec=User)
    user.id = "user_123abc"
    user.email = "test@example.com"
    user.name = "테스트 사용자"
    user.role = UserRole.LAWYER
    user.status = UserStatus.ACTIVE
    user.created_at = datetime.now(timezone.utc)
    return user


class TestUserRepositoryGetByEmail:
    """Tests for get_by_email method"""

    def test_get_by_email_found(self, user_repository, mock_session, sample_user):
        """Test getting user by email when it exists"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = sample_user
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_by_email("test@example.com")

        # Assert
        assert result == sample_user
        mock_session.query.assert_called_once_with(User)

    def test_get_by_email_not_found(self, user_repository, mock_session):
        """Test getting user by email when it doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_by_email("nonexistent@example.com")

        # Assert
        assert result is None


class TestUserRepositoryGetById:
    """Tests for get_by_id method"""

    def test_get_by_id_found(self, user_repository, mock_session, sample_user):
        """Test getting user by ID when it exists"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = sample_user
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_by_id("user_123abc")

        # Assert
        assert result == sample_user

    def test_get_by_id_not_found(self, user_repository, mock_session):
        """Test getting user by ID when it doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_by_id("nonexistent")

        # Assert
        assert result is None


class TestUserRepositoryCreate:
    """Tests for create method"""

    @patch("app.repositories.user_repository.hash_password")
    def test_create_user_success(
        self, mock_hash, user_repository, mock_session
    ):
        """Test successful user creation"""
        # Arrange
        mock_hash.return_value = "hashed_password_123"

        email = "new@example.com"
        password = "securepassword123"
        name = "새 사용자"

        # Act
        user_repository.create(email, password, name)

        # Assert
        mock_hash.assert_called_once_with(password)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Check the user was created with correct values
        added_user = mock_session.add.call_args[0][0]
        assert added_user.email == email
        assert added_user.hashed_password == "hashed_password_123"
        assert added_user.name == name
        assert added_user.role == UserRole.LAWYER

    @patch("app.repositories.user_repository.hash_password")
    def test_create_user_with_admin_role(
        self, mock_hash, user_repository, mock_session
    ):
        """Test user creation with admin role"""
        # Arrange
        mock_hash.return_value = "hashed_password_123"

        # Act
        user_repository.create(
            email="admin@example.com",
            password="adminpass",
            name="관리자",
            role=UserRole.ADMIN
        )

        # Assert
        added_user = mock_session.add.call_args[0][0]
        assert added_user.role == UserRole.ADMIN


class TestUserRepositoryExists:
    """Tests for exists method"""

    def test_exists_true(self, user_repository, mock_session):
        """Test exists returns True when user exists"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.count.return_value = 1
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.exists("test@example.com")

        # Assert
        assert result is True

    def test_exists_false(self, user_repository, mock_session):
        """Test exists returns False when user doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.count.return_value = 0
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.exists("nonexistent@example.com")

        # Assert
        assert result is False


class TestUserRepositoryGetAll:
    """Tests for get_all method"""

    def test_get_all_no_filters(self, user_repository, mock_session, sample_user):
        """Test getting all users without filters"""
        # Arrange
        mock_query = Mock()
        mock_order_by = Mock()
        mock_order_by.all.return_value = [sample_user]
        mock_query.order_by.return_value = mock_order_by
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_all()

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user

    def test_get_all_with_email_filter(self, user_repository, mock_session, sample_user):
        """Test getting users with email filter"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()

        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_order_by.all.return_value = [sample_user]
        mock_session.query.return_value = mock_query

        # Act
        user_repository.get_all(email="test")

        # Assert
        mock_query.filter.assert_called_once()

    def test_get_all_with_role_filter(self, user_repository, mock_session, sample_user):
        """Test getting users with role filter"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()

        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_order_by.all.return_value = [sample_user]
        mock_session.query.return_value = mock_query

        # Act
        user_repository.get_all(role=UserRole.LAWYER)

        # Assert
        mock_query.filter.assert_called_once()

    def test_get_all_with_status_filter(self, user_repository, mock_session, sample_user):
        """Test getting users with status filter"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()

        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_order_by.all.return_value = [sample_user]
        mock_session.query.return_value = mock_query

        # Act
        user_repository.get_all(status=UserStatus.ACTIVE)

        # Assert
        mock_query.filter.assert_called_once()

    def test_get_all_empty(self, user_repository, mock_session):
        """Test getting all users when none exist"""
        # Arrange
        mock_query = Mock()
        mock_order_by = Mock()
        mock_order_by.all.return_value = []
        mock_query.order_by.return_value = mock_order_by
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.get_all()

        # Assert
        assert len(result) == 0


class TestUserRepositorySoftDelete:
    """Tests for soft_delete method"""

    def test_soft_delete_success(self, user_repository, mock_session, sample_user):
        """Test successful soft deletion"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = sample_user
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.soft_delete("user_123abc")

        # Assert
        assert result == sample_user
        assert sample_user.status == UserStatus.INACTIVE
        mock_session.flush.assert_called_once()

    def test_soft_delete_not_found(self, user_repository, mock_session):
        """Test soft deletion when user doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = user_repository.soft_delete("nonexistent")

        # Assert
        assert result is None
        mock_session.flush.assert_not_called()
