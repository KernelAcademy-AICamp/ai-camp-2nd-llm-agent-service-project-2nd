"""
Unit tests for Evidence Service
TDD - Improving test coverage for evidence_service.py
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import uuid

from app.services.evidence_service import EvidenceService
from app.db.schemas import (
    PresignedUrlRequest,
    UploadCompleteRequest,
    Article840Category,
)
from app.db.models import Case, CaseMember, User, CaseStatus, CaseMemberRole
from app.middleware import NotFoundError, PermissionError


class TestParseArticle840Tags:
    """Unit tests for _parse_article_840_tags static method"""

    def test_parse_valid_tags(self):
        """Valid tags are parsed correctly"""
        evidence_data = {
            "article_840_tags": {
                "categories": ["adultery", "desertion"],
                "confidence": 0.95,
                "matched_keywords": ["외도", "유기"]
            }
        }
        result = EvidenceService._parse_article_840_tags(evidence_data)

        assert result is not None
        assert len(result.categories) == 2
        assert Article840Category.ADULTERY in result.categories
        assert Article840Category.DESERTION in result.categories
        assert result.confidence == 0.95
        assert "외도" in result.matched_keywords

    def test_parse_no_tags(self):
        """None returned when no tags"""
        evidence_data = {}
        result = EvidenceService._parse_article_840_tags(evidence_data)
        assert result is None

    def test_parse_invalid_category(self):
        """Invalid category returns None"""
        evidence_data = {
            "article_840_tags": {
                "categories": ["invalid_category"],
                "confidence": 0.5
            }
        }
        result = EvidenceService._parse_article_840_tags(evidence_data)
        assert result is None


class TestGetContentType:
    """Unit tests for _get_content_type static method"""

    def test_image_types(self):
        """Image extensions return correct content type"""
        assert EvidenceService._get_content_type("jpg") == "image/jpeg"
        assert EvidenceService._get_content_type("jpeg") == "image/jpeg"
        assert EvidenceService._get_content_type("png") == "image/png"
        assert EvidenceService._get_content_type("gif") == "image/gif"

    def test_audio_types(self):
        """Audio extensions return correct content type"""
        assert EvidenceService._get_content_type("mp3") == "audio/mpeg"
        assert EvidenceService._get_content_type("wav") == "audio/wav"
        assert EvidenceService._get_content_type("m4a") == "audio/mp4"

    def test_video_types(self):
        """Video extensions return correct content type"""
        assert EvidenceService._get_content_type("mp4") == "video/mp4"
        assert EvidenceService._get_content_type("avi") == "video/x-msvideo"
        assert EvidenceService._get_content_type("mov") == "video/quicktime"

    def test_document_types(self):
        """Document extensions return correct content type"""
        assert EvidenceService._get_content_type("pdf") == "application/pdf"
        assert EvidenceService._get_content_type("txt") == "text/plain"
        assert EvidenceService._get_content_type("csv") == "text/csv"
        assert EvidenceService._get_content_type("json") == "application/json"

    def test_unknown_type(self):
        """Unknown extension returns octet-stream"""
        assert EvidenceService._get_content_type("xyz") == "application/octet-stream"


class TestGenerateUploadPresignedUrl:
    """Unit tests for generate_upload_presigned_url method"""

    def test_presigned_url_success(self, test_env):
        """Successful presigned URL generation"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"presign_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Presign User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Presign Case",
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

        service = EvidenceService(db)
        request = PresignedUrlRequest(
            case_id=case.id,
            filename="test.jpg",
            content_type="image/jpeg"
        )

        with patch('app.services.evidence_service.generate_presigned_upload_url') as mock_presign:
            mock_presign.return_value = {
                "upload_url": "https://s3.amazonaws.com/...",
                "fields": {"key": "value"}
            }

            result = service.generate_upload_presigned_url(request, user.id)

            assert result.upload_url == "https://s3.amazonaws.com/..."
            assert result.evidence_temp_id is not None
            assert case.id in result.s3_key

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_presigned_url_case_not_found(self, test_env):
        """NotFoundError when case doesn't exist"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"nf_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = EvidenceService(db)
        request = PresignedUrlRequest(
            case_id="nonexistent-case",
            filename="test.jpg",
            content_type="image/jpeg"
        )

        with pytest.raises(NotFoundError):
            service.generate_upload_presigned_url(request, user.id)

        db.delete(user)
        db.commit()
        db.close()

    def test_presigned_url_no_access(self, test_env):
        """PermissionError when user has no access"""
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

        service = EvidenceService(db)
        request = PresignedUrlRequest(
            case_id=case.id,
            filename="test.jpg",
            content_type="image/jpeg"
        )

        with pytest.raises(PermissionError):
            service.generate_upload_presigned_url(request, other.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(owner)
        db.delete(other)
        db.commit()
        db.close()


class TestHandleUploadComplete:
    """Unit tests for handle_upload_complete method"""

    def test_upload_complete_success(self, test_env):
        """Successful upload completion handling"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"upload_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Upload User",
            role="lawyer"
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

        member = CaseMember(case_id=case.id, user_id=user.id, role=CaseMemberRole.OWNER)
        db.add(member)
        db.commit()

        service = EvidenceService(db)
        request = UploadCompleteRequest(
            case_id=case.id,
            s3_key=f"cases/{case.id}/raw/test123_photo.jpg",
            evidence_temp_id="test123",
            file_size=1024,
            note="Test note"
        )

        with patch('app.services.evidence_service.save_evidence_metadata') as mock_save, \
             patch('app.services.evidence_service.invoke_ai_worker') as mock_invoke, \
             patch('app.services.evidence_service.update_evidence_status') as mock_status:

            mock_invoke.return_value = {"StatusCode": 200}

            result = service.handle_upload_complete(request, user.id)

            assert result.evidence_id == "test123"
            assert result.case_id == case.id
            assert result.status == "processing"
            mock_save.assert_called_once()
            mock_invoke.assert_called_once()

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_upload_complete_ai_worker_failure(self, test_env):
        """Handle AI worker invocation failure"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"fail_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Fail User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Fail Case",
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

        service = EvidenceService(db)
        request = UploadCompleteRequest(
            case_id=case.id,
            s3_key=f"cases/{case.id}/raw/test456_photo.jpg",
            evidence_temp_id="test456",
            file_size=1024
        )

        with patch('app.services.evidence_service.save_evidence_metadata'), \
             patch('app.services.evidence_service.invoke_ai_worker') as mock_invoke, \
             patch('app.services.evidence_service.update_evidence_status'):

            mock_invoke.side_effect = Exception("Lambda invocation failed")

            result = service.handle_upload_complete(request, user.id)

            assert result.status == "failed"
            assert result.evidence_id == "test456"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestGetEvidenceList:
    """Unit tests for get_evidence_list method"""

    def test_get_evidence_list_success(self, test_env):
        """Successfully get evidence list"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"list_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="List User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="List Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_case') as mock_get:
            mock_get.return_value = [
                {
                    "evidence_id": "ev1",
                    "case_id": case.id,
                    "type": "image",
                    "filename": "photo.jpg",
                    "size": 1024,
                    "created_at": "2025-01-01T00:00:00",
                    "status": "completed"
                }
            ]

            result = service.get_evidence_list(case.id, user.id)

            assert len(result) == 1
            assert result[0].id == "ev1"
            assert result[0].type == "image"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_evidence_list_with_category_filter(self, test_env):
        """Filter evidence by Article 840 category"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"cat_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Cat User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Cat Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_case') as mock_get:
            mock_get.return_value = [
                {
                    "evidence_id": "ev1",
                    "case_id": case.id,
                    "type": "image",
                    "filename": "photo1.jpg",
                    "size": 1024,
                    "created_at": "2025-01-01T00:00:00",
                    "status": "completed",
                    "article_840_tags": {
                        "categories": ["adultery"],
                        "confidence": 0.9
                    }
                },
                {
                    "evidence_id": "ev2",
                    "case_id": case.id,
                    "type": "image",
                    "filename": "photo2.jpg",
                    "size": 2048,
                    "created_at": "2025-01-02T00:00:00",
                    "status": "completed",
                    "article_840_tags": {
                        "categories": ["desertion"],
                        "confidence": 0.85
                    }
                }
            ]

            result = service.get_evidence_list(
                case.id,
                user.id,
                categories=[Article840Category.ADULTERY]
            )

            assert len(result) == 1
            assert result[0].id == "ev1"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestGetEvidenceDetail:
    """Unit tests for get_evidence_detail method"""

    def test_get_evidence_detail_success(self, test_env):
        """Successfully get evidence detail"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"det_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Det User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Det Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get:
            mock_get.return_value = {
                "evidence_id": "ev1",
                "case_id": case.id,
                "type": "image",
                "filename": "photo.jpg",
                "size": 1024,
                "s3_key": f"cases/{case.id}/raw/ev1_photo.jpg",
                "content_type": "image/jpeg",
                "created_at": "2025-01-01T00:00:00",
                "status": "completed",
                "ai_summary": "Test summary",
                "article_840_tags": {
                    "categories": ["adultery"],
                    "confidence": 0.9,
                    "matched_keywords": ["외도"]
                }
            }

            result = service.get_evidence_detail("ev1", user.id)

            assert result.id == "ev1"
            assert result.type == "image"
            assert result.ai_summary == "Test summary"
            assert result.article_840_tags is not None
            assert Article840Category.ADULTERY in result.article_840_tags.categories

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_evidence_detail_not_found(self, test_env):
        """NotFoundError when evidence doesn't exist"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"nf_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="NF User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get:
            mock_get.return_value = None

            with pytest.raises(NotFoundError):
                service.get_evidence_detail("nonexistent", user.id)

        db.delete(user)
        db.commit()
        db.close()


class TestRetryProcessing:
    """Unit tests for retry_processing method"""

    def test_retry_processing_success(self, test_env):
        """Successfully retry processing"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"retry_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Retry User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Retry Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get, \
             patch('app.services.evidence_service.update_evidence_status'), \
             patch('app.services.evidence_service.invoke_ai_worker') as mock_invoke:

            mock_get.return_value = {
                "evidence_id": "ev1",
                "case_id": case.id,
                "status": "failed",
                "s3_key": f"cases/{case.id}/raw/ev1_photo.jpg"
            }
            mock_invoke.return_value = {"StatusCode": 200}

            result = service.retry_processing("ev1", user.id)

            assert result["success"] is True
            assert result["status"] == "processing"

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_retry_processing_invalid_status(self, test_env):
        """ValueError when evidence not in failed state"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"invst_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="InvSt User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="InvSt Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get:
            mock_get.return_value = {
                "evidence_id": "ev1",
                "case_id": case.id,
                "status": "completed",
                "s3_key": f"cases/{case.id}/raw/ev1_photo.jpg"
            }

            with pytest.raises(ValueError):
                service.retry_processing("ev1", user.id)

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()


class TestGetEvidenceStatus:
    """Unit tests for get_evidence_status method"""

    def test_get_evidence_status_success(self, test_env):
        """Successfully get evidence status"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]
        now = datetime.now(timezone.utc)

        user = User(
            email=f"status_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="Status User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        case = Case(
            title="Status Case",
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

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get:
            mock_get.return_value = {
                "evidence_id": "ev1",
                "case_id": case.id,
                "status": "processing",
                "error_message": None,
                "updated_at": "2025-01-01T00:00:00"
            }

            result = service.get_evidence_status("ev1", user.id)

            assert result["evidence_id"] == "ev1"
            assert result["status"] == "processing"
            assert result["error_message"] is None

        # Cleanup
        db.query(CaseMember).filter(CaseMember.case_id == case.id).delete()
        db.query(Case).filter(Case.id == case.id).delete()
        db.delete(user)
        db.commit()
        db.close()

    def test_get_evidence_status_not_found(self, test_env):
        """NotFoundError when evidence doesn't exist"""
        from app.db.session import get_db
        from app.core.security import hash_password

        db = next(get_db())
        unique_id = uuid.uuid4().hex[:8]

        user = User(
            email=f"nfst_{unique_id}@test.com",
            hashed_password=hash_password("pass"),
            name="NFSt User",
            role="lawyer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = EvidenceService(db)

        with patch('app.services.evidence_service.get_evidence_by_id') as mock_get:
            mock_get.return_value = None

            with pytest.raises(NotFoundError):
                service.get_evidence_status("nonexistent", user.id)

        db.delete(user)
        db.commit()
        db.close()
