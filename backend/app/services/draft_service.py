"""
Draft Service - Business logic for draft generation with RAG
Orchestrates Qdrant RAG + OpenAI GPT-4o for draft preview
"""

from sqlalchemy.orm import Session
from typing import List, Tuple
from datetime import datetime, timezone
from io import BytesIO

from app.db.schemas import (
    DraftPreviewRequest,
    DraftPreviewResponse,
    DraftCitation,
    DraftExportFormat
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.dynamo import get_evidence_by_case
from app.utils.qdrant import search_evidence_by_semantic, search_legal_knowledge
from app.utils.openai_client import generate_chat_completion
from app.middleware import NotFoundError, PermissionError, ValidationError

# Optional: python-docx for DOCX generation
try:
    from docx import Document
    from docx.shared import Pt, Inches  # noqa: F401
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DraftService:
    """
    Service for draft generation with RAG
    """

    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)

    def generate_draft_preview(
        self,
        case_id: str,
        request: DraftPreviewRequest,
        user_id: str
    ) -> DraftPreviewResponse:
        """
        Generate draft preview using RAG + GPT-4o

        Process:
        1. Validate case access
        2. Retrieve evidence metadata from DynamoDB
        3. Perform semantic search in Qdrant (RAG)
        4. Build GPT-4o prompt with RAG context
        5. Generate draft text
        6. Extract citations

        Args:
            case_id: Case ID
            request: Draft generation request (sections, language, style)
            user_id: User ID requesting draft

        Returns:
            Draft preview with citations

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case
            ValidationError: No evidence in case
        """
        # 1. Validate case access
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # 2. Retrieve evidence metadata from DynamoDB
        evidence_list = get_evidence_by_case(case_id)

        # Check if there's any evidence
        if not evidence_list:
            raise ValidationError("사건에 증거가 하나도 없습니다. 증거를 업로드한 후 초안을 생성해 주세요.")

        # Filter for completed evidence only (status="done")
        # Note: Currently filtering for reference, may be used for future enhancements
        _ = [ev for ev in evidence_list if ev.get("status") == "done"]

        # 3. Perform semantic RAG search in Qdrant (evidence + legal)
        rag_results = self._perform_rag_search(case_id, request.sections)
        evidence_results = rag_results.get("evidence", [])
        legal_results = rag_results.get("legal", [])

        # 4. Build GPT-4o prompt with RAG context
        prompt_messages = self._build_draft_prompt(
            case=case,
            sections=request.sections,
            evidence_context=evidence_results,
            legal_context=legal_results,
            language=request.language,
            style=request.style
        )

        # 5. Generate draft text using GPT-4o
        draft_text = generate_chat_completion(
            messages=prompt_messages,
            temperature=0.3,  # Low temperature for consistent legal writing
            max_tokens=4000
        )

        # 6. Extract citations from RAG results
        citations = self._extract_citations(evidence_results)

        return DraftPreviewResponse(
            case_id=case_id,
            draft_text=draft_text,
            citations=citations,
            generated_at=datetime.now(timezone.utc)
        )

    def _perform_rag_search(self, case_id: str, sections: List[str]) -> dict:
        """
        Perform semantic search in Qdrant for RAG context

        Args:
            case_id: Case ID
            sections: Sections being generated

        Returns:
            Dict with 'evidence' and 'legal' results
        """
        # Build search query based on sections
        if "청구원인" in sections:
            # Search for fault evidence (guilt factors)
            query = "이혼 사유 귀책사유 폭언 불화 부정행위"
            evidence_results = search_evidence_by_semantic(
                case_id=case_id,
                query=query,
                top_k=10
            )
            # Search legal knowledge for divorce grounds
            legal_results = search_legal_knowledge(
                query="재판상 이혼 사유 민법 제840조",
                top_k=5,
                doc_type="statute"
            )
        else:
            # General search for all sections
            query = " ".join(sections)
            evidence_results = search_evidence_by_semantic(
                case_id=case_id,
                query=query,
                top_k=5
            )
            legal_results = search_legal_knowledge(
                query="이혼 " + query,
                top_k=3
            )

        return {
            "evidence": evidence_results,
            "legal": legal_results
        }

    def _build_draft_prompt(
        self,
        case: any,
        sections: List[str],
        evidence_context: List[dict],
        legal_context: List[dict],
        language: str,
        style: str
    ) -> List[dict]:
        """
        Build GPT-4o prompt with evidence and legal RAG context

        Args:
            case: Case object
            sections: Sections to generate
            evidence_context: Evidence RAG search results
            legal_context: Legal knowledge RAG search results
            language: Language (ko/en)
            style: Writing style

        Returns:
            List of messages for GPT-4o
        """
        # System message - define role and constraints
        system_message = {
            "role": "system",
            "content": """당신은 대한민국의 전문 법률가입니다.
이혼 소송 소장(訴狀) 초안을 작성하는 AI 어시스턴트입니다.

**중요 원칙:**
1. 제공된 증거와 법률 조문을 기반으로 작성하세요
2. 추측이나 가정을 하지 마세요
3. 법률 용어를 정확하게 사용하세요
4. 제공된 법률 조문(민법 제840조 등)을 정확히 인용하세요
5. 존중하고 전문적인 어조를 유지하세요

**소장 작성 형식:**
1. 소장 제목
2. 당사자 정보 (원고/피고)
3. 청구 취지
4. 청구 원인
   - 당사자들의 관계
   - 혼인생활 과정
   - 이혼 사유 발생 (민법 제840조 근거)
   - 위자료/재산분할/양육권 청구 근거
5. 입증 방법
6. 첨부 서류

**주의사항:**
본 문서는 AI가 생성한 초안이며, 변호사의 검토 및 수정이 필수입니다.
"""
        }

        # Build context strings
        evidence_context_str = self._format_evidence_context(evidence_context)
        legal_context_str = self._format_legal_context(legal_context)

        # User message - include case info, evidence, and legal context
        user_message = {
            "role": "user",
            "content": f"""
다음 정보를 바탕으로 이혼 소송 소장 초안을 작성해 주세요.

**사건 정보:**
- 사건명: {case.title}
- 사건 설명: {case.description or "N/A"}

**생성할 섹션:**
{", ".join(sections)}

**관련 법률 조문:**
{legal_context_str}

**증거 자료:**
{evidence_context_str}

**요청사항:**
- 언어: {language}
- 스타일: {style}
- 위 법률 조문과 증거를 기반으로 법률적 논리를 구성해 주세요
- 이혼 사유는 반드시 민법 제840조를 인용하여 작성하세요
- 각 주장에 대해 증거 번호를 명시해 주세요 (예: [갑 제1호증], [갑 제2호증])

소장 초안을 작성해 주세요.
"""
        }

        return [system_message, user_message]

    def _format_legal_context(self, legal_results: List[dict]) -> str:
        """
        Format legal knowledge search results for GPT-4o prompt

        Args:
            legal_results: List of legal documents from RAG search

        Returns:
            Formatted legal context string
        """
        if not legal_results:
            return "(관련 법률 조문 없음)"

        context_parts = []
        for doc in legal_results:
            article_number = doc.get("article_number", "")
            statute_name = doc.get("statute_name", "민법")
            content = doc.get("text", "")

            if article_number and content:
                context_parts.append(f"""
【{statute_name} {article_number}】
{content}
""")

        return "\n".join(context_parts) if context_parts else "(관련 법률 조문 없음)"

    def _format_evidence_context(self, evidence_results: List[dict]) -> str:
        """
        Format evidence search results for GPT-4o prompt

        Args:
            evidence_results: List of evidence documents from RAG search

        Returns:
            Formatted evidence context string
        """
        if not evidence_results:
            return "(증거 자료 없음 - 기본 템플릿으로 작성)"

        context_parts = []
        for i, doc in enumerate(evidence_results, start=1):
            evidence_id = doc.get("id", f"evidence_{i}")
            content = doc.get("content", "")
            labels = doc.get("labels", [])
            speaker = doc.get("speaker", "")
            timestamp = doc.get("timestamp", "")

            # Truncate content if too long
            if len(content) > 500:
                content = content[:500] + "..."

            context_parts.append(f"""
[갑 제{i}호증] (ID: {evidence_id})
- 분류: {", ".join(labels) if labels else "N/A"}
- 화자: {speaker or "N/A"}
- 시점: {timestamp or "N/A"}
- 내용: {content}
""")

        return "\n".join(context_parts)

    def _format_rag_context(self, rag_results: List[dict]) -> str:
        """
        Format RAG search results for GPT-4o prompt

        Args:
            rag_results: List of evidence documents from RAG search

        Returns:
            Formatted context string
        """
        if not rag_results:
            return "(증거 자료 없음 - 기본 템플릿으로 작성)"

        context_parts = []
        for i, doc in enumerate(rag_results, start=1):
            evidence_id = doc.get("id", f"evidence_{i}")
            content = doc.get("content", "")
            labels = doc.get("labels", [])
            speaker = doc.get("speaker", "")
            timestamp = doc.get("timestamp", "")

            # Truncate content if too long
            if len(content) > 500:
                content = content[:500] + "..."

            context_parts.append(f"""
[증거 {i}] (ID: {evidence_id})
- 분류: {", ".join(labels) if labels else "N/A"}
- 화자: {speaker or "N/A"}
- 시점: {timestamp or "N/A"}
- 내용: {content}
""")

        return "\n".join(context_parts)

    def _extract_citations(self, rag_results: List[dict]) -> List[DraftCitation]:
        """
        Extract citations from RAG results

        Args:
            rag_results: List of evidence documents from RAG search

        Returns:
            List of DraftCitation objects
        """
        citations = []

        for doc in rag_results:
            evidence_id = doc.get("id")
            content = doc.get("content", "")
            labels = doc.get("labels", [])

            # Create snippet (first 200 chars)
            snippet = content[:200] + "..." if len(content) > 200 else content

            citations.append(
                DraftCitation(
                    evidence_id=evidence_id,
                    snippet=snippet,
                    labels=labels
                )
            )

        return citations

    def export_draft(
        self,
        case_id: str,
        user_id: str,
        export_format: DraftExportFormat = DraftExportFormat.DOCX
    ) -> Tuple[BytesIO, str, str]:
        """
        Export draft as DOCX or PDF file

        Process:
        1. Validate case access
        2. Generate draft preview using RAG + GPT-4o
        3. Convert to requested format (DOCX or PDF)

        Args:
            case_id: Case ID
            user_id: User ID requesting export
            export_format: Output format (docx or pdf)

        Returns:
            Tuple of (file_bytes, filename, content_type)

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access to case
            ValidationError: Export format not supported or missing dependencies
        """
        # 1. Validate case access
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # 2. Generate draft preview
        request = DraftPreviewRequest()  # Use default sections
        draft_response = self.generate_draft_preview(case_id, request, user_id)

        # 3. Convert to requested format
        if export_format == DraftExportFormat.DOCX:
            return self._generate_docx(case, draft_response)
        elif export_format == DraftExportFormat.PDF:
            return self._generate_pdf(case, draft_response)
        else:
            raise ValidationError(f"Unsupported export format: {export_format}")

    def _generate_docx(
        self,
        case,
        draft_response: DraftPreviewResponse
    ) -> Tuple[BytesIO, str, str]:
        """
        Generate DOCX file from draft response

        Args:
            case: Case object
            draft_response: Generated draft preview

        Returns:
            Tuple of (file_bytes, filename, content_type)
        """
        if not DOCX_AVAILABLE:
            raise ValidationError(
                "DOCX export is not available. "
                "Please install python-docx: pip install python-docx"
            )

        # Create document
        doc = Document()

        # Title
        title = doc.add_heading("이혼 소송 준비서면 (초안)", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Case info
        doc.add_paragraph()
        case_info = doc.add_paragraph()
        case_info.add_run(f"사건명: {case.title}").bold = True
        doc.add_paragraph(f"생성일시: {draft_response.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Draft content
        doc.add_heading("본문", level=1)
        for paragraph_text in draft_response.draft_text.split("\n\n"):
            if paragraph_text.strip():
                doc.add_paragraph(paragraph_text.strip())

        # Citations
        if draft_response.citations:
            doc.add_heading("인용 증거", level=1)
            for i, citation in enumerate(draft_response.citations, 1):
                p = doc.add_paragraph()
                p.add_run(f"[증거 {i}] ").bold = True
                p.add_run(f"(ID: {citation.evidence_id})")
                doc.add_paragraph(f"  - 분류: {', '.join(citation.labels) if citation.labels else 'N/A'}")
                doc.add_paragraph(f"  - 내용: {citation.snippet}")

        # Disclaimer
        doc.add_paragraph()
        disclaimer = doc.add_paragraph()
        disclaimer.add_run(
            "⚠️ 본 문서는 AI가 생성한 초안이며, "
            "변호사의 검토 및 수정이 필수입니다."
        ).italic = True

        # Save to BytesIO
        file_buffer = BytesIO()
        doc.save(file_buffer)
        file_buffer.seek(0)

        # Generate filename
        safe_title = case.title.replace(" ", "_")[:30]
        filename = f"draft_{safe_title}_{draft_response.generated_at.strftime('%Y%m%d')}.docx"
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        return file_buffer, filename, content_type

    def _generate_pdf(
        self,
        case,
        draft_response: DraftPreviewResponse
    ) -> Tuple[BytesIO, str, str]:
        """
        Generate PDF file from draft response

        Note: For simplicity, we generate a basic text-based PDF.
        For production, consider using reportlab or weasyprint.

        Args:
            case: Case object
            draft_response: Generated draft preview

        Returns:
            Tuple of (file_bytes, filename, content_type)
        """
        # For now, create a simple text file as PDF placeholder
        # In production, use reportlab or weasyprint for proper PDF generation
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            from reportlab.pdfbase.ttfonts import TTFont  # noqa: F401

            file_buffer = BytesIO()
            doc = SimpleDocTemplate(file_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # Title
            story.append(Paragraph("이혼 소송 준비서면 (초안)", styles['Title']))
            story.append(Spacer(1, 0.5 * inch))

            # Case info
            story.append(Paragraph(f"<b>사건명:</b> {case.title}", styles['Normal']))
            story.append(Paragraph(
                f"<b>생성일시:</b> {draft_response.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 0.3 * inch))

            # Draft content
            story.append(Paragraph("<b>본문</b>", styles['Heading2']))
            for paragraph_text in draft_response.draft_text.split("\n\n"):
                if paragraph_text.strip():
                    story.append(Paragraph(paragraph_text.strip(), styles['Normal']))
                    story.append(Spacer(1, 0.1 * inch))

            # Build PDF
            doc.build(story)
            file_buffer.seek(0)

            safe_title = case.title.replace(" ", "_")[:30]
            filename = f"draft_{safe_title}_{draft_response.generated_at.strftime('%Y%m%d')}.pdf"
            content_type = "application/pdf"

            return file_buffer, filename, content_type

        except ImportError:
            # Fallback: Return DOCX instead with a warning
            raise ValidationError(
                "PDF export is not available. "
                "Please install reportlab: pip install reportlab. "
                "Alternatively, use DOCX format."
            )
