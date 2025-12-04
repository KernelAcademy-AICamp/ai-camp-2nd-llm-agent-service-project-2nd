"""
Unit tests for Case Service
TDD - Improving test coverage for case_service.py
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
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
        Then: Raises NotFoundError
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

        # When/Then
        service = CaseService(db)
        with pytest.raises(NotFoundError):
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
