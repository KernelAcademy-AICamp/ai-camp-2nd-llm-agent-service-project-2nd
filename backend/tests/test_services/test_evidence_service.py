"""
Tests for EvidenceService
"""

import pytest
from unittest.mock import Mock, patch
from app.services.evidence_service import EvidenceService
from app.db.schemas import (
    PresignedUrlRequest,
    UploadCompleteRequest,
    Article840Category
)
from app.db.models import Case
from app.middleware import NotFoundError, PermissionError


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def evidence_service(mock_db):
    """Create EvidenceService with mocked dependencies"""
    service = EvidenceService(mock_db)
    service.case_repo = Mock()
    service.member_repo = Mock()
    return service


@pytest.fixture
def sample_case():
    """Sample Case model instance"""
    case = Mock(spec=Case)
    case.id = "case_123abc"
    case.title = "테스트 사건"
    case.description = "테스트 설명"
    case.status = "active"
    case.created_by = "user_456"
    return case


class TestEvidenceServicePresignedUrl:
    """Tests for generate_upload_presigned_url method"""

    @patch("app.services.evidence_service.generate_presigned_upload_url")
    @patch("app.services.evidence_service.settings")
    def test_generate_presigned_url_success(
        self, mock_settings, mock_generate_url, evidence_service, sample_case
    ):
        """Test successful presigned URL generation"""
        # Arrange
        mock_settings.S3_EVIDENCE_BUCKET = "test-bucket"
        mock_settings.S3_PRESIGNED_URL_EXPIRE_SECONDS = 300

        mock_generate_url.return_value = {
            "upload_url": "https://s3.amazonaws.com/test-bucket",
            "fields": {"key": "value"}
        }

        request = PresignedUrlRequest(
            case_id="case_123abc",
            filename="test_file.jpg",
            content_type="image/jpeg"
        )
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.generate_upload_presigned_url(request, user_id)

        # Assert
        assert result.upload_url == "https://s3.amazonaws.com/test-bucket"
        assert result.evidence_temp_id.startswith("ev_")
        evidence_service.case_repo.get_by_id.assert_called_once_with("case_123abc")
        evidence_service.member_repo.has_access.assert_called_once_with("case_123abc", "user_456")

    def test_generate_presigned_url_case_not_found(self, evidence_service):
        """Test presigned URL generation with non-existent case"""
        # Arrange
        request = PresignedUrlRequest(
            case_id="nonexistent",
            filename="test_file.jpg",
            content_type="image/jpeg"
        )
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            evidence_service.generate_upload_presigned_url(request, user_id)

    def test_generate_presigned_url_no_access(self, evidence_service, sample_case):
        """Test presigned URL generation without access permission"""
        # Arrange
        request = PresignedUrlRequest(
            case_id="case_123abc",
            filename="test_file.jpg",
            content_type="image/jpeg"
        )
        user_id = "unauthorized_user"

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            evidence_service.generate_upload_presigned_url(request, user_id)


class TestEvidenceServiceUploadComplete:
    """Tests for handle_upload_complete method"""

    @patch("app.services.evidence_service.save_evidence_metadata")
    def test_handle_upload_complete_success(
        self, mock_save_metadata, evidence_service, sample_case
    ):
        """Test successful upload completion handling"""
        # Arrange
        request = UploadCompleteRequest(
            case_id="case_123abc",
            evidence_temp_id="ev_temp123",
            s3_key="cases/case_123abc/raw/ev_temp123_test.jpg",
            note="테스트 증거"
        )
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.handle_upload_complete(request, user_id)

        # Assert
        assert result.case_id == "case_123abc"
        assert result.evidence_id.startswith("ev_")
        assert result.status == "pending"
        mock_save_metadata.assert_called_once()

    @patch("app.services.evidence_service.save_evidence_metadata")
    def test_handle_upload_complete_extracts_filename(
        self, mock_save_metadata, evidence_service, sample_case
    ):
        """Test filename extraction from s3_key"""
        # Arrange
        request = UploadCompleteRequest(
            case_id="case_123abc",
            evidence_temp_id="ev_temp123",
            s3_key="cases/case_123abc/raw/ev_abc123def_document.pdf"
        )
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.handle_upload_complete(request, user_id)

        # Assert
        assert result.filename == "document.pdf"

    def test_handle_upload_complete_case_not_found(self, evidence_service):
        """Test upload complete with non-existent case"""
        # Arrange
        request = UploadCompleteRequest(
            case_id="nonexistent",
            evidence_temp_id="ev_temp123",
            s3_key="cases/nonexistent/raw/test.jpg"
        )
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            evidence_service.handle_upload_complete(request, user_id)

    def test_handle_upload_complete_no_access(self, evidence_service, sample_case):
        """Test upload complete without access permission"""
        # Arrange
        request = UploadCompleteRequest(
            case_id="case_123abc",
            evidence_temp_id="ev_temp123",
            s3_key="cases/case_123abc/raw/test.jpg"
        )
        user_id = "unauthorized_user"

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            evidence_service.handle_upload_complete(request, user_id)


class TestEvidenceServiceGetList:
    """Tests for get_evidence_list method"""

    @patch("app.services.evidence_service.get_evidence_by_case")
    def test_get_evidence_list_success(
        self, mock_get_evidence, evidence_service, sample_case
    ):
        """Test getting evidence list for a case"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        mock_get_evidence.return_value = [
            {
                "id": "ev_001",
                "case_id": case_id,
                "type": "image",
                "filename": "photo.jpg",
                "size": 512000,
                "created_at": "2024-01-01T00:00:00",
                "status": "done"
            }
        ]

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.get_evidence_list(case_id, user_id)

        # Assert
        assert len(result) == 1
        assert result[0].id == "ev_001"
        assert result[0].filename == "photo.jpg"

    @patch("app.services.evidence_service.get_evidence_by_case")
    def test_get_evidence_list_empty(
        self, mock_get_evidence, evidence_service, sample_case
    ):
        """Test getting evidence list when case has no evidence"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        mock_get_evidence.return_value = []

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.get_evidence_list(case_id, user_id)

        # Assert
        assert len(result) == 0

    @patch("app.services.evidence_service.get_evidence_by_case")
    def test_get_evidence_list_with_category_filter(
        self, mock_get_evidence, evidence_service, sample_case
    ):
        """Test filtering evidence by Article 840 categories"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        mock_get_evidence.return_value = [
            {
                "id": "ev_001",
                "case_id": case_id,
                "type": "audio",
                "filename": "recording.mp3",
                "size": 1048576,
                "created_at": "2024-01-01T00:00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["adultery"],
                    "confidence": 0.9,
                    "matched_keywords": ["부정행위"]
                }
            },
            {
                "id": "ev_002",
                "case_id": case_id,
                "type": "image",
                "filename": "photo.jpg",
                "size": 512000,
                "created_at": "2024-01-02T00:00:00",
                "status": "done",
                "article_840_tags": {
                    "categories": ["desertion"],
                    "confidence": 0.8,
                    "matched_keywords": ["유기"]
                }
            }
        ]

        evidence_service.case_repo.get_by_id.return_value = sample_case
        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.get_evidence_list(
            case_id, user_id,
            categories=[Article840Category.ADULTERY]
        )

        # Assert
        assert len(result) == 1
        assert result[0].id == "ev_001"

    def test_get_evidence_list_case_not_found(self, evidence_service):
        """Test getting evidence list for non-existent case"""
        # Arrange
        case_id = "nonexistent"
        user_id = "user_456"

        evidence_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            evidence_service.get_evidence_list(case_id, user_id)


class TestEvidenceServiceGetDetail:
    """Tests for get_evidence_detail method"""

    @patch("app.services.evidence_service.get_evidence_by_id")
    def test_get_evidence_detail_success(
        self, mock_get_evidence, evidence_service
    ):
        """Test getting evidence detail"""
        # Arrange
        evidence_id = "ev_001"
        user_id = "user_456"

        mock_get_evidence.return_value = {
            "id": evidence_id,
            "case_id": "case_123abc",
            "type": "audio",
            "filename": "recording.mp3",
            "size": 2097152,
            "s3_key": "cases/case_123abc/raw/recording.mp3",
            "content_type": "audio/mpeg",
            "created_at": "2024-01-01T00:00:00",
            "status": "done",
            "ai_summary": "테스트 요약",
            "labels": ["폭언"],
            "content": "음성 텍스트 내용"
        }

        evidence_service.member_repo.has_access.return_value = True

        # Act
        result = evidence_service.get_evidence_detail(evidence_id, user_id)

        # Assert
        assert result.id == evidence_id
        assert result.ai_summary == "테스트 요약"
        assert result.content == "음성 텍스트 내용"

    @patch("app.services.evidence_service.get_evidence_by_id")
    def test_get_evidence_detail_not_found(self, mock_get_evidence, evidence_service):
        """Test getting non-existent evidence"""
        # Arrange
        evidence_id = "nonexistent"
        user_id = "user_456"

        mock_get_evidence.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            evidence_service.get_evidence_detail(evidence_id, user_id)

    @patch("app.services.evidence_service.get_evidence_by_id")
    def test_get_evidence_detail_no_access(self, mock_get_evidence, evidence_service):
        """Test getting evidence without access permission"""
        # Arrange
        evidence_id = "ev_001"
        user_id = "unauthorized_user"

        mock_get_evidence.return_value = {
            "id": evidence_id,
            "case_id": "case_123abc",
            "type": "audio",
            "filename": "recording.mp3",
            "size": 2097152,
            "s3_key": "cases/case_123abc/raw/recording.mp3",
            "content_type": "audio/mpeg",
            "created_at": "2024-01-01T00:00:00",
            "status": "pending"
        }

        evidence_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            evidence_service.get_evidence_detail(evidence_id, user_id)


class TestEvidenceServiceContentType:
    """Tests for _get_content_type static method"""

    def test_get_content_type_image_jpeg(self):
        """Test JPEG content type"""
        assert EvidenceService._get_content_type("jpg") == "image/jpeg"
        assert EvidenceService._get_content_type("jpeg") == "image/jpeg"

    def test_get_content_type_image_png(self):
        """Test PNG content type"""
        assert EvidenceService._get_content_type("png") == "image/png"

    def test_get_content_type_audio(self):
        """Test audio content types"""
        assert EvidenceService._get_content_type("mp3") == "audio/mpeg"
        assert EvidenceService._get_content_type("wav") == "audio/wav"

    def test_get_content_type_video(self):
        """Test video content types"""
        assert EvidenceService._get_content_type("mp4") == "video/mp4"

    def test_get_content_type_document(self):
        """Test document content types"""
        assert EvidenceService._get_content_type("pdf") == "application/pdf"
        assert EvidenceService._get_content_type("json") == "application/json"

    def test_get_content_type_unknown(self):
        """Test unknown extension returns octet-stream"""
        assert EvidenceService._get_content_type("xyz") == "application/octet-stream"


class TestArticle840TagParsing:
    """Tests for _parse_article_840_tags static method"""

    def test_parse_tags_success(self):
        """Test successful parsing of Article 840 tags"""
        evidence_data = {
            "article_840_tags": {
                "categories": ["adultery", "desertion"],
                "confidence": 0.85,
                "matched_keywords": ["부정행위", "유기"]
            }
        }

        result = EvidenceService._parse_article_840_tags(evidence_data)

        assert result is not None
        assert len(result.categories) == 2
        assert Article840Category.ADULTERY in result.categories
        assert result.confidence == 0.85

    def test_parse_tags_empty(self):
        """Test parsing when no tags present"""
        evidence_data = {}

        result = EvidenceService._parse_article_840_tags(evidence_data)

        assert result is None

    def test_parse_tags_invalid_category(self):
        """Test parsing with invalid category value"""
        evidence_data = {
            "article_840_tags": {
                "categories": ["invalid_category"],
                "confidence": 0.5,
                "matched_keywords": []
            }
        }

        result = EvidenceService._parse_article_840_tags(evidence_data)

        assert result is None
