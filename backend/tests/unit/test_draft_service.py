"""
Unit tests for Draft Service
TDD - Improving test coverage for draft_service.py
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.draft_service import DraftService
from app.db.schemas import DraftPreviewRequest, DraftExportFormat
from app.middleware.error_handler import ValidationError, NotFoundError, PermissionError


class TestFormatEvidenceContext:
    """Unit tests for _format_evidence_context method"""

    def test_format_evidence_context_empty(self):
        """Returns placeholder for empty results"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_evidence_context([])

            assert "(증거 자료 없음" in result

    def test_format_evidence_context_with_data(self):
        """Formats evidence data correctly"""
        mock_db = MagicMock()
        evidence = [
            {
                "chunk_id": "ev-123",
                "document": "피고는 폭언을 하였습니다.",
                "legal_categories": ["폭언", "유책사유"],
                "sender": "원고",
                "timestamp": "2024-01-15"
            }
        ]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_evidence_context(evidence)

            assert "[갑 제1호증]" in result
            assert "ev-123" in result
            assert "폭언" in result
            assert "원고" in result

    def test_format_evidence_context_truncates_long_content(self):
        """Truncates content longer than 500 chars"""
        mock_db = MagicMock()
        long_content = "A" * 600
        evidence = [{"document": long_content}]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_evidence_context(evidence)

            assert "..." in result
            assert "A" * 500 in result


class TestFormatLegalContext:
    """Unit tests for _format_legal_context method"""

    def test_format_legal_context_empty(self):
        """Returns placeholder for empty results"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_legal_context([])

            assert "(관련 법률 조문 없음)" in result

    def test_format_legal_context_with_data(self):
        """Formats legal documents correctly"""
        mock_db = MagicMock()
        legal_docs = [
            {
                "article_number": "제840조",
                "statute_name": "민법",
                "document": "재판상 이혼 사유..."
            }
        ]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_legal_context(legal_docs)

            assert "민법" in result
            assert "제840조" in result
            assert "재판상 이혼" in result


class TestFormatRagContext:
    """Unit tests for _format_rag_context method"""

    def test_format_rag_context_empty(self):
        """Returns placeholder for empty results"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_rag_context([])

            assert "(증거 자료 없음" in result

    def test_format_rag_context_with_data(self):
        """Formats RAG results correctly"""
        mock_db = MagicMock()
        rag_results = [
            {
                "id": "ev-456",
                "content": "증거 내용입니다.",
                "labels": ["불륜"],
                "speaker": "피고",
                "timestamp": "2024-02-20"
            }
        ]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_rag_context(rag_results)

            assert "[증거 1]" in result
            assert "ev-456" in result
            assert "불륜" in result

    def test_format_rag_context_truncates_long_content(self):
        """Truncates content longer than 500 chars"""
        mock_db = MagicMock()
        long_content = "B" * 600
        rag_results = [{"content": long_content}]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._format_rag_context(rag_results)

            assert "..." in result


class TestExtractCitations:
    """Unit tests for _extract_citations method"""

    def test_extract_citations_empty(self):
        """Returns empty list for empty results"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._extract_citations([])

            assert result == []

    def test_extract_citations_with_data(self):
        """Extracts citations from RAG results"""
        mock_db = MagicMock()
        rag_results = [
            {
                "evidence_id": "ev-789",
                "content": "증거 내용",
                "labels": ["폭언"]
            }
        ]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._extract_citations(rag_results)

            assert len(result) == 1
            assert result[0].evidence_id == "ev-789"
            assert result[0].labels == ["폭언"]

    def test_extract_citations_truncates_snippet(self):
        """Truncates snippet longer than 200 chars"""
        mock_db = MagicMock()
        long_content = "C" * 300
        rag_results = [{"content": long_content, "id": "ev-1"}]

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._extract_citations(rag_results)

            assert "..." in result[0].snippet
            assert len(result[0].snippet) == 203  # 200 + "..."


class TestGenerateDraftPreview:
    """Unit tests for generate_draft_preview method"""

    def test_generate_draft_preview_case_not_found(self):
        """Raises NotFoundError when case not found"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.generate_draft_preview(
                    "nonexistent",
                    DraftPreviewRequest(),
                    "user-123"
                )

    def test_generate_draft_preview_no_access(self):
        """Raises PermissionError when user has no access"""
        mock_db = MagicMock()
        mock_case = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.member_repo.has_access.return_value = False

            with pytest.raises(PermissionError):
                service.generate_draft_preview(
                    "case-123",
                    DraftPreviewRequest(),
                    "user-123"
                )

    @patch('app.services.draft_service.get_evidence_by_case')
    def test_generate_draft_preview_no_evidence(self, mock_get_evidence):
        """Raises ValidationError when no evidence in case"""
        mock_db = MagicMock()
        mock_case = MagicMock()
        mock_get_evidence.return_value = []

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.member_repo.has_access.return_value = True

            with pytest.raises(ValidationError, match="증거가 하나도 없습니다"):
                service.generate_draft_preview(
                    "case-123",
                    DraftPreviewRequest(),
                    "user-123"
                )

    @patch('app.services.draft_service.generate_chat_completion')
    @patch('app.services.draft_service.search_legal_knowledge')
    @patch('app.services.draft_service.search_evidence_by_semantic')
    @patch('app.services.draft_service.get_evidence_by_case')
    def test_generate_draft_preview_success(
        self,
        mock_get_evidence,
        mock_search_evidence,
        mock_search_legal,
        mock_generate
    ):
        """Successfully generates draft preview"""
        mock_db = MagicMock()
        mock_case = MagicMock()
        mock_case.title = "이혼 사건"
        mock_case.description = "테스트 사건"

        mock_get_evidence.return_value = [{"status": "done", "id": "ev-1"}]
        mock_search_evidence.return_value = [{"id": "ev-1", "content": "증거"}]
        mock_search_legal.return_value = []
        mock_generate.return_value = "이혼 소장 초안 내용"

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.member_repo.has_access.return_value = True

            result = service.generate_draft_preview(
                "case-123",
                DraftPreviewRequest(sections=["청구취지"]),
                "user-123"
            )

            assert result.case_id == "case-123"
            assert result.draft_text == "이혼 소장 초안 내용"


class TestPerformRagSearch:
    """Unit tests for _perform_rag_search method"""

    @patch('app.services.draft_service.search_legal_knowledge')
    @patch('app.services.draft_service.search_evidence_by_semantic')
    def test_perform_rag_search_with_청구원인(self, mock_search_ev, mock_search_legal):
        """Uses fault evidence query for 청구원인 section"""
        mock_db = MagicMock()
        mock_search_ev.return_value = []
        mock_search_legal.return_value = []

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._perform_rag_search("case-123", ["청구원인"])

            # Should search with fault-related keywords
            mock_search_ev.assert_called_once()
            call_args = mock_search_ev.call_args
            assert "귀책사유" in call_args.kwargs["query"]

    @patch('app.services.draft_service.search_legal_knowledge')
    @patch('app.services.draft_service.search_evidence_by_semantic')
    def test_perform_rag_search_general(self, mock_search_ev, mock_search_legal):
        """Uses section-based query for other sections"""
        mock_db = MagicMock()
        mock_search_ev.return_value = []
        mock_search_legal.return_value = []

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._perform_rag_search("case-123", ["당사자", "청구취지"])

            assert "evidence" in result
            assert "legal" in result


class TestExportDraft:
    """Unit tests for export_draft method"""

    def test_export_draft_case_not_found(self):
        """Raises NotFoundError when case not found"""
        mock_db = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = None

            with pytest.raises(NotFoundError):
                service.export_draft("nonexistent", "user-123")

    def test_export_draft_no_access(self):
        """Raises PermissionError when user has no access"""
        mock_db = MagicMock()
        mock_case = MagicMock()

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)
            service.db = mock_db
            service.case_repo = MagicMock()
            service.member_repo = MagicMock()

            service.case_repo.get_by_id.return_value = mock_case
            service.member_repo.has_access.return_value = False

            with pytest.raises(PermissionError):
                service.export_draft("case-123", "user-123")


class TestBuildDraftPrompt:
    """Unit tests for _build_draft_prompt method"""

    def test_build_draft_prompt_structure(self):
        """Builds correct prompt structure"""
        mock_db = MagicMock()
        mock_case = MagicMock()
        mock_case.title = "테스트 사건"
        mock_case.description = "사건 설명"

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._build_draft_prompt(
                case=mock_case,
                sections=["청구원인"],
                evidence_context=[],
                legal_context=[],
                language="ko",
                style="formal"
            )

            assert len(result) == 2
            assert result[0]["role"] == "system"
            assert result[1]["role"] == "user"

    def test_build_draft_prompt_includes_case_info(self):
        """Includes case information in prompt"""
        mock_db = MagicMock()
        mock_case = MagicMock()
        mock_case.title = "이혼 소송 사건"
        mock_case.description = "상세 설명"

        with patch.object(DraftService, '__init__', lambda x, y: None):
            service = DraftService(mock_db)

            result = service._build_draft_prompt(
                case=mock_case,
                sections=["청구취지"],
                evidence_context=[],
                legal_context=[],
                language="ko",
                style="formal"
            )

            user_content = result[1]["content"]
            assert "이혼 소송 사건" in user_content
            assert "상세 설명" in user_content
