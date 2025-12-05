"""
Tests for CaseMemberRepository
"""

import pytest
from unittest.mock import Mock
from app.repositories.case_member_repository import CaseMemberRepository
from app.db.models import CaseMember, CaseMemberRole


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
def case_member_repository(mock_session):
    """Create CaseMemberRepository with mocked session"""
    return CaseMemberRepository(mock_session)


@pytest.fixture
def sample_member():
    """Sample CaseMember instance"""
    member = Mock(spec=CaseMember)
    member.case_id = "case_123abc"
    member.user_id = "user_456"
    member.role = CaseMemberRole.OWNER
    return member


class TestCaseMemberRepositoryAddMember:
    """Tests for add_member method"""

    def test_add_member_success(self, case_member_repository, mock_session):
        """Test successful member addition"""
        # Act
        result = case_member_repository.add_member(
            case_id="case_123",
            user_id="user_456",
            role="owner"
        )

        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        added_member = mock_session.add.call_args[0][0]
        assert added_member.case_id == "case_123"
        assert added_member.user_id == "user_456"
        assert added_member.role == "owner"

    def test_add_member_default_role(self, case_member_repository, mock_session):
        """Test member addition with default role"""
        # Act
        case_member_repository.add_member(
            case_id="case_123",
            user_id="user_456"
        )

        # Assert
        added_member = mock_session.add.call_args[0][0]
        assert added_member.role == "owner"


class TestCaseMemberRepositoryGetMember:
    """Tests for get_member method"""

    def test_get_member_found(self, case_member_repository, mock_session, sample_member):
        """Test getting member when exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.get_member("case_123abc", "user_456")

        # Assert
        assert result == sample_member
        mock_session.query.assert_called_once_with(CaseMember)

    def test_get_member_not_found(self, case_member_repository, mock_session):
        """Test getting member when not exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.get_member("case_123", "user_unknown")

        # Assert
        assert result is None


class TestCaseMemberRepositoryHasAccess:
    """Tests for has_access method"""

    def test_has_access_true(self, case_member_repository, mock_session, sample_member):
        """Test has_access returns True when member exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_access("case_123abc", "user_456")

        # Assert
        assert result is True

    def test_has_access_false(self, case_member_repository, mock_session):
        """Test has_access returns False when member not exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_access("case_123", "user_unknown")

        # Assert
        assert result is False


class TestCaseMemberRepositoryRemoveMember:
    """Tests for remove_member method"""

    def test_remove_member_success(self, case_member_repository, mock_session, sample_member):
        """Test successful member removal"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.remove_member("case_123abc", "user_456")

        # Assert
        assert result is True
        mock_session.delete.assert_called_once_with(sample_member)
        mock_session.flush.assert_called_once()

    def test_remove_member_not_found(self, case_member_repository, mock_session):
        """Test removal when member not exists"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.remove_member("case_123", "user_unknown")

        # Assert
        assert result is False
        mock_session.delete.assert_not_called()


class TestCaseMemberRepositoryIsOwner:
    """Tests for is_owner method"""

    def test_is_owner_true(self, case_member_repository, mock_session, sample_member):
        """Test is_owner returns True for owner"""
        # Arrange
        sample_member.role = CaseMemberRole.OWNER
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.is_owner("case_123abc", "user_456")

        # Assert
        assert result is True

    def test_is_owner_false_for_member(self, case_member_repository, mock_session, sample_member):
        """Test is_owner returns False for non-owner member"""
        # Arrange
        sample_member.role = CaseMemberRole.MEMBER
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.is_owner("case_123abc", "user_456")

        # Assert
        assert result is False

    def test_is_owner_false_when_not_member(self, case_member_repository, mock_session):
        """Test is_owner returns False when not a member"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.is_owner("case_123", "user_unknown")

        # Assert
        assert result is False


class TestCaseMemberRepositoryHasWriteAccess:
    """Tests for has_write_access method"""

    def test_has_write_access_owner(self, case_member_repository, mock_session, sample_member):
        """Test owner has write access"""
        # Arrange
        sample_member.role = CaseMemberRole.OWNER
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_write_access("case_123abc", "user_456")

        # Assert
        assert result is True

    def test_has_write_access_member(self, case_member_repository, mock_session, sample_member):
        """Test member has write access"""
        # Arrange
        sample_member.role = CaseMemberRole.MEMBER
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_write_access("case_123abc", "user_456")

        # Assert
        assert result is True

    def test_has_write_access_viewer_denied(self, case_member_repository, mock_session, sample_member):
        """Test viewer does not have write access"""
        # Arrange
        sample_member.role = CaseMemberRole.VIEWER
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = sample_member
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_write_access("case_123abc", "user_456")

        # Assert
        assert result is False

    def test_has_write_access_not_member(self, case_member_repository, mock_session):
        """Test non-member does not have write access"""
        # Arrange
        mock_query = Mock()
        mock_filter1 = Mock()
        mock_filter2 = Mock()
        mock_filter2.first.return_value = None
        mock_filter1.filter.return_value = mock_filter2
        mock_query.filter.return_value = mock_filter1
        mock_session.query.return_value = mock_query

        # Act
        result = case_member_repository.has_write_access("case_123", "user_unknown")

        # Assert
        assert result is False
