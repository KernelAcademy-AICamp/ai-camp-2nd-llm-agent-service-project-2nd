"""
Tests for DraftService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from io import BytesIO
from app.services.draft_service import DraftService
from app.db.schemas import (
    DraftPreviewRequest,
    DraftPreviewResponse,
    DraftCitation,
    DraftExportFormat
)
from app.db.models import Case
from app.middleware import NotFoundError, PermissionError, ValidationError


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


@pytest.fixture
def draft_service(mock_db):
    """Create DraftService with mocked dependencies"""
    service = DraftService(mock_db)
    service.case_repo = Mock()
    service.member_repo = Mock()
    return service


@pytest.fixture
def sample_case():
    """Sample Case model instance"""
    case = Mock(spec=Case)
    case.id = "case_123abc"
    case.title = "이혼 사건 테스트"
    case.description = "테스트용 이혼 사건입니다"
    case.status = "active"
    case.created_by = "user_456"
    return case


@pytest.fixture
def sample_evidence_list():
    """Sample evidence list from DynamoDB"""
    return [
        {
            "id": "ev_001",
            "case_id": "case_123abc",
            "type": "audio",
            "filename": "recording.mp3",
            "status": "done",
            "content": "배우자가 폭언을 했다",
            "labels": ["폭언"]
        },
        {
            "id": "ev_002",
            "case_id": "case_123abc",
            "type": "image",
            "filename": "photo.jpg",
            "status": "done",
            "content": "메시지 캡처 이미지",
            "labels": ["불화"]
        }
    ]


@pytest.fixture
def sample_rag_results():
    """Sample RAG search results"""
    return [
        {
            "id": "ev_001",
            "content": "배우자가 폭언을 했다는 내용의 음성 녹음",
            "labels": ["폭언"],
            "speaker": "원고",
            "timestamp": "2024-01-15",
            "_score": 0.95
        }
    ]


class TestDraftServicePreview:
    """Tests for generate_draft_preview method"""

    @patch("app.services.draft_service.generate_chat_completion")
    @patch("app.services.draft_service.search_evidence_by_semantic")
    @patch("app.services.draft_service.get_evidence_by_case")
    def test_generate_draft_preview_success(
        self,
        mock_get_evidence,
        mock_rag_search,
        mock_gpt,
        draft_service,
        sample_case,
        sample_evidence_list,
        sample_rag_results
    ):
        """Test successful draft preview generation"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"
        request = DraftPreviewRequest(
            sections=["청구원인", "증거목록"],
            language="ko",
            style="formal"
        )

        draft_service.case_repo.get_by_id.return_value = sample_case
        draft_service.member_repo.has_access.return_value = True
        mock_get_evidence.return_value = sample_evidence_list
        mock_rag_search.return_value = sample_rag_results
        mock_gpt.return_value = "생성된 초안 내용입니다."

        # Act
        result = draft_service.generate_draft_preview(case_id, request, user_id)

        # Assert
        assert result.case_id == case_id
        assert result.draft_text == "생성된 초안 내용입니다."
        assert len(result.citations) > 0
        mock_gpt.assert_called_once()

    @patch("app.services.draft_service.get_evidence_by_case")
    def test_generate_draft_preview_case_not_found(
        self, mock_get_evidence, draft_service
    ):
        """Test draft preview with non-existent case"""
        # Arrange
        case_id = "nonexistent"
        user_id = "user_456"
        request = DraftPreviewRequest()

        draft_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            draft_service.generate_draft_preview(case_id, request, user_id)

    @patch("app.services.draft_service.get_evidence_by_case")
    def test_generate_draft_preview_no_access(
        self, mock_get_evidence, draft_service, sample_case
    ):
        """Test draft preview without access permission"""
        # Arrange
        case_id = "case_123abc"
        user_id = "unauthorized_user"
        request = DraftPreviewRequest()

        draft_service.case_repo.get_by_id.return_value = sample_case
        draft_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            draft_service.generate_draft_preview(case_id, request, user_id)

    @patch("app.services.draft_service.get_evidence_by_case")
    def test_generate_draft_preview_no_evidence(
        self, mock_get_evidence, draft_service, sample_case
    ):
        """Test draft preview when case has no evidence"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"
        request = DraftPreviewRequest()

        draft_service.case_repo.get_by_id.return_value = sample_case
        draft_service.member_repo.has_access.return_value = True
        mock_get_evidence.return_value = []

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            draft_service.generate_draft_preview(case_id, request, user_id)

        assert "증거가 하나도 없습니다" in str(exc_info.value)


class TestDraftServiceRagSearch:
    """Tests for _perform_rag_search method"""

    @patch("app.services.draft_service.search_evidence_by_semantic")
    def test_rag_search_with_claim_section(
        self, mock_search, draft_service
    ):
        """Test RAG search includes fault keywords for 청구원인 section"""
        # Arrange
        case_id = "case_123abc"
        sections = ["청구원인"]

        mock_search.return_value = []

        # Act
        draft_service._perform_rag_search(case_id, sections)

        # Assert
        call_args = mock_search.call_args
        assert "귀책사유" in call_args.kwargs.get("query", call_args[1].get("query", ""))
        assert call_args.kwargs.get("top_k", call_args[1].get("top_k")) == 10

    @patch("app.services.draft_service.search_evidence_by_semantic")
    def test_rag_search_general_sections(
        self, mock_search, draft_service
    ):
        """Test RAG search for general sections"""
        # Arrange
        case_id = "case_123abc"
        sections = ["당사자", "사건경위"]

        mock_search.return_value = []

        # Act
        draft_service._perform_rag_search(case_id, sections)

        # Assert
        call_args = mock_search.call_args
        assert call_args.kwargs.get("top_k", call_args[1].get("top_k")) == 5


class TestDraftServicePromptBuilding:
    """Tests for _build_draft_prompt method"""

    def test_build_draft_prompt_structure(self, draft_service, sample_case):
        """Test prompt structure has system and user messages"""
        # Arrange
        sections = ["청구원인"]
        evidence_context = [{"id": "ev_001", "content": "증거 내용"}]
        legal_context = [{"article": "840", "content": "이혼 사유"}]

        # Act
        messages = draft_service._build_draft_prompt(
            case=sample_case,
            sections=sections,
            evidence_context=evidence_context,
            legal_context=legal_context,
            language="ko",
            style="formal"
        )

        # Assert
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "법률가" in messages[0]["content"]
        assert sample_case.title in messages[1]["content"]

    def test_format_rag_context_empty(self, draft_service):
        """Test RAG context formatting when empty"""
        result = draft_service._format_rag_context([])
        assert "증거 자료 없음" in result

    def test_format_rag_context_with_data(self, draft_service, sample_rag_results):
        """Test RAG context formatting with data"""
        result = draft_service._format_rag_context(sample_rag_results)

        assert "[증거 1]" in result
        assert "ev_001" in result
        assert "폭언" in result

    def test_format_rag_context_truncates_long_content(self, draft_service):
        """Test RAG context truncates long content"""
        long_content = "가" * 1000
        rag_results = [{
            "id": "ev_001",
            "content": long_content,
            "labels": []
        }]

        result = draft_service._format_rag_context(rag_results)

        assert "..." in result
        assert len(result) < len(long_content)


class TestDraftServiceCitations:
    """Tests for _extract_citations method"""

    def test_extract_citations_success(self, draft_service, sample_rag_results):
        """Test successful citation extraction"""
        result = draft_service._extract_citations(sample_rag_results)

        assert len(result) == 1
        assert isinstance(result[0], DraftCitation)
        assert result[0].evidence_id == "ev_001"
        assert result[0].labels == ["폭언"]

    def test_extract_citations_empty(self, draft_service):
        """Test citation extraction with empty results"""
        result = draft_service._extract_citations([])
        assert len(result) == 0

    def test_extract_citations_truncates_snippet(self, draft_service):
        """Test citation snippet truncation for long content"""
        long_content = "가" * 500
        rag_results = [{
            "id": "ev_001",
            "content": long_content,
            "labels": []
        }]

        result = draft_service._extract_citations(rag_results)

        assert len(result[0].snippet) <= 203  # 200 + "..."


class TestDraftServiceExport:
    """Tests for export_draft method"""

    @patch.object(DraftService, "generate_draft_preview")
    @patch.object(DraftService, "_generate_docx")
    def test_export_draft_docx_success(
        self, mock_generate_docx, mock_preview, draft_service, sample_case
    ):
        """Test successful DOCX export"""
        # Arrange
        case_id = "case_123abc"
        user_id = "user_456"

        draft_service.case_repo.get_by_id.return_value = sample_case
        draft_service.member_repo.has_access.return_value = True

        mock_preview.return_value = DraftPreviewResponse(
            case_id=case_id,
            draft_text="초안 내용",
            citations=[],
            generated_at=datetime.now(timezone.utc)
        )

        mock_generate_docx.return_value = (
            BytesIO(b"docx content"),
            "draft_test.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # Act
        result = draft_service.export_draft(case_id, user_id, DraftExportFormat.DOCX)

        # Assert
        assert result[1].endswith(".docx")
        mock_generate_docx.assert_called_once()

    def test_export_draft_case_not_found(self, draft_service):
        """Test export with non-existent case"""
        # Arrange
        case_id = "nonexistent"
        user_id = "user_456"

        draft_service.case_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            draft_service.export_draft(case_id, user_id)

    def test_export_draft_no_access(self, draft_service, sample_case):
        """Test export without access permission"""
        # Arrange
        case_id = "case_123abc"
        user_id = "unauthorized_user"

        draft_service.case_repo.get_by_id.return_value = sample_case
        draft_service.member_repo.has_access.return_value = False

        # Act & Assert
        with pytest.raises(PermissionError):
            draft_service.export_draft(case_id, user_id)


class TestDraftServiceDocxGeneration:
    """Tests for _generate_docx method"""

    @patch("app.services.draft_service.DOCX_AVAILABLE", True)
    @patch("app.services.draft_service.Document")
    def test_generate_docx_creates_document(
        self, mock_document_class, draft_service, sample_case
    ):
        """Test DOCX generation creates proper document structure"""
        # Arrange
        mock_doc = MagicMock()
        mock_document_class.return_value = mock_doc

        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="초안 본문 내용입니다.\n\n두 번째 문단입니다.",
            citations=[
                DraftCitation(
                    evidence_id="ev_001",
                    snippet="증거 내용",
                    labels=["폭언"]
                )
            ],
            generated_at=datetime.now(timezone.utc)
        )

        # Act
        result = draft_service._generate_docx(sample_case, draft_response)

        # Assert
        mock_doc.add_heading.assert_called()
        mock_doc.add_paragraph.assert_called()
        mock_doc.save.assert_called_once()
        assert result[1].endswith(".docx")

    @patch("app.services.draft_service.DOCX_AVAILABLE", False)
    def test_generate_docx_not_available(self, draft_service, sample_case):
        """Test DOCX generation raises error when python-docx not installed"""
        # Arrange
        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="초안",
            citations=[],
            generated_at=datetime.now(timezone.utc)
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            draft_service._generate_docx(sample_case, draft_response)

        assert "python-docx" in str(exc_info.value)


class TestDraftServicePdfGeneration:
    """Tests for _generate_pdf method"""

    def test_generate_pdf_creates_document(self, draft_service, sample_case):
        """Test PDF generation creates proper document with Korean support"""
        # Arrange
        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="초안 본문 내용입니다.\n\n두 번째 문단입니다.",
            citations=[
                DraftCitation(
                    evidence_id="ev_001",
                    snippet="증거 내용",
                    labels=["폭언"]
                )
            ],
            generated_at=datetime.now(timezone.utc)
        )

        # Act
        try:
            result = draft_service._generate_pdf(sample_case, draft_response)

            # Assert
            file_buffer, filename, content_type = result
            assert filename.endswith(".pdf")
            assert content_type == "application/pdf"
            assert file_buffer.read(4) == b"%PDF"  # PDF magic bytes
        except ValidationError as e:
            # reportlab not installed - this is acceptable
            assert "reportlab" in str(e)

    def test_generate_pdf_with_citations(self, draft_service, sample_case):
        """Test PDF generation includes citations section"""
        # Arrange
        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="초안 내용",
            citations=[
                DraftCitation(
                    evidence_id="ev_001",
                    snippet="첫 번째 증거",
                    labels=["폭언", "불화"]
                ),
                DraftCitation(
                    evidence_id="ev_002",
                    snippet="두 번째 증거",
                    labels=["부정행위"]
                )
            ],
            generated_at=datetime.now(timezone.utc)
        )

        # Act
        try:
            result = draft_service._generate_pdf(sample_case, draft_response)

            # Assert
            file_buffer, filename, content_type = result
            assert content_type == "application/pdf"
            # PDF should be generated without errors
            assert file_buffer.tell() == 0  # Buffer should be at start
            content = file_buffer.read()
            assert len(content) > 0
        except ValidationError as e:
            # reportlab not installed - this is acceptable
            assert "reportlab" in str(e)

    def test_generate_pdf_escapes_special_characters(self, draft_service, sample_case):
        """Test PDF generation handles XML special characters"""
        # Arrange
        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="특수문자 테스트: <tag> & \"quote\" > less",
            citations=[
                DraftCitation(
                    evidence_id="ev_001",
                    snippet="<script>alert('xss')</script>",
                    labels=[]
                )
            ],
            generated_at=datetime.now(timezone.utc)
        )

        # Act - should not raise XML parsing errors
        try:
            result = draft_service._generate_pdf(sample_case, draft_response)
            assert result[1].endswith(".pdf")
        except ValidationError as e:
            # reportlab not installed - this is acceptable
            assert "reportlab" in str(e)

    def test_generate_pdf_without_citations(self, draft_service, sample_case):
        """Test PDF generation without citations"""
        # Arrange
        draft_response = DraftPreviewResponse(
            case_id="case_123abc",
            draft_text="초안 내용만 있는 문서",
            citations=[],
            generated_at=datetime.now(timezone.utc)
        )

        # Act
        try:
            result = draft_service._generate_pdf(sample_case, draft_response)
            assert result[1].endswith(".pdf")
        except ValidationError as e:
            # reportlab not installed - this is acceptable
            assert "reportlab" in str(e)

    def test_register_korean_font_returns_bool(self, draft_service):
        """Test _register_korean_font returns boolean"""
        # This test verifies the method signature and return type
        # Actual font registration depends on system fonts
        from unittest.mock import MagicMock

        mock_pdfmetrics = MagicMock()
        mock_ttfont = MagicMock()

        result = draft_service._register_korean_font(mock_pdfmetrics, mock_ttfont)

        assert isinstance(result, bool)
