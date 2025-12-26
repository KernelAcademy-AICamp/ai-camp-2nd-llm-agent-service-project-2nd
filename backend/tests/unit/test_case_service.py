"""
Unit tests for Case Service
TDD - Improving test coverage for case_service.py
"""

import pytest
from unittest.mock import patch
import uuid

from app.services.case_service import CaseService
from app.db.models import Case, CaseMember, User, CaseStatus, CaseMemberRole
from app.db.schemas import CaseCreate, CaseUpdate, CaseMemberAdd, CaseMemberPermission
from app.middleware import NotFoundError, PermissionError


class TestCaseServiceCreate:
    """Unit tests for case creation"""

    def test_create_case_success(self, test_env):
        """
        Given: Valid case data
        When: create_case is called
        Then: Case is created and user is added as owner
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"create_case_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Create Case User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # When
        service = CaseService(db)
        case_data = CaseCreate(
            title="New Case",
            client_name="Test Client",
            description="Test Description"
        )
        result = service.create_case(case_data, user.id)

        # Then
        assert result.title == "New Case"
        assert result.client_name == "Test Client"

        # Verify owner membership
        member = db.query(CaseMember).filter(
            CaseMember.case_id == result.id,
            CaseMember.user_id == user.id
        ).first()
        assert member is not None
        assert member.role == CaseMemberRole.OWNER

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == result.id).delete()
        db.query(Case).filter(Case.id == result.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestCaseServiceGet:
    """Unit tests for case retrieval"""

    def test_get_cases_for_user_returns_accessible_cases(self, test_env):
        """
        Given: User with multiple cases
        When: get_cases_for_user is called
        Then: Returns all accessible cases
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"get_cases_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Get Cases User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        cases = []
        for i in range(3):
            case = Case(
                title=f"User Case {i+1}",
                status=CaseStatus.ACTIVE,
                created_by=user.id
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(
                case_id=case.id,
                user_id=user.id,
                role=CaseMemberRole.OWNER
            )
            db.add(member)
            db.commit()

        # When
        service = CaseService(db)
        result = service.get_cases_for_user(user.id)

        # Then
        assert len(result) == 3

        # Cleanup
        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_get_case_by_id_success(self, test_env):
        """
        Given: Case exists and user has access
        When: get_case_by_id is called
        Then: Returns case data
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"get_by_id_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Get By ID User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Get By ID Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When
        service = CaseService(db)
        result = service.get_case_by_id(case.id, user.id)

        # Then
        assert result.title == "Get By ID Case"
        assert result.id == case.id

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_get_case_by_id_not_found(self, test_env):
        """
        Given: Case does not exist
        When: get_case_by_id is called
        Then: Raises PermissionError (prevents info leakage about case existence)
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"not_found_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Not Found User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # When/Then: PermissionError instead of NotFoundError to prevent info leakage
        service = CaseService(db)
        with pytest.raises(PermissionError):
            service.get_case_by_id("non-existent-id", user.id)

        # Cleanup
        db.delete(user)
        db.commit()
        db.close()

    def test_get_case_by_id_no_access(self, test_env):
        """
        Given: Case exists but user has no access
        When: get_case_by_id is called
        Then: Raises PermissionError
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"owner_no_access_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        other_user = User(
            email=f"other_no_access_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Other",
            role="lawyer"
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        case = Case(
            title="Private Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When/Then
        service = CaseService(db)
        with pytest.raises(PermissionError):
            service.get_case_by_id(case.id, other_user.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(other_user)
        db.commit()
        db.close()


class TestCaseServiceUpdate:
    """Unit tests for case updates"""

    def test_update_case_title(self, test_env):
        """
        Given: Case exists and user is owner
        When: update_case is called with new title
        Then: Case title is updated
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"update_title_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Update Title User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Original Title",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When
        service = CaseService(db)
        update_data = CaseUpdate(title="Updated Title")
        result = service.update_case(case.id, update_data, user.id)

        # Then
        assert result.title == "Updated Title"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_update_case_viewer_cannot_update(self, test_env):
        """
        Given: User is viewer of case
        When: update_case is called
        Then: Raises PermissionError
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"owner_update_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        viewer = User(
            email=f"viewer_update_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Viewer",
            role="lawyer"
        )
        db.add(viewer)
        db.commit()
        db.refresh(viewer)

        case = Case(
            title="Owner's Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        viewer_member = CaseMember(
            case_id=case.id,
            user_id=viewer.id,
            role=CaseMemberRole.VIEWER
        )
        db.add(viewer_member)
        db.commit()

        # When/Then
        service = CaseService(db)
        update_data = CaseUpdate(title="Viewer Update")
        with pytest.raises(PermissionError):
            service.update_case(case.id, update_data, viewer.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(viewer)
        db.commit()
        db.close()


class TestCaseServiceDelete:
    """Unit tests for case deletion"""

    @patch('app.services.case_service.delete_case_collection')
    @patch('app.services.case_service.clear_case_evidence')
    def test_delete_case_owner_can_delete(self, mock_clear, mock_delete, test_env):
        """
        Given: User is owner of case
        When: delete_case is called
        Then: Case is soft deleted
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        mock_delete.return_value = True
        mock_clear.return_value = 0

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"delete_owner_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Delete Owner User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="To Delete",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When
        service = CaseService(db)
        service.delete_case(case.id, user.id)

        # Then
        db.refresh(case)
        assert case.status == CaseStatus.CLOSED

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    def test_delete_case_non_owner_cannot_delete(self, test_env):
        """
        Given: User is member but not owner
        When: delete_case is called
        Then: Raises PermissionError
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"owner_delete_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        member_user = User(
            email=f"member_delete_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Member",
            role="lawyer"
        )
        db.add(member_user)
        db.commit()
        db.refresh(member_user)

        case = Case(
            title="Owner's Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        member = CaseMember(
            case_id=case.id,
            user_id=member_user.id,
            role=CaseMemberRole.MEMBER
        )
        db.add(member)
        db.commit()

        # When/Then
        service = CaseService(db)
        with pytest.raises(PermissionError):
            service.delete_case(case.id, member_user.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(member_user)
        db.commit()
        db.close()


class TestCaseServiceMembers:
    """Unit tests for case member management"""

    def test_get_case_members_success(self, test_env):
        """
        Given: Case with multiple members
        When: get_case_members is called
        Then: Returns all members
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"owner_members_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        member_user = User(
            email=f"member_members_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Member",
            role="lawyer"
        )
        db.add(member_user)
        db.commit()
        db.refresh(member_user)

        case = Case(
            title="Case With Members",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        member = CaseMember(
            case_id=case.id,
            user_id=member_user.id,
            role=CaseMemberRole.MEMBER
        )
        db.add(member)
        db.commit()

        # When
        service = CaseService(db)
        result = service.get_case_members(case.id, owner.id)

        # Then
        assert result.total == 2
        assert len(result.members) == 2

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(member_user)
        db.commit()
        db.close()

    def test_add_case_members_success(self, test_env):
        """
        Given: Case exists and user is owner
        When: add_case_members is called
        Then: New members are added
        """
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"owner_add_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        new_member = User(
            email=f"new_member_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="New Member",
            role="lawyer"
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        case = Case(
            title="Add Members Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        # When
        service = CaseService(db)
        members_to_add = [
            CaseMemberAdd(user_id=new_member.id, permission=CaseMemberPermission.READ_WRITE)
        ]
        result = service.add_case_members(case.id, members_to_add, owner.id)

        # Then
        assert result.total == 2

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(new_member)
        db.commit()
        db.close()


class TestDeleteCaseEdgeCases:
    """Unit tests for delete_case edge cases"""

    @patch('app.services.case_service.delete_case_collection')
    @patch('app.services.case_service.clear_case_evidence')
    def test_delete_case_qdrant_returns_false(self, mock_clear, mock_delete, test_env):
        """Logs warning when Qdrant collection not found (line 196)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        # Qdrant returns False (not found)
        mock_delete.return_value = False
        mock_clear.return_value = 0

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"qdrant_false_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Qdrant False User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Qdrant False Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When - should not raise, just log warning
        service = CaseService(db)
        service.delete_case(case.id, user.id)

        # Then
        db.refresh(case)
        assert case.status == CaseStatus.CLOSED
        mock_delete.assert_called_once()

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    @patch('app.services.case_service.delete_case_collection')
    @patch('app.services.case_service.clear_case_evidence')
    def test_delete_case_qdrant_exception(self, mock_clear, mock_delete, test_env):
        """Continues deletion when Qdrant fails (lines 197-198)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        # Qdrant raises exception
        mock_delete.side_effect = Exception("Qdrant error")
        mock_clear.return_value = 0

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"qdrant_exc_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Qdrant Exception User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Qdrant Exception Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When - should not raise, just log error
        service = CaseService(db)
        service.delete_case(case.id, user.id)

        # Then
        db.refresh(case)
        assert case.status == CaseStatus.CLOSED

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()

    @patch('app.services.case_service.delete_case_collection')
    @patch('app.services.case_service.clear_case_evidence')
    def test_delete_case_dynamodb_exception(self, mock_clear, mock_delete, test_env):
        """Continues deletion when DynamoDB fails (lines 205-206)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        # Qdrant succeeds, DynamoDB fails
        mock_delete.return_value = True
        mock_clear.side_effect = Exception("DynamoDB error")

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"dynamo_exc_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="DynamoDB Exception User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="DynamoDB Exception Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When - should not raise, just log error
        service = CaseService(db)
        service.delete_case(case.id, user.id)

        # Then
        db.refresh(case)
        assert case.status == CaseStatus.CLOSED

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()


class TestUpdateCaseDescription:
    """Unit tests for update_case with description field"""

    def test_update_case_with_description(self, test_env):
        """Updates case with description (line 159)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"update_desc_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Update Desc User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Case With Description",
            description="Original description",
            status=CaseStatus.ACTIVE,
            created_by=user.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=user.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        # When
        service = CaseService(db)
        update_data = CaseUpdate(description="Updated description")
        result = service.update_case(case.id, update_data, user.id)

        # Then
        assert result.description == "Updated description"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(user)
        db.commit()
        db.close()


class TestPermissionConversion:
    """Unit tests for permission/role conversion using enum methods"""

    def test_permission_to_role_viewer(self, test_env):
        """READ permission converts to VIEWER role via to_role() method"""
        result = CaseMemberPermission.READ.to_role()
        assert result == CaseMemberRole.VIEWER

    def test_permission_to_role_member(self, test_env):
        """READ_WRITE permission converts to MEMBER role via to_role() method"""
        result = CaseMemberPermission.READ_WRITE.to_role()
        assert result == CaseMemberRole.MEMBER

    def test_role_to_permission_viewer(self, test_env):
        """VIEWER role converts to READ permission via to_permission() method"""
        result = CaseMemberRole.VIEWER.to_permission()
        assert result == CaseMemberPermission.READ

    def test_role_to_permission_member(self, test_env):
        """MEMBER role converts to READ_WRITE permission via to_permission() method"""
        result = CaseMemberRole.MEMBER.to_permission()
        assert result == CaseMemberPermission.READ_WRITE

    def test_role_to_permission_owner(self, test_env):
        """OWNER role converts to READ_WRITE permission via to_permission() method"""
        result = CaseMemberRole.OWNER.to_permission()
        assert result == CaseMemberPermission.READ_WRITE


class TestUpdateCaseErrors:
    """Unit tests for update_case error cases"""

    def test_update_case_not_found(self, test_env):
        """PermissionError when case doesn't exist (prevents info leakage)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"upd_notfound_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Update NotFound User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseService(db)
        update_data = CaseUpdate(title="New Title")

        # PermissionError instead of NotFoundError to prevent info leakage
        with pytest.raises(PermissionError):
            service.update_case("nonexistent-case-id", update_data, user.id)

        db.delete(user)
        db.commit()
        db.close()

    def test_update_case_no_access(self, test_env):
        """PermissionError when user has no access (line 149)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"upd_owner_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        stranger = User(
            email=f"upd_stranger_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Stranger",
            role="lawyer"
        )
        db.add(owner)
        db.add(stranger)
        db.commit()
        db.refresh(owner)
        db.refresh(stranger)

        case = Case(
            title="Owner's Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(member)
        db.commit()

        service = CaseService(db)
        update_data = CaseUpdate(title="Stranger's Update")

        # Stranger has no membership
        with pytest.raises(PermissionError):
            service.update_case(case.id, update_data, stranger.id)

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(stranger)
        db.commit()
        db.close()


class TestDeleteCaseErrors:
    """Unit tests for delete_case error cases"""

    def test_delete_case_not_found(self, test_env):
        """PermissionError when case doesn't exist (prevents info leakage)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"del_notfound_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Delete NotFound User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseService(db)

        # PermissionError instead of NotFoundError to prevent info leakage
        with pytest.raises(PermissionError):
            service.delete_case("nonexistent-case-id", user.id)

        db.delete(user)
        db.commit()
        db.close()


class TestAddMembersErrors:
    """Unit tests for add_case_members error cases"""

    def test_add_members_case_not_found(self, test_env):
        """PermissionError when case doesn't exist (prevents info leakage)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"add_notfound_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Add NotFound User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseService(db)
        members = [CaseMemberAdd(user_id=user.id, permission=CaseMemberPermission.READ_WRITE)]

        # PermissionError instead of NotFoundError to prevent info leakage
        with pytest.raises(PermissionError):
            service.add_case_members("nonexistent-case-id", members, user.id)

        db.delete(user)
        db.commit()
        db.close()

    def test_add_members_not_owner(self, test_env):
        """PermissionError when user is not owner or admin (line 243)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"add_owner_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        member_user = User(
            email=f"add_member_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Member",
            role="lawyer"
        )
        new_user = User(
            email=f"add_new_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="New User",
            role="lawyer"
        )
        db.add(owner)
        db.add(member_user)
        db.add(new_user)
        db.commit()
        db.refresh(owner)
        db.refresh(member_user)
        db.refresh(new_user)

        case = Case(
            title="Add Members Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        member = CaseMember(
            case_id=case.id,
            user_id=member_user.id,
            role=CaseMemberRole.MEMBER
        )
        db.add(owner_member)
        db.add(member)
        db.commit()

        service = CaseService(db)
        members = [CaseMemberAdd(user_id=new_user.id, permission=CaseMemberPermission.READ_WRITE)]

        # Member (not owner) trying to add members
        with pytest.raises(PermissionError):
            service.add_case_members(case.id, members, member_user.id)

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(member_user)
        db.delete(new_user)
        db.commit()
        db.close()

    def test_add_members_user_not_found(self, test_env):
        """NotFoundError when member user doesn't exist (line 249)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"add_owner_nf_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        case = Case(
            title="Add User NF Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        service = CaseService(db)
        members = [CaseMemberAdd(user_id="nonexistent-user-id", permission=CaseMemberPermission.READ_WRITE)]

        with pytest.raises(NotFoundError):
            service.add_case_members(case.id, members, owner.id)

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.commit()
        db.close()


class TestGetMembersErrors:
    """Unit tests for get_case_members error cases"""

    def test_get_members_case_not_found(self, test_env):
        """PermissionError when case doesn't exist (prevents info leakage)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"get_mem_nf_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Get Members NotFound User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseService(db)

        # PermissionError instead of NotFoundError to prevent info leakage
        with pytest.raises(PermissionError):
            service.get_case_members("nonexistent-case-id", user.id)

        db.delete(user)
        db.commit()
        db.close()

    def test_get_members_no_access(self, test_env):
        """PermissionError when user has no access (line 289)"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        owner = User(
            email=f"get_mem_owner_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Owner",
            role="lawyer"
        )
        stranger = User(
            email=f"get_mem_stranger_{unique_id}@test.com",
            hashed_password=hash_password("password123"),
            name="Stranger",
            role="lawyer"
        )
        db.add(owner)
        db.add(stranger)
        db.commit()
        db.refresh(owner)
        db.refresh(stranger)

        case = Case(
            title="Get Members Case",
            status=CaseStatus.ACTIVE,
            created_by=owner.id
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        owner_member = CaseMember(
            case_id=case.id,
            user_id=owner.id,
            role=CaseMemberRole.OWNER
        )
        db.add(owner_member)
        db.commit()

        service = CaseService(db)

        # Stranger has no access
        with pytest.raises(PermissionError):
            service.get_case_members(case.id, stranger.id)

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.delete(case)
        db.delete(owner)
        db.delete(stranger)
        db.commit()
        db.close()
