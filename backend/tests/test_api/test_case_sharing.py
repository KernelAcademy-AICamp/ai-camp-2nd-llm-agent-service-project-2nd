"""
Tests for Case Sharing (1.10)

Tests the following endpoints:
- POST /cases/{case_id}/members - Add members to case
- GET /cases/{case_id}/members - List case members
"""

import pytest
from unittest.mock import Mock, patch
from app.db.models import UserRole, CaseMemberRole


class TestCaseSharing:
    """Test suite for case sharing functionality"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.commit = Mock()
        session.flush = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def sample_case(self):
        """Sample case data"""
        case = Mock()
        case.id = "case_test123"
        case.title = "테스트 이혼 사건"
        case.description = "테스트용 사건"
        case.status = "active"
        case.created_by = "user_owner"
        return case

    @pytest.fixture
    def sample_owner_user(self):
        """Sample owner user"""
        user = Mock()
        user.id = "user_owner"
        user.email = "owner@example.com"
        user.name = "소유자"
        user.role = UserRole.LAWYER
        return user

    @pytest.fixture
    def sample_member_user(self):
        """Sample member user to be added"""
        user = Mock()
        user.id = "user_member"
        user.email = "member@example.com"
        user.name = "멤버"
        user.role = UserRole.LAWYER
        return user

    @pytest.fixture
    def sample_viewer_user(self):
        """Sample viewer user to be added"""
        user = Mock()
        user.id = "user_viewer"
        user.email = "viewer@example.com"
        user.name = "뷰어"
        user.role = UserRole.STAFF
        return user

    def test_add_case_members_as_owner(
        self,
        client,
        auth_headers,
        sample_case,
        sample_owner_user,
        sample_member_user,
        sample_viewer_user,
        mock_db_session,
    ):
        """
        Test POST /cases/{case_id}/members by case owner

        Given: Case owner wants to add team members
        When: POST /cases/{case_id}/members with members list
        Then: Members are added successfully, returns updated member list
        """
        case_id = sample_case.id

        # Request body
        request_body = {
            "members": [
                {
                    "user_id": sample_member_user.id,
                    "permission": "read_write"
                },
                {
                    "user_id": sample_viewer_user.id,
                    "permission": "read"
                }
            ]
        }

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            mock_member_instance = mock_member_repo.return_value
            mock_member_instance.is_owner.return_value = True
            mock_member_instance.add_members_batch.return_value = []

            # Mock get_all_members for response
            owner_member = Mock()
            owner_member.user_id = sample_owner_user.id
            owner_member.role = CaseMemberRole.OWNER

            new_member1 = Mock()
            new_member1.user_id = sample_member_user.id
            new_member1.role = CaseMemberRole.MEMBER

            new_member2 = Mock()
            new_member2.user_id = sample_viewer_user.id
            new_member2.role = CaseMemberRole.VIEWER

            mock_member_instance.get_all_members.return_value = [
                owner_member,
                new_member1,
                new_member2
            ]

            # Mock user repository
            def mock_get_by_id(user_id):
                if user_id == sample_owner_user.id:
                    return sample_owner_user
                elif user_id == sample_member_user.id:
                    return sample_member_user
                elif user_id == sample_viewer_user.id:
                    return sample_viewer_user
                return None

            mock_user_repo.return_value.get_by_id.side_effect = mock_get_by_id

            # Call API
            response = client.post(
                f"/cases/{case_id}/members",
                headers=auth_headers,
                json=request_body
            )

        # Assert response
        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "members" in data
        assert "total" in data
        assert data["total"] == 3

        # Check members list
        members = data["members"]
        assert len(members) == 3

        # Check owner
        owner = next(m for m in members if m["user_id"] == sample_owner_user.id)
        assert owner["permission"] == "read_write"
        assert owner["role"] == "owner"

        # Check member with read_write permission
        member = next(m for m in members if m["user_id"] == sample_member_user.id)
        assert member["permission"] == "read_write"
        assert member["role"] == "member"

        # Check viewer with read permission
        viewer = next(m for m in members if m["user_id"] == sample_viewer_user.id)
        assert viewer["permission"] == "read"
        assert viewer["role"] == "viewer"

    def test_add_case_members_as_non_owner_fails(
        self,
        client,
        auth_headers,
        sample_case,
        sample_member_user,
    ):
        """
        Test POST /cases/{case_id}/members by non-owner fails

        Given: User is not case owner or admin
        When: POST /cases/{case_id}/members
        Then: Returns 403 Forbidden
        """
        case_id = sample_case.id

        # Request body
        request_body = {
            "members": [
                {
                    "user_id": sample_member_user.id,
                    "permission": "read"
                }
            ]
        }

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            # User is not owner
            mock_member_repo.return_value.is_owner.return_value = False

            # User is not admin
            non_admin_user = Mock()
            non_admin_user.role = UserRole.LAWYER
            mock_user_repo.return_value.get_by_id.return_value = non_admin_user

            # Call API
            response = client.post(
                f"/cases/{case_id}/members",
                headers=auth_headers,
                json=request_body
            )

        # Assert response
        assert response.status_code == 403
        assert "owner or admin" in response.json()["detail"].lower()

    def test_add_case_members_with_nonexistent_user_fails(
        self,
        client,
        auth_headers,
        sample_case,
        sample_owner_user,
    ):
        """
        Test POST /cases/{case_id}/members with non-existent user fails

        Given: Case owner tries to add non-existent user
        When: POST /cases/{case_id}/members
        Then: Returns 404 Not Found
        """
        case_id = sample_case.id

        # Request body with non-existent user
        request_body = {
            "members": [
                {
                    "user_id": "user_nonexistent",
                    "permission": "read"
                }
            ]
        }

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case
            mock_member_repo.return_value.is_owner.return_value = True

            # User does not exist
            mock_user_repo.return_value.get_by_id.return_value = None

            # Call API
            response = client.post(
                f"/cases/{case_id}/members",
                headers=auth_headers,
                json=request_body
            )

        # Assert response
        assert response.status_code == 404
        assert "user" in response.json()["detail"].lower()

    def test_add_case_members_admin_can_add(
        self,
        client,
        auth_headers,
        sample_case,
        sample_member_user,
    ):
        """
        Test POST /cases/{case_id}/members by admin succeeds

        Given: Admin user (not case owner) wants to add members
        When: POST /cases/{case_id}/members
        Then: Members are added successfully
        """
        case_id = sample_case.id

        # Request body
        request_body = {
            "members": [
                {
                    "user_id": sample_member_user.id,
                    "permission": "read"
                }
            ]
        }

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            # User is not owner
            mock_member_instance = mock_member_repo.return_value
            mock_member_instance.is_owner.return_value = False

            # But user is admin
            admin_user = Mock()
            admin_user.role = UserRole.ADMIN
            mock_user_repo.return_value.get_by_id.return_value = admin_user

            # Mock successful add
            mock_member_instance.add_members_batch.return_value = []
            mock_member_instance.get_all_members.return_value = []

            # Call API
            response = client.post(
                f"/cases/{case_id}/members",
                headers=auth_headers,
                json=request_body
            )

        # Assert response
        assert response.status_code == 201

    def test_get_case_members_as_member(
        self,
        client,
        auth_headers,
        sample_case,
        sample_owner_user,
        sample_member_user,
    ):
        """
        Test GET /cases/{case_id}/members by case member

        Given: User is a case member
        When: GET /cases/{case_id}/members
        Then: Returns list of all case members
        """
        case_id = sample_case.id

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            # User has access
            mock_member_instance = mock_member_repo.return_value
            mock_member_instance.has_access.return_value = True

            # Mock members list
            owner_member = Mock()
            owner_member.user_id = sample_owner_user.id
            owner_member.role = CaseMemberRole.OWNER

            regular_member = Mock()
            regular_member.user_id = sample_member_user.id
            regular_member.role = CaseMemberRole.MEMBER

            mock_member_instance.get_all_members.return_value = [
                owner_member,
                regular_member
            ]

            # Mock user repository
            def mock_get_by_id(user_id):
                if user_id == sample_owner_user.id:
                    return sample_owner_user
                elif user_id == sample_member_user.id:
                    return sample_member_user
                return None

            mock_user_repo.return_value.get_by_id.side_effect = mock_get_by_id

            # Call API
            response = client.get(
                f"/cases/{case_id}/members",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "members" in data
        assert "total" in data
        assert data["total"] == 2

        # Check members include owner and member
        members = data["members"]
        member_ids = [m["user_id"] for m in members]
        assert sample_owner_user.id in member_ids
        assert sample_member_user.id in member_ids

    def test_get_case_members_as_non_member_fails(
        self,
        client,
        auth_headers,
        sample_case,
    ):
        """
        Test GET /cases/{case_id}/members by non-member fails

        Given: User is not a case member
        When: GET /cases/{case_id}/members
        Then: Returns 403 Forbidden
        """
        case_id = sample_case.id

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            # User does not have access
            mock_member_repo.return_value.has_access.return_value = False

            # Call API
            response = client.get(
                f"/cases/{case_id}/members",
                headers=auth_headers
            )

        # Assert response
        assert response.status_code == 403
        assert "access" in response.json()["detail"].lower()

    def test_add_existing_member_updates_permission(
        self,
        client,
        auth_headers,
        sample_case,
        sample_owner_user,
        sample_member_user,
    ):
        """
        Test adding an existing member updates their permission

        Given: User is already a member with READ permission
        When: POST /cases/{case_id}/members with same user but READ_WRITE
        Then: User's permission is updated to READ_WRITE
        """
        case_id = sample_case.id

        # Request body - upgrade viewer to member
        request_body = {
            "members": [
                {
                    "user_id": sample_member_user.id,
                    "permission": "read_write"
                }
            ]
        }

        # Mock service layer
        with patch("app.services.case_service.CaseRepository") as mock_case_repo, \
             patch("app.services.case_service.CaseMemberRepository") as mock_member_repo, \
             patch("app.services.case_service.UserRepository") as mock_user_repo:

            # Setup mocks
            mock_case_repo.return_value.get_by_id.return_value = sample_case

            mock_member_instance = mock_member_repo.return_value
            mock_member_instance.is_owner.return_value = True

            # Member now has upgraded role
            upgraded_member = Mock()
            upgraded_member.user_id = sample_member_user.id
            upgraded_member.role = CaseMemberRole.MEMBER  # Upgraded from VIEWER

            mock_member_instance.get_all_members.return_value = [upgraded_member]

            mock_user_repo.return_value.get_by_id.return_value = sample_member_user

            # Call API
            response = client.post(
                f"/cases/{case_id}/members",
                headers=auth_headers,
                json=request_body
            )

        # Assert response
        assert response.status_code == 201
        data = response.json()

        # Check member has updated permission
        member = data["members"][0]
        assert member["user_id"] == sample_member_user.id
        assert member["permission"] == "read_write"
        assert member["role"] == "member"

    def test_permission_to_role_mapping(self):
        """
        Test permission to role conversion

        Given: CaseMemberPermission enum values
        When: Converted to CaseMemberRole
        Then:
            - READ → VIEWER
            - READ_WRITE → MEMBER
        """
        from app.db.schemas import CaseMemberPermission
        from app.services.case_service import CaseService

        # Test READ → VIEWER
        viewer_role = CaseService._permission_to_role(CaseMemberPermission.READ)
        assert viewer_role == CaseMemberRole.VIEWER

        # Test READ_WRITE → MEMBER
        member_role = CaseService._permission_to_role(CaseMemberPermission.READ_WRITE)
        assert member_role == CaseMemberRole.MEMBER

    def test_role_to_permission_mapping(self):
        """
        Test role to permission conversion

        Given: CaseMemberRole enum values
        When: Converted to CaseMemberPermission
        Then:
            - OWNER → READ_WRITE
            - MEMBER → READ_WRITE
            - VIEWER → READ
        """
        from app.db.schemas import CaseMemberPermission
        from app.services.case_service import CaseService

        # Test OWNER → READ_WRITE
        owner_perm = CaseService._role_to_permission(CaseMemberRole.OWNER)
        assert owner_perm == CaseMemberPermission.READ_WRITE

        # Test MEMBER → READ_WRITE
        member_perm = CaseService._role_to_permission(CaseMemberRole.MEMBER)
        assert member_perm == CaseMemberPermission.READ_WRITE

        # Test VIEWER → READ
        viewer_perm = CaseService._role_to_permission(CaseMemberRole.VIEWER)
        assert viewer_perm == CaseMemberPermission.READ
