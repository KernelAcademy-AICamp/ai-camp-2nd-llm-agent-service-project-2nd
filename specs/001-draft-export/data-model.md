# Data Model: Draft Document Export

**Feature**: 001-draft-export
**Date**: 2025-12-03

## Entities

### 1. DraftDocument

Represents an AI-generated legal document draft linked to a case.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | Unique identifier |
| case_id | UUID | Foreign Key → cases.id, NOT NULL | Parent case |
| title | String | NOT NULL, max 255 chars | Document title (e.g., "이혼소송 준비서면") |
| document_type | Enum | NOT NULL | Type: COMPLAINT, MOTION, BRIEF, RESPONSE |
| content | JSON | NOT NULL | Structured content with sections |
| version | Integer | NOT NULL, default 1 | Version number for edits |
| status | Enum | NOT NULL | DRAFT, REVIEWED, EXPORTED |
| created_by | UUID | Foreign Key → users.id | User who generated draft |
| created_at | DateTime | NOT NULL | Creation timestamp |
| updated_at | DateTime | NOT NULL | Last modification |

**Content JSON Structure**:
```json
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
    {
      "title": "청구취지",
      "content": "1. 원고와 피고는 이혼한다...",
      "order": 1
    },
    {
      "title": "청구원인",
      "content": "원고와 피고는 2015년 3월...",
      "order": 2
    }
  ],
  "citations": [
    {
      "evidence_id": "ev-123",
      "reference": "[증 제1호증]",
      "description": "카카오톡 대화내역"
    }
  ],
  "footer": {
    "date": "2025년 12월 3일",
    "attorney": "변호사 박○○"
  }
}
```

**Relationships**:
- Belongs to: Case (many-to-one)
- Has many: ExportJob (one-to-many)
- References: Evidence (many-to-many via citations)

---

### 2. ExportJob

Records each document export operation for audit trail.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | Unique identifier |
| draft_id | UUID | Foreign Key → draft_documents.id, NOT NULL | Source draft |
| case_id | UUID | Foreign Key → cases.id, NOT NULL | Parent case (denormalized for queries) |
| user_id | UUID | Foreign Key → users.id, NOT NULL | User who initiated export |
| format | Enum | NOT NULL | DOCX, PDF |
| status | Enum | NOT NULL | PENDING, PROCESSING, COMPLETED, FAILED |
| file_key | String | nullable | S3 key for generated file |
| file_size | Integer | nullable | File size in bytes |
| page_count | Integer | nullable | Number of pages |
| error_message | String | nullable | Error details if failed |
| started_at | DateTime | NOT NULL | When export started |
| completed_at | DateTime | nullable | When export finished |
| expires_at | DateTime | nullable | When S3 file expires (24h after creation) |

**Relationships**:
- Belongs to: DraftDocument (many-to-one)
- Belongs to: User (many-to-one)
- Belongs to: Case (many-to-one)

**State Transitions**:
```
PENDING → PROCESSING → COMPLETED
                    ↘ FAILED
```

---

### 3. DocumentTemplate

Legal document formatting templates (pre-configured, not user-editable).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | Primary Key | Unique identifier |
| name | String | NOT NULL, unique | Template name (e.g., "divorce_complaint") |
| document_type | Enum | NOT NULL | COMPLAINT, MOTION, BRIEF, RESPONSE |
| description | String | nullable | Human-readable description |
| html_template | Text | NOT NULL | Jinja2 HTML template for PDF |
| css_styles | Text | NOT NULL | CSS for PDF formatting |
| docx_template_key | String | nullable | S3 key for Word template |
| margins | JSON | NOT NULL | Page margin settings |
| is_active | Boolean | default true | Whether template is available |
| created_at | DateTime | NOT NULL | Creation timestamp |
| updated_at | DateTime | NOT NULL | Last modification |

**Margins JSON Structure**:
```json
{
  "top": 25,
  "bottom": 25,
  "left": 20,
  "right": 20,
  "unit": "mm"
}
```

**Relationships**:
- Used by: DraftDocument (implicit via document_type)

---

## Enums

### DocumentType
```python
class DocumentType(str, Enum):
    COMPLAINT = "complaint"      # 소장
    MOTION = "motion"            # 신청서
    BRIEF = "brief"              # 준비서면
    RESPONSE = "response"        # 답변서
```

### DraftStatus
```python
class DraftStatus(str, Enum):
    DRAFT = "draft"              # Initial AI-generated
    REVIEWED = "reviewed"        # Lawyer has reviewed/edited
    EXPORTED = "exported"        # Has been exported at least once
```

### ExportFormat
```python
class ExportFormat(str, Enum):
    DOCX = "docx"
    PDF = "pdf"
```

### ExportJobStatus
```python
class ExportJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Database Schema (PostgreSQL)

```sql
-- Draft documents table
CREATE TABLE draft_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_draft_documents_case_id ON draft_documents(case_id);
CREATE INDEX idx_draft_documents_status ON draft_documents(status);

-- Export jobs table
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    draft_id UUID NOT NULL REFERENCES draft_documents(id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    format VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    file_key VARCHAR(500),
    file_size INTEGER,
    page_count INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_export_jobs_draft_id ON export_jobs(draft_id);
CREATE INDEX idx_export_jobs_case_id ON export_jobs(case_id);
CREATE INDEX idx_export_jobs_user_id ON export_jobs(user_id);
CREATE INDEX idx_export_jobs_status ON export_jobs(status);

-- Document templates table
CREATE TABLE document_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    document_type VARCHAR(50) NOT NULL,
    description TEXT,
    html_template TEXT NOT NULL,
    css_styles TEXT NOT NULL,
    docx_template_key VARCHAR(500),
    margins JSONB NOT NULL DEFAULT '{"top": 25, "bottom": 25, "left": 20, "right": 20, "unit": "mm"}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## Validation Rules

### DraftDocument
- `case_id` must reference an existing case where user has MEMBER or OWNER role
- `content` must be valid JSON matching the expected structure
- `version` must be >= 1 and increment on each edit

### ExportJob
- `format` must be one of: DOCX, PDF
- `file_key` must be set when status is COMPLETED
- `error_message` must be set when status is FAILED
- `completed_at` must be set when status is COMPLETED or FAILED

### DocumentTemplate
- `name` must be unique and use snake_case
- `margins` values must be positive numbers
- `html_template` must be valid Jinja2 syntax

---

## Audit Log Integration

All export operations are logged to the existing `audit_logs` table:

```json
{
  "action": "EXPORT_DRAFT",
  "user_id": "user-uuid",
  "case_id": "case-uuid",
  "resource_type": "draft_document",
  "resource_id": "draft-uuid",
  "details": {
    "format": "pdf",
    "export_job_id": "job-uuid",
    "page_count": 25,
    "file_size": 1234567
  },
  "ip_address": "192.168.1.1",
  "timestamp": "2025-12-03T10:30:00Z"
}
```
