"""
Tests for CaseRepository
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from app.repositories.case_repository import CaseRepository
from app.db.models import Case


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    session = Mock()
    session.add = Mock()
    session.flush = Mock()
    session.query = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def case_repository(mock_session):
    """Create CaseRepository with mocked session"""
    return CaseRepository(mock_session)


@pytest.fixture
def sample_case():
    """Sample Case instance"""
    case = Mock(spec=Case)
    case.id = "case_123abc"
    case.title = "테스트 사건"
    case.description = "테스트 설명"
    case.status = "active"
    case.created_by = "user_456"
    case.created_at = datetime.now(timezone.utc)
    return case


class TestCaseRepositoryCreate:
    """Tests for create method"""

    @patch("app.repositories.case_repository.uuid")
    @patch("app.repositories.case_repository.datetime")
    def test_create_case_success(
        self, mock_datetime, mock_uuid, case_repository, mock_session
    ):
        """Test successful case creation"""
        # Arrange
        mock_uuid.uuid4.return_value.hex = "abc123def456"
        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        title = "새 사건"
        description = "새 사건 설명"
        created_by = "user_456"

        # Act
        case_repository.create(title, description, created_by)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Check the case was created with correct values
        added_case = mock_session.add.call_args[0][0]
        assert added_case.id == "case_abc123def456"
        assert added_case.title == title
        assert added_case.description == description
        assert added_case.status == "active"
        assert added_case.created_by == created_by

    @patch("app.repositories.case_repository.uuid")
    def test_create_case_without_description(
        self, mock_uuid, case_repository, mock_session
    ):
        """Test case creation without description"""
        # Arrange
        mock_uuid.uuid4.return_value.hex = "abc123def456"

        title = "새 사건"
        created_by = "user_456"

        # Act
        case_repository.create(title, None, created_by)

        # Assert
        added_case = mock_session.add.call_args[0][0]
        assert added_case.description is None


class TestCaseRepositoryGetById:
    """Tests for get_by_id method"""

    def test_get_by_id_found(self, case_repository, mock_session, sample_case):
        """Test getting case by ID when it exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_case
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.get_by_id("case_123abc")

        # Assert
        assert result == sample_case
        mock_session.query.assert_called_once_with(Case)

    def test_get_by_id_not_found(self, case_repository, mock_session):
        """Test getting case by ID when it doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.get_by_id("nonexistent")

        # Assert
        assert result is None

    def test_get_by_id_include_deleted(self, case_repository, mock_session, sample_case):
        """Test getting deleted case with include_deleted=True"""
        # Arrange
        sample_case.deleted_at = datetime.now(timezone.utc)
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = sample_case
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.get_by_id("case_123abc", include_deleted=True)

        # Assert
        assert result == sample_case


class TestCaseRepositoryGetAllForUser:
    """Tests for get_all_for_user method"""

    def test_get_all_for_user_success(self, case_repository, mock_session, sample_case):
        """Test getting all cases for a user"""
        # Arrange
        mock_query = Mock()
        mock_join = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()

        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = [sample_case]

        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.get_all_for_user("user_456")

        # Assert
        assert len(result) == 1
        assert result[0] == sample_case
        mock_session.query.assert_called_once_with(Case)

    def test_get_all_for_user_empty(self, case_repository, mock_session):
        """Test getting cases when user has none"""
        # Arrange
        mock_query = Mock()
        mock_join = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()

        mock_query.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter1
        mock_filter1.filter.return_value = mock_filter2
        mock_filter2.all.return_value = []

        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.get_all_for_user("user_456")

        # Assert
        assert len(result) == 0


class TestCaseRepositoryUpdate:
    """Tests for update method"""

    def test_update_case_success(self, case_repository, mock_session, sample_case):
        """Test successful case update"""
        # Arrange
        sample_case.title = "수정된 제목"

        # Act
        result = case_repository.update(sample_case)

        # Assert
        mock_session.add.assert_called_once_with(sample_case)
        mock_session.flush.assert_called_once()
        assert result == sample_case


class TestCaseRepositorySoftDelete:
    """Tests for soft_delete method"""

    def test_soft_delete_success(self, case_repository, mock_session, sample_case):
        """Test successful soft deletion"""
        # Arrange - get_by_id now uses two filter() calls
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_case
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.soft_delete("case_123abc")

        # Assert
        assert result is True
        assert sample_case.status == "closed"
        assert sample_case.deleted_at is not None
        mock_session.flush.assert_called_once()

    def test_soft_delete_not_found(self, case_repository, mock_session):
        """Test soft deletion when case doesn't exist"""
        # Arrange - get_by_id now uses two filter() calls
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.soft_delete("nonexistent")

        # Assert
        assert result is False
        mock_session.flush.assert_not_called()


class TestCaseRepositoryHardDelete:
    """Tests for hard_delete method"""

    def test_hard_delete_success(self, case_repository, mock_session, sample_case):
        """Test successful hard deletion"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_case
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.hard_delete("case_123abc")

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_case)
        mock_session.flush.assert_called_once()

    def test_hard_delete_not_found(self, case_repository, mock_session):
        """Test hard deletion when case doesn't exist"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_repository.hard_delete("nonexistent")

        # Assert
        assert result is False
        mock_session.delete.assert_not_called()
