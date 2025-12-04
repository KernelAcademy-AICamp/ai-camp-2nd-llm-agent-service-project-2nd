# Research: Draft Document Export

**Feature**: 001-draft-export
**Date**: 2025-12-03
**Status**: Complete

## Research Summary

This document captures technology decisions and best practices research for implementing document export functionality.

---

## 1. Word (.docx) Generation Library

### Decision: python-docx

**Rationale**:
- Industry standard Python library for Word document generation
- Native UTF-8 support for Korean text
- Excellent margin/page size control
- BSD license (free for commercial use)
- Active maintenance and large community

**Alternatives Considered**:

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| python-docx | Mature, well-documented, BSD license | Page numbers require XML workaround | **SELECTED** |
| docxtpl | Template-based (Jinja2), simpler syntax | Less control over formatting | Rejected - need fine control |
| python-docx-template | Jinja2 templates with python-docx | Additional dependency | Consider for future enhancement |

**Key Implementation Patterns**:

```python
from docx import Document
from docx.shared import Mm, Pt

# A4 with Korean court margins
section = document.sections[0]
section.page_width = Mm(210)
section.page_height = Mm(297)
section.top_margin = Mm(25)
section.bottom_margin = Mm(25)
section.left_margin = Mm(20)
section.right_margin = Mm(20)

# Korean font via styles
style = document.styles['Normal']
style.font.name = 'Batang'  # or 'Malgun Gothic'
style.font.size = Pt(12)
```

**Performance Considerations**:
- Text-only documents (100 pages): < 1 second
- Documents with tables: Pre-allocate table size to avoid O(n²) performance
- Recommendation: Use template document for headers/footers with page numbers

---

## 2. PDF Generation Library

### Decision: WeasyPrint

**Rationale**:
- HTML/CSS-based templates (easy to maintain by frontend team)
- Excellent CSS Paged Media support (headers, footers, page numbers)
- Native Korean font support via @font-face
- BSD license (free for commercial use)
- Aligns with project's existing HTML expertise

**Alternatives Considered**:

| Library | Pros | Cons | Decision |
|---------|------|------|----------|
| WeasyPrint | HTML/CSS templates, excellent Korean support | Slower than ReportLab for large docs | **SELECTED** |
| ReportLab | Fast, precise control, PDF/A support | Complex code-based layouts, steep learning curve | Rejected - maintenance burden |
| xhtml2pdf | Simple HTML to PDF | Poor CJK support, mojibake issues | Rejected - Korean rendering problems |
| pdfkit/wkhtmltopdf | External binary, full browser rendering | Headless browser overhead, deployment complexity | Rejected - infrastructure overhead |

**Key Implementation Patterns**:

```python
from weasyprint import HTML, CSS

css = """
@page {
    size: A4 portrait;
    margin: 25mm 20mm;

    @top-center {
        content: "사건번호: " attr(data-case-number);
        font-size: 9pt;
    }

    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
    }
}

@font-face {
    font-family: 'Batang';
    src: url('/fonts/batang.ttf');
}

body {
    font-family: 'Batang', serif;
    font-size: 12pt;
    line-height: 1.6;
}
"""

pdf_bytes = HTML(string=html_content).write_pdf(
    stylesheets=[CSS(string=css)]
)
```

**Performance Considerations**:
- CJK fonts add ~6x overhead to PDF generation
- 50-page document: ~10-15 seconds with Korean fonts
- 100+ page document: ~30-60 seconds
- Recommendation: Cache font configuration, use async generation with progress indicator

---

## 3. Korean Font Selection

### Decision: Batang (primary), Malgun Gothic (fallback)

**Rationale**:
- Batang is the standard serif font for Korean legal documents
- Court filings traditionally use serif fonts for body text
- Malgun Gothic is a modern sans-serif for headers/UI elements

**Font Deployment Strategy**:
- Bundle fonts in backend `/fonts/` directory
- Use Noto Serif CJK KR as open-source alternative
- Register fonts at application startup

**Alternatives Considered**:

| Font | Type | Use Case | Notes |
|------|------|----------|-------|
| Batang | Serif | Body text, legal documents | Korean court standard |
| Malgun Gothic | Sans-serif | Headers, UI | Windows default, clean |
| Noto Serif CJK KR | Serif | Open-source alternative | Google/Adobe, free |
| Noto Sans CJK KR | Sans-serif | Modern documents | Free, good rendering |

---

## 4. Document Template Architecture

### Decision: Jinja2 HTML templates with CSS for PDF, python-docx templates for Word

**Rationale**:
- Separation of content (HTML/template) from styling (CSS)
- Frontend team can maintain PDF templates
- Reusable components for evidence sections
- Different templates per document type (complaint, motion, brief)

**Template Structure**:
```
backend/
├── app/
│   └── templates/
│       ├── docx/
│       │   └── legal_draft_template.docx  # Base template with styles
│       └── pdf/
│           ├── base.html                  # Base HTML structure
│           ├── legal_draft.html           # Main draft template
│           ├── evidence_section.html      # Reusable evidence block
│           └── styles/
│               └── legal_document.css     # Page styles, fonts
└── fonts/
    ├── Batang.ttf
    └── NotoSerifCJKkr-Regular.otf
```

---

## 5. Export Job Processing

### Decision: Synchronous for small documents, Background job for large (>30 pages)

**Rationale**:
- Most drafts are 10-30 pages (complete in <10 seconds)
- Large documents (100+ pages) should not block UI
- Progress indicator for exports >3 seconds

**Implementation Pattern**:
```python
async def export_draft(case_id: str, format: str) -> ExportJob:
    draft = await get_draft(case_id)
    page_estimate = estimate_pages(draft.content)

    if page_estimate <= 30:
        # Synchronous export
        file_bytes = generate_document(draft, format)
        return create_download_response(file_bytes)
    else:
        # Background job with polling
        job = await create_export_job(case_id, format)
        background_tasks.add_task(generate_document_async, job.id)
        return job  # Client polls for completion
```

---

## 6. Frontend Preview Editor

### Decision: React-based rich text editor with controlled formatting

**Rationale**:
- WYSIWYG editing for lawyer review
- Restrict formatting options to maintain legal document standards
- Save edits before export

**Options Evaluated**:

| Editor | Pros | Cons | Decision |
|--------|------|------|----------|
| TipTap | Modern, extensible, good React support | Learning curve | **Consider** |
| Slate.js | Highly customizable | Complex for simple needs | Rejected |
| Draft.js | Facebook-backed | Maintenance slowing | Rejected |
| Lexical | Meta's new editor, performant | Newer, less ecosystem | Future consideration |
| Plain textarea | Simple | No rich formatting | Rejected - need basic formatting |

**Recommendation**: TipTap or Lexical for rich text editing with restricted toolbar (bold, italic, headings only).

---

## 7. File Storage Strategy

### Decision: Generate on-demand, store temporarily in S3

**Rationale**:
- Avoid storing duplicate data (drafts already in DynamoDB)
- S3 presigned URLs for secure downloads
- Clean up after 24 hours

**Implementation**:
```python
# Generate PDF
pdf_bytes = generate_pdf(draft_content)

# Upload to S3 with expiration metadata
s3_key = f"exports/{case_id}/{export_job_id}.pdf"
await s3_client.put_object(
    Bucket=EXPORTS_BUCKET,
    Key=s3_key,
    Body=pdf_bytes,
    Metadata={"expires": (datetime.now() + timedelta(hours=24)).isoformat()}
)

# Return presigned URL (valid 1 hour)
download_url = s3_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': EXPORTS_BUCKET, 'Key': s3_key},
    ExpiresIn=3600
)
```

---

## 8. Audit Logging

### Decision: Log all export actions to existing audit_logs table

**Rationale**:
- Constitution Principle I requires all CRUD operations logged
- Export is a sensitive action (accessing case data)
- Compliance with legal document handling requirements

**Log Fields**:
- `user_id`: Who initiated export
- `case_id`: Which case
- `action`: "EXPORT_DRAFT"
- `details`: `{"format": "pdf", "page_count": 25, "file_size": 1234567}`
- `timestamp`: When exported
- `ip_address`: From where

---

## Dependencies to Add

### Backend (requirements.txt)

```
python-docx>=0.8.11       # Word document generation
weasyprint>=60.0          # PDF generation
Jinja2>=3.1.2             # Already in FastAPI, but ensure version
```

### System Dependencies (for WeasyPrint)

```dockerfile
# Dockerfile additions
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-cjk
```

### Frontend (package.json)

```json
{
  "dependencies": {
    "@tiptap/react": "^2.1.0",
    "@tiptap/starter-kit": "^2.1.0"
  }
}
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| WeasyPrint slow for large docs | Async generation with progress indicator |
| Korean font rendering issues | Bundle fonts, test thoroughly, have fallback fonts |
| Memory issues with 500-page docs | Stream generation, set memory limits |
| Export failure mid-process | Retry mechanism, preserve draft state |
| S3 storage costs | Auto-cleanup after 24 hours |

---

## Next Steps

1. Install dependencies (python-docx, weasyprint)
2. Create document templates (HTML/CSS for PDF, .docx for Word)
3. Implement export service with Clean Architecture pattern
4. Add export API endpoints
5. Build frontend preview/export UI
6. Integration testing with Korean content
7. Performance testing with 100-page documents
