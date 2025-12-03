"""
Tests for CaseService
"""

import pytest
from unittest.mock import Mock
from app.services.case_service import CaseService
from app.db.schemas import CaseCreate, CaseUpdate, CaseMemberAdd, CaseMemberPermission
from app.db.models import Case, CaseMember, CaseMemberRole, User, UserRole
from app.middleware import NotFoundError, PermissionError
from datetime import datetime, timezone


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def case_service(mock_db):
    """Create CaseService with mocked dependencies"""
    service = CaseService(mock_db)
    service.case_repo = Mock()
    service.member_repo = Mock()
    service.user_repo = Mock()
    return service


@pytest.fixture
def sample_case():
    """Sample Case model instance"""
    case = Mock(spec=Case)
    case.id = "case_123abc"
    case.title = "테스트 사건"
    case.client_name = "홍길동"
    case.description = "테스트 설명"
    case.status = "active"
    case.created_by = "user_456"
    case.created_at = datetime.now(timezone.utc)
    case.updated_at = datetime.now(timezone.utc)
    return case


@pytest.fixture
def sample_member():
    """Sample CaseMember model instance"""
    member = Mock(spec=CaseMember)
    member.case_id = "case_123abc"
    member.user_id = "user_456"
    member.role = CaseMemberRole.OWNER
    return member


@pytest.fixture
def sample_user():
    """Sample User model instance"""
    user = Mock(spec=User)
    user.id = "user_456"
    user.email = "test@example.com"
    user.name = "테스트 사용자"
    user.role = UserRole.LAWYER
    return user


class TestCaseServiceCreate:
    """Tests for create_case method"""

    def test_create_case_success(self, case_service, mock_db, sample_case):
        """Test successful case creation"""
        # Arrange
        case_data = CaseCreate(title="새 사건", description="새 사건 설명")
        user_id = "user_456"

        case_service.case_repo.create.return_value = sample_case

        # Act
        result = case_service.create_case(case_data, user_id)

        # Assert
        case_service.case_repo.create.assert_called_once_with(
            title="새 사건",
            client_name=None,
            description="새 사건 설명",
            created_by=user_id
        )
        case_service.member_repo.add_member.assert_called_once_with(
            case_id=sample_case.id,
            user_id=user_id,
            role="owner"
        )
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_case)
        assert result.id == sample_case.id

    def test_create_case_without_description(self, case_service, mock_db, sample_case):
        """Test case creation without description"""
        # Arrange
        case_data = CaseCreate(title="새 사건")
        user_id = "user_456"
        sample_case.description = None

        case_service.case_repo.create.return_value = sample_case

        # Act
        case_service.create_case(case_data, user_id)

        # Assert
        case_service.case_repo.create.assert_called_once_with(
            title="새 사건",
            client_name=None,
            description=None,
            created_by=user_id
        )


class TestCaseServiceGetCases:
    """Tests for get_cases_for_user method"""

    def test_get_cases_for_user_success(self, case_service, sample_case):
        """Test getting cases for user"""
        # Arrange
        user_id = "user_456"
        case_service.case_repo.get_all_for_user.return_value = [sample_case]

        # Act
        result = case_service.get_cases_for_user(user_id)

        # Assert
        case_service.case_repo.get_all_for_user.assert_called_once_with(user_id)
        assert len(result) == 1
        assert result[0].id == sample_case.id

    def test_get_cases_for_user_empty(self, case_service):
        """Test getting cases when user has no cases"""
        # Arrange
        user_id = "user_456"
        case_service.case_repo.get_all_for_user.return_value = []

        # Act
        result = case_service.get_cases_for_user(user_id)

        # Assert
        assert len(result) == 0


class TestCaseServiceGetById:
    """Tests for get_case_by_id method"""

    def test_get_case_by_id_success(self, case_service, sample_case):
        """Test getting case by ID with permission"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.has_access.return_value = True

        # Act
        result = case_service.get_case_by_id(case_id, user_id)

        # Assert
        case_service.case_repo.get_by_id.assert_called_once_with(case_id)
        case_service.member_repo.has_access.assert_called_once_with(case_id, user_id)
        assert result.id == case_id

    def test_get_case_by_id_not_found(self, case_service):
        """Test getting non-existent case"""
        # Arrange
        case_id = "nonexistent"
        user_id = "user_456"

        case_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            case_service.get_case_by_id(case_id, user_id)

    def test_get_case_by_id_no_access(self, case_service, sample_case):
        """Test getting case without access permission"""
        # Arrange
        case_id = "case_123abc"
        user_id = "other_user"

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            case_service.get_case_by_id(case_id, user_id)


class TestCaseServiceUpdate:
    """Tests for update_case method"""

    def test_update_case_success(self, case_service, mock_db, sample_case, sample_member):
        """Test successful case update"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"
        update_data = CaseUpdate(title="수정된 제목", description="수정된 설명")

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.get_member.return_value = sample_member

        # Act
        case_service.update_case(case_id, update_data, user_id)

        # Assert
        assert sample_case.title == "수정된 제목"
        assert sample_case.description == "수정된 설명"
        mock_db.commit.assert_called_once()

    def test_update_case_not_found(self, case_service):
        """Test updating non-existent case"""
        # Arrange
        case_id = "nonexistent"
        user_id = "user_456"
        update_data = CaseUpdate(title="수정된 제목")

        case_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            case_service.update_case(case_id, update_data, user_id)

    def test_update_case_viewer_no_permission(self, case_service, sample_case):
        """Test viewer cannot update case"""
        # Arrange
        case_id = "case_123abc"
        user_id = "viewer_user"
        update_data = CaseUpdate(title="수정된 제목")

        viewer_member = Mock(spec=CaseMember)
        viewer_member.role = CaseMemberRole.VIEWER

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.get_member.return_value = viewer_member

        # Act & Assert
        with pytest.raises(PermissionError):
            case_service.update_case(case_id, update_data, user_id)


class TestCaseServiceDelete:
    """Tests for delete_case method"""

    def test_delete_case_success(self, case_service, mock_db, sample_case, sample_member):
        """Test successful case deletion by owner"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        sample_member.role = "owner"

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.get_member.return_value = sample_member

        # Act
        case_service.delete_case(case_id, user_id)

        # Assert
        case_service.case_repo.soft_delete.assert_called_once_with(case_id)
        mock_db.commit.assert_called_once()

    def test_delete_case_not_owner(self, case_service, sample_case, sample_member):
        """Test non-owner cannot delete case"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        sample_member.role = "member"

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.get_member.return_value = sample_member

        # Act & Assert
        with pytest.raises(PermissionError):
            case_service.delete_case(case_id, user_id)


class TestCaseServiceMembers:
    """Tests for case member management methods"""

    def test_add_case_members_success(self, case_service, mock_db, sample_case, sample_user):
        """Test adding members to case"""
        # Arrange
        case_id = "case_123abc"
        owner_id = "owner_user"
        members_to_add = [
            CaseMemberAdd(user_id="new_user_1", permission=CaseMemberPermission.READ),
            CaseMemberAdd(user_id="new_user_2", permission=CaseMemberPermission.READ_WRITE)
        ]

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.is_owner.return_value = True
        case_service.user_repo.get_by_id.return_value = sample_user
        case_service.member_repo.has_access.return_value = True
        case_service.member_repo.get_all_members.return_value = []

        # Act
        case_service.add_case_members(case_id, members_to_add, owner_id)

        # Assert
        case_service.member_repo.add_members_batch.assert_called_once()
        mock_db.commit.assert_called()

    def test_add_members_not_owner(self, case_service, sample_case, sample_user):
        """Test non-owner cannot add members"""
        # Arrange
        case_id = "case_123abc"
        user_id = "regular_user"
        members_to_add = [
            CaseMemberAdd(user_id="new_user", permission=CaseMemberPermission.READ)
        ]

        sample_user.role = UserRole.LAWYER  # Not admin

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.is_owner.return_value = False
        case_service.user_repo.get_by_id.return_value = sample_user

        # Act & Assert
        with pytest.raises(PermissionError):
            case_service.add_case_members(case_id, members_to_add, user_id)

    def test_get_case_members_success(self, case_service, sample_case, sample_member, sample_user):
        """Test getting case members"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        case_service.case_repo.get_by_id.return_value = sample_case
        case_service.member_repo.has_access.return_value = True
        case_service.member_repo.get_all_members.return_value = [sample_member]
        case_service.user_repo.get_by_id.return_value = sample_user

        # Act
        result = case_service.get_case_members(case_id, user_id)

        # Assert
        assert result.total == 1
        assert len(result.members) == 1


class TestPermissionRoleConversion:
    """Tests for permission-role conversion methods"""

    def test_permission_to_role_read(self):
        """Test READ permission converts to VIEWER role"""
        result = CaseService._permission_to_role(CaseMemberPermission.READ)
        assert result == CaseMemberRole.VIEWER

    def test_permission_to_role_read_write(self):
        """Test READ_WRITE permission converts to MEMBER role"""
        result = CaseService._permission_to_role(CaseMemberPermission.READ_WRITE)
        assert result == CaseMemberRole.MEMBER

    def test_role_to_permission_owner(self):
        """Test OWNER role converts to READ_WRITE permission"""
        result = CaseService._role_to_permission(CaseMemberRole.OWNER)
        assert result == CaseMemberPermission.READ_WRITE

    def test_role_to_permission_member(self):
        """Test MEMBER role converts to READ_WRITE permission"""
        result = CaseService._role_to_permission(CaseMemberRole.MEMBER)
        assert result == CaseMemberPermission.READ_WRITE

    def test_role_to_permission_viewer(self):
        """Test VIEWER role converts to READ permission"""
        result = CaseService._role_to_permission(CaseMemberRole.VIEWER)
        assert result == CaseMemberPermission.READ
