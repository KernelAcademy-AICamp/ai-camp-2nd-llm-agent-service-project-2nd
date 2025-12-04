# Implementation Plan: Draft Document Export

**Branch**: `001-draft-export` | **Date**: 2025-12-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-draft-export/spec.md`

## Summary

Enable lawyers to export AI-generated draft documents to Word (.docx) and PDF formats with proper Korean legal document formatting. The feature includes a preview/edit capability before export, maintains document integrity with headers/footers/margins, and logs all export actions for audit compliance.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript (Frontend)
**Primary Dependencies**: FastAPI, Next.js 14, python-docx (Word generation), WeasyPrint or ReportLab (PDF generation)
**Storage**: PostgreSQL (export job records), S3 (temporary file storage for large exports)
**Testing**: pytest (Backend), Jest + React Testing Library (Frontend)
**Target Platform**: Web application (CloudFront CDN)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Export completion under 30 seconds for 50-page documents
**Constraints**: A4 paper size, Korean court standard formatting, UTF-8 encoding
**Scale/Scope**: Support documents up to 500 pages, concurrent exports per user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Notes |
|-----------|--------|------------------|
| I. Evidence Integrity | PASS | Export actions logged to audit_logs table (FR-007) |
| II. Case Isolation | PASS | Export restricted to case members only (FR-009) |
| III. No Auto-Submit | PASS | Export is user-initiated, no auto-submission to external systems |
| IV. AWS-Only Data Storage | PASS | Temporary files stored in S3, no external storage |
| V. Clean Architecture | PASS | Will follow Routers → Services → Repositories pattern |
| VI. Branch Protection | PASS | Development on feature branch, PR to dev required |

**Gate Status**: ALL PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-draft-export/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── export-api.yaml  # OpenAPI specification
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── export.py           # Export API router
│   ├── services/
│   │   └── export_service.py   # Export business logic
│   ├── repositories/
│   │   └── export_repository.py # Export job persistence
│   └── utils/
│       ├── docx_generator.py   # Word document generation
│       └── pdf_generator.py    # PDF document generation
└── tests/
    ├── test_api/
    │   └── test_export.py
    └── test_services/
        └── test_export_service.py

frontend/
├── src/
│   ├── app/
│   │   └── cases/[id]/draft/
│   │       └── page.tsx        # Draft preview page
│   ├── components/
│   │   └── draft/
│   │       ├── DraftPreview.tsx
│   │       ├── DraftEditor.tsx
│   │       └── ExportButton.tsx
│   └── lib/
│       └── api/
│           └── export.ts       # Export API client
└── tests/
    └── components/
        └── draft/
```

**Structure Decision**: Web application structure (Option 2) - Backend handles document generation and export logic, Frontend provides preview/edit UI and export triggers.

## Complexity Tracking

> No violations identified - all principles pass.

*This section intentionally left minimal as no complexity justifications are required.*
