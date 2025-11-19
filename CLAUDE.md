# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Legal Evidence Hub (LEH)** - AI 파라리걸 & 이혼 사건 전용 증거 허브

A three-tier AI-assisted legal platform that automatically analyzes, organizes, and generates draft documents from divorce case evidence. The system uses AWS services, FastAPI backend, React frontend, and event-driven AI workers.

**Current Version:** 0.2.0 (Early implementation stage)

---

## System Architecture

### High-Level Components

```
Frontend (React/Next.js) → Backend API (FastAPI) → AWS Services
                                                    ├── S3 (evidence files)
                                                    ├── RDS PostgreSQL (users, cases)
                                                    ├── DynamoDB (evidence metadata)
                                                    └── OpenSearch (RAG indices)
S3 Event → AI Worker (Lambda/ECS) → DynamoDB + OpenSearch
```

### Critical Architecture Principles

1. **Stateless API Design**: All state in RDS/DynamoDB/OpenSearch/S3, never in-memory
2. **Event-Driven Processing**: S3 uploads trigger AI Worker via S3 Events (not polling)
3. **Per-Case RAG Isolation**: Each case has isolated OpenSearch index (`case_rag_{case_id}`)
4. **Data Layer Separation**:
   - **S3**: Raw evidence files only
   - **RDS**: Structured data (users, cases, permissions, audit logs)
   - **DynamoDB**: Evidence analysis results (JSON metadata)
   - **OpenSearch**: Full-text and semantic search with embeddings

5. **Read-Only Backend for Evidence**: AI Worker writes to DynamoDB/OpenSearch; Backend only reads

---

## Directory Structure & Conventions

### Backend (`backend/app/`)

```
app/
├── main.py                 # FastAPI app, middleware registration, lifespan
├── core/
│   ├── config.py           # Pydantic Settings (single source of env vars)
│   └── security.py         # JWT encode/decode (future)
├── db/
│   ├── session.py          # SQLAlchemy connection pooling
│   ├── models.py           # SQLAlchemy ORM models
│   └── schemas.py          # Pydantic request/response schemas
├── api/                    # API endpoints (per BACKEND_SERVICE_REPOSITORY_GUIDE.md)
│   ├── auth.py             # /auth/login, /auth/refresh
│   ├── cases.py            # /cases CRUD
│   ├── evidence.py         # /evidence presigned URLs
│   ├── draft.py            # /cases/{id}/draft-preview
│   └── search.py           # /cases/{id}/search (RAG)
├── services/               # Business logic, AWS integration
│   ├── case_service.py
│   ├── evidence_service.py # S3 + DynamoDB ops
│   ├── draft_service.py    # GPT-4o orchestration
│   └── search_service.py   # OpenSearch queries
├── repositories/           # Data access layer (DB, DynamoDB, etc.)
│   ├── case_repository.py
│   └── evidence_repository.py
├── utils/
│   ├── s3.py               # Presigned URL generation
│   ├── dynamo.py           # DynamoDB wrapper
│   └── opensearch.py       # OpenSearch wrapper
└── middleware/
    ├── security.py         # Security headers, HTTPS redirect
    ├── error_handler.py    # Global exception handling
    ├── auth_middleware.py  # JWT validation (future)
    └── audit.py            # Audit logging (future)
```

**Key Patterns:**
- Use `api/` for API endpoints (per BACKEND_SERVICE_REPOSITORY_GUIDE.md)
- Use Service/Repository pattern: API → Services → Repositories → Utils
- Import config via `from app.core.config import settings`
- All API responses use unified error format (see middleware/error_handler.py)
- Custom exceptions: `LEHException`, `AuthenticationError`, `PermissionError`, etc.

### AI Worker (`ai_worker/`)

```
ai_worker/
├── handler.py              # Lambda/ECS entry point
├── processor/
│   ├── router.py           # File type routing (text/image/audio/video/PDF)
│   ├── text_parser.py      # Conversation parsing
│   ├── ocr.py              # GPT-4o Vision OCR
│   ├── stt.py              # Whisper STT + diarization
│   ├── semantic.py         # 민법 제840 guilt factor labeling
│   ├── embed.py            # OpenAI embedding generation
│   └── timeline.py         # Timeline formatting
└── utils/
    ├── s3.py
    ├── opensearch.py       # Index creation, document upload
    ├── dynamo.py           # Evidence metadata writes
    └── ffmpeg.py           # Audio/video extraction
```

---

## Common Development Commands

### Backend

```bash
# Setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
# OR
python app/main.py

# API documentation (when DEBUG=true)
# http://localhost:8000/docs

# Run tests (when implemented)
pytest tests/ -v
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # Dev server at :3000 (Next.js) or :5173 (Vite)
npm run build
npm run lint
```

### AI Worker

```bash
cd ai_worker
pip install -r requirements.txt
WORKER_ENV=dev python handler.py
```

### Full Stack (Docker Compose)

```bash
# Start all services
docker compose up --build

# View logs
docker compose logs -f backend
docker compose logs -f ai_worker

# Stop
docker compose down
```

---

## Critical Data Flows

### Evidence Upload → Processing → Display

1. **FE → Backend**: `POST /evidence/presigned-url` → Get S3 signed URL
2. **FE → S3**: Direct upload using presigned URL (multipart)
3. **S3 → AI Worker**: S3 Event (`ObjectCreated`) triggers Lambda/ECS
4. **AI Worker**:
   - Download from S3
   - Route by file type → OCR/STT/parsing
   - Generate embeddings + semantic labels
   - Write to DynamoDB (metadata) + OpenSearch (RAG)
5. **FE → Backend**: Poll `GET /cases/{id}/evidence` until `status="done"`
6. **Backend → FE**: Return DynamoDB metadata (summary, labels, insights)

### Draft Preview Generation

1. **FE → Backend**: `POST /cases/{id}/draft-preview`
2. **Backend**:
   - Fetch case metadata from RDS
   - Query DynamoDB for evidence list
   - Query OpenSearch for semantic RAG search
   - Call GPT-4o with RAG context
   - Return draft text + citation references
3. **FE**: Display in read-only preview panel (no auto-submit)

---

## Configuration Management

### Environment Variables Pattern

**All config via Pydantic Settings** (`app/core/config.py`):
```python
from app.core.config import settings

# Access anywhere
settings.APP_ENV          # "local" | "dev" | "prod"
settings.JWT_SECRET       # Strong secret key
settings.S3_EVIDENCE_BUCKET
settings.DATABASE_URL     # Auto-generated or explicit
settings.cors_origins_list  # Computed property
```

**Never hardcode values** - always use `settings.*`

### Critical Environment Variables

```bash
# Application
APP_ENV=prod|dev|local
APP_DEBUG=false  # Disable /docs in production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+psycopg2://...
# OR individual: POSTGRES_HOST, POSTGRES_PORT, etc.

# JWT
JWT_SECRET=<strong-random-string>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# AWS
AWS_REGION=ap-northeast-2
S3_EVIDENCE_BUCKET=leh-evidence-prod
S3_PRESIGNED_URL_EXPIRE_SECONDS=300  # 5min max

DDB_EVIDENCE_TABLE=leh_evidence_prod
OPENSEARCH_HOST=https://...

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL_CHAT=gpt-4o-mini
OPENAI_MODEL_EMBEDDING=text-embedding-3-small

# Frontend
VITE_API_BASE_URL=https://api.leh.example.com
```

---

## Database Schemas

### PostgreSQL (RDS)

```sql
-- Core tables
users(id, email, hashed_password, name, role, created_at)
cases(id, title, description, status, created_by, created_at)
case_members(case_id, user_id, role)  -- role: owner|member|viewer
audit_logs(id, user_id, action, object_id, timestamp)
```

### DynamoDB

**Table:** `leh_evidence_prod`
- **PK:** `case_id`
- **SK:** `evidence_id`
- **Attributes:** type, timestamp, speaker, labels, ai_summary, insights, content, s3_key, status, opensearch_id

### OpenSearch

**Index pattern:** `case_rag_{case_id}` (per-case isolation)

**Document structure:**
```json
{
  "id": "case_123_ev_1",
  "content": "Full STT/OCR text",
  "labels": ["폭언", "계속적 불화"],
  "timestamp": "2024-12-25T10:20:00Z",
  "speaker": "피고",
  "vector": [0.123, ...]  // 1536-dim embedding
}
```

---

## Error Handling Conventions

### Custom Exception Hierarchy

```python
from app.middleware import (
    LEHException,           # Base (500)
    AuthenticationError,    # 401
    PermissionError,        # 403
    NotFoundError,          # 404
    ConflictError           # 409
)

# Usage
raise NotFoundError("Case")
# → Returns: {"error": {"code": "NOT_FOUND", "message": "Case not found", "error_id": "...", "timestamp": "..."}}
```

### Unified Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "error_id": "uuid",
    "timestamp": "ISO8601",
    "details": [...]  // Optional
  }
}
```

**Production Safety:** Error messages automatically masked in `APP_ENV=prod`

---

## Security Best Practices (SECURITY_COMPLIANCE.md)

### Absolute Prohibitions

1. **AI Auto-Submit Forbidden**: Draft is "Preview only", never auto-submit
2. **No Sensitive Data in Logs**: Never log evidence content, only evidence_id
3. **Backend Read-Only for Evidence**: Only AI Worker writes to DynamoDB/OpenSearch
4. **Direct S3 Upload Only**: Always use presigned URLs, never proxy through API

### Implemented Safeguards

- JWT token-based stateless auth (24h TTL)
- Security headers middleware (X-Frame-Options, CSP, HSTS in prod)
- HTTPS redirect in production
- Per-case data isolation (RBAC + index separation)
- S3 presigned URLs expire in 5 minutes max
- Soft-delete for case closure (audit trail preserved)

---

## Team Collaboration & Git Workflow

### Branch Strategy

```
main  ←  dev  ←  feat/*
```

- **main**: Production-ready, direct push forbidden, PR-only
- **dev**: Integration branch, free push for H/L/P
- **feat/***: Feature branches (optional), merge to dev

### Commit Message Convention

```
feat:     New feature
fix:      Bug fix
refactor: Structure change (no functional change)
docs:     Documentation only
chore:    Build/config/logging
```

**Always in English** for AI analysis compatibility

### Team Roles

- **H (You)**: Backend/Infra - FastAPI, RDS, JWT auth, AWS integration
- **L**: AI/Data - AI Worker, OCR/STT, semantic analysis, RAG
- **P**: Frontend/PM - React, PR approval, GitHub management

---

## Key Design Documents (Source of Truth)

Located in `docs/`:

### Core Specs (`docs/specs/`)
- **PRD.md**: Product requirements, MVP scope
- **ARCHITECTURE.md**: System architecture, data flows
- **BACKEND_DESIGN.md**: Backend structure, API design patterns
- **API_SPEC.md**: REST API endpoints, request/response formats
- **AI_PIPELINE_DESIGN.md**: AI Worker pipeline, processing stages
- **SECURITY_COMPLIANCE.md**: Security rules, legal compliance

### Development Guides (`docs/guides/`)
- **BACKEND_SERVICE_REPOSITORY_GUIDE.md**: Service/Repository pattern, layered architecture
- **CLEAN_ARCHITECTURE_GUIDE.md**: Clean code principles, design patterns, domain separation
- **test_template.md**: TDD test structure, Given-When-Then pattern
- **CONTRIBUTING.md**: Git workflow, branching strategy

**When in doubt, refer to these docs** - they define the canonical system design.

---

## AWS Service Integration Patterns

### S3 Presigned URL Pattern

```python
from app.utils.s3 import generate_presigned_upload_url

# In evidence_service.py
presigned_data = generate_presigned_upload_url(
    bucket=settings.S3_EVIDENCE_BUCKET,
    key=f"cases/{case_id}/raw/{uuid}_{filename}",
    expires_in=300  # 5 minutes
)
# Returns: {"upload_url": "...", "fields": {...}}
```

**Bucket Structure:**
```
s3://leh-evidence-prod/
  cases/
    {case_id}/
      raw/          # Original uploads
      processed/    # (Optional) processed versions
```

### DynamoDB Query Pattern

```python
# Query all evidence for a case
response = dynamodb_client.query(
    TableName=settings.DDB_EVIDENCE_TABLE,
    KeyConditionExpression='case_id = :cid',
    ExpressionAttributeValues={':cid': {'S': case_id}}
)
```

### OpenSearch RAG Search

```python
# Semantic search with filters
results = opensearch_client.search(
    index=f'case_rag_{case_id}',
    body={
        "query": {
            "bool": {
                "must": [{"knn": {"vector": {"vector": query_embedding, "k": 5}}}],
                "filter": [{"term": {"labels": "폭언"}}]
            }
        }
    }
)
```

---

## Deployment

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/deploy_paralegal.yml`):

- **Trigger:** Push to `main` with changes in `backend/`, `ai_worker/`, or `docker-compose.yml`
- **Process:**
  1. SCP files to Oracle VM
  2. SSH into VM
  3. `docker compose down && docker compose up -d --build`

**Required Secrets:** `SSH_HOST`, `SSH_USER`, `SSH_PORT`, `SSH_KEY`, `APP_DIR`

### Environment Progression

- **local**: Developer machine, minimal AWS mocks
- **dev**: Staging, RDS/DynamoDB/OpenSearch dev instances
- **prod**: Full AWS managed services

---

## Testing Strategy

### Backend Tests

```bash
# All tests
pytest -v

# Core module tests (config, etc.)
pytest tests/test_core/ -v

# Middleware tests (security, error handling)
pytest tests/test_middleware/ -v

# API tests (integration tests)
pytest tests/test_api/ -v

# Service layer tests (when implemented)
pytest tests/test_services/ -v

# Repository layer tests (when implemented)
pytest tests/test_repositories/ -v

# Run specific test
pytest tests/test_services/test_evidence_service.py::test_presigned_url -v
```

### Frontend Tests

```bash
npm test                    # Jest + React Testing Library
npm run test:coverage       # Coverage report
```

**Mock Pattern:** Use `pytest-mock` for S3/DynamoDB/OpenSearch mocking

---

## Known Limitations & Future Work

### Current Implementation Status (v0.2.0)

✅ **Completed:**
- FastAPI app structure with lifespan, middleware, error handlers
- Pydantic Settings configuration
- Security headers, HTTPS redirect middleware
- Unified error response format
- Directory structure per BACKEND_SERVICE_REPOSITORY_GUIDE.md
- Test infrastructure with 67 test cases (TDD-ready)
- Service/Repository layer separation

🚧 **TODO (marked in code):**
- Database connection pooling (SQLAlchemy)
- JWT authentication middleware
- Audit log middleware
- All API endpoints (auth, cases, evidence, draft, search)
- All service implementations (S3, DynamoDB, OpenSearch integration)
- All repository implementations (case, evidence, user repositories)
- Database migrations (Alembic)

### Design Debt

- No rate limiting yet (optional for v1)
- OpenSearch index lifecycle management (delete old cases)
- Async Draft generation (currently synchronous GPT-4o calls)
- Webhook notifications for evidence processing completion

---

## Quick Reference: Common Tasks

### Add New API Endpoint

1. Create router in `app/api/{module}.py`:
```python
from fastapi import APIRouter, Depends
from app.db.schemas import ResponseSchema
from app.middleware import AuthenticationError

router = APIRouter()

@router.get("/{id}")
async def get_item(id: str):
    # Implementation
    return {"data": {...}}
```

2. Register in `main.py`:
```python
from app.api import items
app.include_router(items.router, prefix="/items", tags=["Items"])
```

### Add Environment Variable

1. Add to `app/core/config.py`:
```python
class Settings(BaseSettings):
    NEW_VAR: str = Field(default="default", env="NEW_VAR")
```

2. Add to `.env.example` with documentation
3. Access via `settings.NEW_VAR`

### Query DynamoDB Evidence

```python
from app.utils.dynamo import get_evidence_by_case

evidence_list = get_evidence_by_case(case_id="case_123")
# Returns list of evidence metadata dicts
```

### Generate Draft Preview

```python
from app.services.draft_service import generate_draft_preview

draft = await generate_draft_preview(
    case_id="case_123",
    sections=["청구취지", "청구원인"]
)
# Returns: {"draft_text": "...", "citations": [...]}
```

---

## Troubleshooting

### Common Issues

**Import errors for `app.*` modules:**
- Run from project root: `python -m app.main` or `uvicorn app.main:app`
- NOT from `backend/app/`: `python main.py` (wrong)

**Pydantic validation errors on startup:**
- Check `.env` file exists and has required variables
- Verify `DATABASE_URL` or `POSTGRES_*` variables are set

**S3 presigned URL 403 errors:**
- Verify `S3_PRESIGNED_URL_EXPIRE_SECONDS <= 300` (5min max per security policy)
- Check IAM role has `s3:PutObject` permission

**CORS errors from frontend:**
- Add frontend URL to `CORS_ALLOW_ORIGINS` in `.env`
- Verify middleware order: HTTPS redirect → Security headers → CORS

---

## Contact & Resources

**Team:**
- H (Backend/Infra): Your role
- L (AI/Data): AI Worker, ML pipeline
- P (Frontend/PM): React, GitHub admin, PR approvals

**Documentation:** All design docs in `docs/` folder
**Issue Tracking:** GitHub Issues with templates in `.github/ISSUE_TEMPLATE/`
**PR Template:** `.github/pull_request_template.md`
