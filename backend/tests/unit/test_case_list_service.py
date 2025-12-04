"""
Unit tests for Case List Service
TDD - Improving test coverage for case_list_service.py
"""

import pytest
from datetime import datetime, timezone
import uuid

from app.services.case_list_service import CaseListService
from app.db.models import Case, CaseMember, User, CaseStatus, CaseMemberRole
from app.schemas.case_list import (
    CaseFilter,
    CaseSortField,
    SortOrder,
    BulkActionType,
)


class TestCaseListService:
    """Unit tests for CaseListService"""

    def test_get_cases_returns_empty_list_for_new_user(self, test_env):
        """User with no cases gets empty list"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"empty_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Empty User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseListService(db)
        result = service.get_cases(user.id)

        assert result.items == []
        assert result.total == 0

        db.delete(user)
        db.commit()
        db.close()

    def test_get_cases_returns_user_cases(self, test_env):
        """User with cases gets their cases"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"with_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Test Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.get_cases(user.id)

        assert result.total == 1

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_cases_with_status_filter(self, test_env):
        """Filter cases by status"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"filter_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        cases = []
        for status in [CaseStatus.ACTIVE, CaseStatus.OPEN]:
            case = Case(
                title=f"Case {status.value}",
                status=status,
                created_by=user.id,
                created_at=now,
                updated_at=now
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
            db.add(member)
            db.commit()

        service = CaseListService(db)
        filters = CaseFilter(status=[CaseStatus.ACTIVE])
        result = service.get_cases(user.id, filters=filters)

        assert result.total == 1

        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_cases_pagination(self, test_env):
        """Pagination works correctly"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"page_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        cases = []
        for i in range(10):
            case = Case(
                title=f"Case {i}",
                status=CaseStatus.ACTIVE,
                created_by=user.id,
                created_at=now,
                updated_at=now
            )
            db.add(case)
            db.commit()
            db.refresh(case)
            cases.append(case)

            member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
            db.add(member)
            db.commit()

        service = CaseListService(db)
        result = service.get_cases(user.id, page=2, page_size=3)

        assert result.total == 10
        assert len(result.items) == 3
        assert result.page == 2

        for case in cases:
            db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
            db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestBulkActions:
    """Unit tests for bulk actions"""

    def test_bulk_action_change_status(self, test_env):
        """Bulk status change works"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"bulk_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Bulk Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.execute_bulk_action(
            user.id,
            [case.id],
            BulkActionType.CHANGE_STATUS,
            {"new_status": "in_progress"}
        )

        assert result.successful == 1
        db.refresh(case)
        assert case.status == CaseStatus.IN_PROGRESS

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_bulk_action_invalid_case(self, test_env):
        """Invalid case returns failure"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"inv_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = CaseListService(db)
        result = service.execute_bulk_action(
            user.id,
            ["invalid-id"],
            BulkActionType.REQUEST_AI_ANALYSIS
        )

        assert result.failed == 1

        db.delete(user)
        db.commit()
        db.close()

    def test_bulk_action_delete(self, test_env):
        """Bulk delete soft deletes case"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"del_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Delete Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.execute_bulk_action(user.id, [case.id], BulkActionType.DELETE)

        assert result.successful == 1
        db.refresh(case)
        assert case.status == CaseStatus.CLOSED

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_bulk_action_export(self, test_env):
        """Bulk export returns success"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"exp_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Export Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.execute_bulk_action(user.id, [case.id], BulkActionType.EXPORT)

        assert result.successful == 1

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestCaseDetail:
    """Unit tests for case detail"""

    def test_get_case_detail_success(self, test_env):
        """Get case detail with access"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"det_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Detail User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Detail Case",
            client_name="Client",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.get_case_detail(user.id, case.id)

        assert result is not None
        assert result.title == "Detail Case"

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_case_detail_no_access(self, test_env):
        """No access returns None"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        owner = User(
            email=f"own_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Owner",
            role="lawyer"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        other = User(
            email=f"oth_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Other",
            role="lawyer"
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        case = Case(
            title="Private",
            status=CaseStatus.ACTIVE,
            created_by=owner.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=owner.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = CaseListService(db)
        result = service.get_case_detail(other.id, case.id)

        assert result is None

        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(owner)
        db.delete(other)
        db.commit()
        db.close()
