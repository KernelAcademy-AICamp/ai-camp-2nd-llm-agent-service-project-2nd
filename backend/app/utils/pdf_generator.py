"""
PdfGenerator - Korean Legal Document PDF Generation Utility

Generates PDF documents using WeasyPrint with HTML/CSS templates:
- A4 paper size (210mm x 297mm)
- Korean court margins (25mm top/bottom, 20mm left/right)
- Noto Serif CJK KR font support
- Page headers and footers with page numbers
- Proper section structure for legal documents
"""

from io import BytesIO
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import os

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class PdfGeneratorError(Exception):
    """Custom exception for PDF generation errors"""
    pass


class PdfGenerator:
    """
    Generator for Korean legal documents in PDF format using WeasyPrint.

    Uses HTML/CSS templates for flexible formatting with proper Korean font support.

    Features:
    - A4 paper with Korean court standard margins
    - Noto Serif CJK KR font (with Batang fallback)
    - Running headers and footers
    - Page numbers in format "1 / 15"
    - Jinja2 templating for dynamic content
    """

    # Template directory
    TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "pdf"
    STYLES_DIR = TEMPLATE_DIR / "styles"
    FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

    # Document type titles in Korean
    DOCUMENT_TYPES = {
        "complaint": "소 장",
        "motion": "신 청 서",
        "brief": "준 비 서 면",
        "response": "답 변 서",
    }

    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise PdfGeneratorError(
                "WeasyPrint is not installed. "
                "Please install it with: pip install weasyprint"
            )
        if not JINJA2_AVAILABLE:
            raise PdfGeneratorError(
                "Jinja2 is not installed. "
                "Please install it with: pip install Jinja2"
            )

        # Configure Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.TEMPLATE_DIR)),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Configure font settings
        self.font_config = FontConfiguration()

    def generate_document(
        self,
        content: Dict[str, Any],
        document_type: str = "brief",
        template_name: str = "legal_draft.html"
    ) -> bytes:
        """
        Generate a PDF document from structured content.

        Args:
            content: Dictionary with structure:
                {
                    "header": {
                        "court_name": "서울가정법원",
                        "case_number": "2025드단12345",
                        "parties": {
                            "plaintiff": "원고 김○○",
                            "defendant": "피고 이○○"
                        }
                    },
                    "sections": [
                        {"title": "청구취지", "content": "...", "order": 1},
                        {"title": "청구원인", "content": "...", "order": 2}
                    ],
                    "citations": [
                        {"reference": "[증 제1호증]", "description": "..."}
                    ],
                    "footer": {
                        "date": "2025년 12월 3일",
                        "attorney": "변호사 박○○"
                    }
                }
            document_type: One of "complaint", "motion", "brief", "response"
            template_name: HTML template filename

        Returns:
            bytes: PDF file content
        """
        # Prepare template context
        context = self._prepare_context(content, document_type)

        # Render HTML template
        html_content = self._render_template(template_name, context)

        # Load CSS styles
        css_content = self._load_styles()

        # Generate PDF
        return self._generate_pdf(html_content, css_content)

    def generate_from_draft_text(
        self,
        draft_text: str,
        case_title: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        generated_at: Optional[datetime] = None
    ) -> bytes:
        """
        Generate PDF from plain draft text (backward compatibility).

        Args:
            draft_text: Plain text draft content
            case_title: Case title for header
            citations: List of citation dictionaries
            generated_at: Generation timestamp

        Returns:
            bytes: PDF file content
        """
        # Build content structure from plain text
        content = self._build_content_from_text(
            draft_text, case_title, citations, generated_at
        )

        # Use simple template for plain text
        html_content = self._render_simple_template(content)
        css_content = self._load_styles()

        return self._generate_pdf(html_content, css_content)

    def _prepare_context(
        self,
        content: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """Prepare Jinja2 template context."""
        header = content.get("header", {})
        footer = content.get("footer", {})
        sections = sorted(
            content.get("sections", []),
            key=lambda s: s.get("order", 0)
        )

        return {
            "document_title": self._get_document_title(header, document_type),
            "document_type_korean": self.DOCUMENT_TYPES.get(document_type, "준 비 서 면"),
            "header": header,
            "sections": sections,
            "citations": content.get("citations", []),
            "footer": footer,
            "generated_at": datetime.now().isoformat(),
        }

    def _get_document_title(
        self,
        header: Dict[str, Any],
        document_type: str
    ) -> str:
        """Generate document title for browser tab/metadata."""
        case_number = header.get("case_number", "")
        doc_type = self.DOCUMENT_TYPES.get(document_type, "문서")
        return f"{case_number} - {doc_type}" if case_number else doc_type

    def _render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render Jinja2 HTML template."""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            # Fallback to simple template if main template fails
            return self._render_simple_template(context)

    def _render_simple_template(self, content: Dict[str, Any]) -> str:
        """Render a simple HTML template for plain text content."""
        sections_html = ""
        for section in content.get("sections", []):
            title = section.get("title", "")
            section_content = section.get("content", "")
            # Convert newlines to <br> and paragraphs
            paragraphs = section_content.replace("\n\n", "</p><p>").replace("\n", "<br>")
            sections_html += f"<h2>{title}</h2><p>{paragraphs}</p>"

        citations_html = ""
        for citation in content.get("citations", []):
            ref = citation.get("reference", "")
            desc = citation.get("description", "")
            citations_html += f"<div class='evidence-item'>{ref}: {desc}</div>"

        header = content.get("header", {})
        footer = content.get("footer", {})
        parties = header.get("parties", {})

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{content.get('document_title', '법률 문서')}</title>
</head>
<body>
    <div class="case-header">
        <div class="court-name">{header.get('court_name', '')}</div>
        <div class="case-number">사건번호: {header.get('case_number', '')}</div>
        <div class="parties">
            <div class="party">원 고: {parties.get('plaintiff', '')}</div>
            <div class="party">피 고: {parties.get('defendant', '')}</div>
        </div>
    </div>

    <div class="document-type">{content.get('document_type_korean', '준 비 서 면')}</div>

    {sections_html}

    {"<section class='evidence-list'><h2>증거목록</h2>" + citations_html + "</section>" if citations_html else ""}

    <div class="signature-section">
        <div class="date">{footer.get('date', '')}</div>
        <div class="attorney">{footer.get('attorney', '')}</div>
        <div class="seal">(인)</div>
    </div>

    <div class="text-center" style="margin-top: 20mm;">
        <strong>{header.get('court_name', '')} 귀중</strong>
    </div>
</body>
</html>"""

    def _build_content_from_text(
        self,
        draft_text: str,
        case_title: str,
        citations: Optional[List[Dict[str, Any]]],
        generated_at: Optional[datetime]
    ) -> Dict[str, Any]:
        """Build structured content from plain text."""
        timestamp = generated_at or datetime.now()

        sections = [{
            "title": "본문",
            "content": draft_text,
            "order": 1
        }]

        citation_list = []
        if citations:
            for i, c in enumerate(citations, 1):
                citation_list.append({
                    "reference": f"[증거 {i}]",
                    "description": f"{c.get('snippet', '')} (분류: {', '.join(c.get('labels', []))})"
                })

        return {
            "document_title": f"초안 - {case_title}",
            "document_type_korean": "초 안",
            "header": {
                "court_name": "",
                "case_number": "",
                "parties": {}
            },
            "sections": sections,
            "citations": citation_list,
            "footer": {
                "date": timestamp.strftime("%Y년 %m월 %d일"),
                "attorney": ""
            },
            "generated_at": timestamp.isoformat()
        }

    def _load_styles(self) -> str:
        """Load CSS styles from file."""
        css_path = self.STYLES_DIR / "legal_document.css"
        if css_path.exists():
            return css_path.read_text(encoding='utf-8')

        # Fallback minimal CSS
        return self._get_fallback_css()

    def _get_fallback_css(self) -> str:
        """Return fallback CSS if template file not found."""
        return """
@page {
    size: A4 portrait;
    margin: 25mm 20mm;

    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
    }
}

body {
    font-family: 'Noto Serif CJK KR', 'Batang', serif;
    font-size: 12pt;
    line-height: 1.6;
}

h1 { font-size: 18pt; text-align: center; }
h2 { font-size: 14pt; margin-top: 15mm; }

.case-header { text-align: center; margin-bottom: 15mm; }
.court-name { font-size: 14pt; font-weight: bold; }
.document-type { font-size: 20pt; font-weight: bold; text-align: center; letter-spacing: 1em; margin: 20mm 0; }
.signature-section { margin-top: 30mm; text-align: right; }
.text-center { text-align: center; }
"""

    def _generate_pdf(self, html_content: str, css_content: str) -> bytes:
        """Generate PDF from HTML and CSS using WeasyPrint."""
        buffer = BytesIO()

        # Create HTML object
        html = HTML(string=html_content, base_url=str(self.TEMPLATE_DIR))

        # Create CSS object
        css = CSS(string=css_content, font_config=self.font_config)

        # Write PDF to buffer
        html.write_pdf(
            buffer,
            stylesheets=[css],
            font_config=self.font_config
        )

        buffer.seek(0)
        return buffer.getvalue()

    def get_page_count(self, pdf_bytes: bytes) -> int:
        """
        Get page count from PDF bytes.

        Note: This requires pypdf or similar library for accurate count.
        For now, returns an estimate based on content size.
        """
        # Simple estimate: ~3KB per page on average for text documents
        return max(1, len(pdf_bytes) // 3000)


def generate_pdf(
    content: Dict[str, Any],
    document_type: str = "brief"
) -> bytes:
    """
    Convenience function to generate PDF from content.

    Args:
        content: Structured content dictionary
        document_type: Document type ("complaint", "motion", "brief", "response")

    Returns:
        bytes: PDF file content
    """
    generator = PdfGenerator()
    return generator.generate_document(content, document_type)


def generate_pdf_from_text(
    draft_text: str,
    case_title: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    generated_at: Optional[datetime] = None
) -> bytes:
    """
    Convenience function to generate PDF from plain text.

    Args:
        draft_text: Plain text draft content
        case_title: Case title
        citations: Optional list of citations
        generated_at: Optional generation timestamp

    Returns:
        bytes: PDF file content
    """
    generator = PdfGenerator()
    return generator.generate_from_draft_text(
        draft_text, case_title, citations, generated_at
    )
