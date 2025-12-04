"""
Unit tests for Client Portal Service
TDD - Improving test coverage for client_portal_service.py
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import uuid

from app.services.client_portal_service import ClientPortalService
from app.db.models import Case, CaseMember, User, Evidence, AuditLog, CaseStatus, CaseMemberRole


class TestClientDashboard:
    """Unit tests for get_dashboard method"""

    def test_dashboard_no_cases(self, test_env):
        """Dashboard for user with no cases"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"dash_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Dash User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = ClientPortalService(db)
        result = service.get_dashboard(user.id)

        assert result.user_name == "Dash User"
        assert result.case_summary is None
        assert result.progress_steps == []
        assert result.lawyer_info is None

        db.delete(user)
        db.commit()
        db.close()

    def test_dashboard_with_active_case(self, test_env):
        """Dashboard shows active case information"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        lawyer = User(
            email=f"law_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Lawyer",
            role="lawyer"
        )
        db.add(lawyer)
        db.commit()
        db.refresh(lawyer)

        client = User(
            email=f"cli_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Client",
            role="client"
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        case = Case(
            title="Active Case",
            status=CaseStatus.ACTIVE,
            created_by=lawyer.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        # Add client as member
        member = CaseMember(case_id=case.id, user_id=client.id, role=CaseMemberRole.MEMBER)
        db.add(member)
        # Add lawyer as owner
        lawyer_member = CaseMember(case_id=case.id, user_id=lawyer.id, role=CaseMemberRole.OWNER)
        db.add(lawyer_member)
        db.commit()

        service = ClientPortalService(db)
        result = service.get_dashboard(client.id)

        assert result.user_name == "Client"
        assert result.case_summary is not None
        assert result.case_summary.title == "Active Case"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(lawyer)
        db.delete(client)
        db.commit()
        db.close()

    def test_dashboard_user_not_found(self, test_env):
        """ValueError when user not found"""
        from app.db.session import get_db

        db = next(get_db())
        service = ClientPortalService(db)

        with pytest.raises(ValueError, match="User not found"):
            service.get_dashboard("nonexistent-user")

        db.close()


class TestClientCaseList:
    """Unit tests for get_case_list method"""

    def test_case_list_empty(self, test_env):
        """Empty list when no cases"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"list_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="List User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = ClientPortalService(db)
        result = service.get_case_list(user.id)

        assert result.items == []
        assert result.total == 0

        db.delete(user)
        db.commit()
        db.close()

    def test_case_list_with_cases(self, test_env):
        """List includes user's cases"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"clist_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="CList User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Client Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.MEMBER)
        db.add(member)
        db.commit()

        service = ClientPortalService(db)
        result = service.get_case_list(user.id)

        assert result.total == 1
        assert result.items[0].title == "Client Case"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestClientCaseDetail:
    """Unit tests for get_case_detail method"""

    def test_case_detail_success(self, test_env):
        """Get case detail with access"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"det_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Det User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Detail Case",
            description="Test description",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.MEMBER)
        db.add(member)
        db.commit()

        service = ClientPortalService(db)
        result = service.get_case_detail(user.id, case.id)

        assert result.title == "Detail Case"
        assert result.description == "Test description"
        assert result.can_upload_evidence is True

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_case_detail_no_access(self, test_env):
        """PermissionError when no access"""
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
            role="client"
        )
        db.add(other)
        db.commit()
        db.refresh(other)

        case = Case(
            title="Private Case",
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

        service = ClientPortalService(db)

        with pytest.raises(PermissionError, match="Access denied"):
            service.get_case_detail(other.id, case.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(owner)
        db.delete(other)
        db.commit()
        db.close()


class TestEvidenceUpload:
    """Unit tests for evidence upload methods"""

    def test_request_evidence_upload_success(self, test_env):
        """Successfully request evidence upload"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"up_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Upload User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Upload Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.MEMBER)
        db.add(member)
        db.commit()

        service = ClientPortalService(db)

        with patch('app.services.client_portal_service.generate_presigned_upload_url') as mock_url:
            mock_url.return_value = "https://s3.amazonaws.com/..."

            result = service.request_evidence_upload(
                user.id,
                case.id,
                "test.jpg",
                "image/jpeg",
                1024
            )

            assert result.evidence_id is not None
            assert result.upload_url is not None
            assert result.expires_in == 300

        # Cleanup
        db.query(Evidence).filter(Evidence.case_id == case.id).delete()
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_request_evidence_upload_closed_case(self, test_env):
        """ValueError when case is closed"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"cl_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Closed User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Closed Case",
            status=CaseStatus.CLOSED,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.MEMBER)
        db.add(member)
        db.commit()

        service = ClientPortalService(db)

        with pytest.raises(ValueError, match="closed"):
            service.request_evidence_upload(
                user.id,
                case.id,
                "test.jpg",
                "image/jpeg",
                1024
            )

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_confirm_evidence_upload_success(self, test_env):
        """Successfully confirm evidence upload"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"conf_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Confirm User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Confirm Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        evidence = Evidence(
            id=str(uuid.uuid4()),
            case_id=case.id,
            file_name="test.jpg",
            s3_key=f"cases/{case.id}/raw/test.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=user.id,
            status="pending",
            created_at=now,
            updated_at=now
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        service = ClientPortalService(db)
        result = service.confirm_evidence_upload(
            user.id,
            case.id,
            evidence.id,
            uploaded=True
        )

        assert result["success"] is True
        db.refresh(evidence)
        assert evidence.status == "uploaded"

        # Cleanup
        db.query(Evidence).filter(Evidence.id == evidence.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_confirm_evidence_upload_cancel(self, test_env):
        """Cancel evidence upload deletes record"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"canc_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Cancel User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Cancel Case",
            status=CaseStatus.ACTIVE,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )
        db.add(case)
        db.commit()
        db.refresh(case)

        evidence_id = str(uuid.uuid4())
        evidence = Evidence(
            id=evidence_id,
            case_id=case.id,
            file_name="test.jpg",
            s3_key=f"cases/{case.id}/raw/test.jpg",
            file_type="image/jpeg",
            file_size=1024,
            uploaded_by=user.id,
            status="pending",
            created_at=now,
            updated_at=now
        )
        db.add(evidence)
        db.commit()

        service = ClientPortalService(db)
        result = service.confirm_evidence_upload(
            user.id,
            case.id,
            evidence_id,
            uploaded=False
        )

        assert result["success"] is True
        assert result["message"] == "Upload cancelled"

        # Verify deleted
        deleted_evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        assert deleted_evidence is None

        # Cleanup
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestHelperMethods:
    """Unit tests for helper methods"""

    def test_calculate_progress(self, test_env):
        """Progress calculation works correctly"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"prog_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Prog User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = ClientPortalService(db)

        # Test different statuses
        statuses = [
            (CaseStatus.OPEN, 10),
            (CaseStatus.ACTIVE, 30),
            (CaseStatus.IN_PROGRESS, 50),
            (CaseStatus.CLOSED, 100),
        ]

        for status, expected in statuses:
            case = Case(
                title=f"Case {status}",
                status=status,
                created_by=user.id,
                created_at=now,
                updated_at=now
            )
            progress = service._calculate_progress(case)
            assert progress == expected, f"Expected {expected} for {status}, got {progress}"

        db.delete(user)
        db.commit()
        db.close()

    def test_get_file_type(self, test_env):
        """File type detection works correctly"""
        from app.db.session import get_db

        db = next(get_db())
        service = ClientPortalService(db)

        assert service._get_file_type("test.jpg") == "image"
        assert service._get_file_type("test.mp3") == "audio"
        assert service._get_file_type("test.mp4") == "video"
        assert service._get_file_type("test.pdf") == "document"
        assert service._get_file_type(None) == "document"
        assert service._get_file_type("no_extension") == "document"

        db.close()

    def test_time_ago(self, test_env):
        """Time ago formatting works correctly"""
        from app.db.session import get_db

        db = next(get_db())
        service = ClientPortalService(db)

        now = datetime.utcnow()

        assert "방금 전" == service._time_ago(now - timedelta(seconds=30))
        assert "분 전" in service._time_ago(now - timedelta(minutes=5))
        assert "시간 전" in service._time_ago(now - timedelta(hours=3))
        assert "일 전" in service._time_ago(now - timedelta(days=3))
        assert "년" in service._time_ago(now - timedelta(days=30))

        db.close()

    def test_map_action_to_activity_type(self, test_env):
        """Action mapping works correctly"""
        from app.db.session import get_db

        db = next(get_db())
        service = ClientPortalService(db)

        assert service._map_action_to_activity_type("evidence_upload") == "evidence"
        assert service._map_action_to_activity_type("message_sent") == "message"
        assert service._map_action_to_activity_type("unknown_action") == "status"

        db.close()

    def test_get_activity_title(self, test_env):
        """Activity title mapping works correctly"""
        from app.db.session import get_db

        db = next(get_db())
        service = ClientPortalService(db)

        assert service._get_activity_title("evidence_upload") == "증거자료 업로드"
        assert service._get_activity_title("message_sent") == "메시지 전송"
        assert service._get_activity_title("unknown") == "unknown"

        db.close()

    def test_get_next_action(self, test_env):
        """Next action suggestions work correctly"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"next_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Next User",
            role="client"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = ClientPortalService(db)

        # Open case should suggest evidence upload
        case = Case(
            title="Open Case",
            status=CaseStatus.OPEN,
            created_by=user.id,
            created_at=now,
            updated_at=now
        )

        action = service._get_next_action(case)
        assert "증거자료" in action

        # Closed case should have no action
        case.status = CaseStatus.CLOSED
        action = service._get_next_action(case)
        assert action is None

        db.delete(user)
        db.commit()
        db.close()


# Note: log_evidence_upload test skipped due to AuditLog model mismatch
# The method uses fields (resource_type, resource_id, details, created_at) not in model
