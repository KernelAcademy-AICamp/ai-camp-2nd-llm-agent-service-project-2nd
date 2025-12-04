# Implementation Plan: Evidence Timeline

**Branch**: `002-evidence-timeline` | **Date**: 2025-12-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-evidence-timeline/spec.md`

## Summary

Implement chronological evidence timeline visualization for divorce cases. The feature displays all case evidence on an interactive timeline with filtering (date range, speaker, labels), significance highlighting for key evidence, and navigation to evidence details. Builds on existing `ai_worker/src/analysis/timeline_generator.py` for backend data model and `frontend/src/components/evidence/Timeline.tsx` for UI foundation.

## Technical Context

**Language/Version**: Python 3.11 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, Next.js 14, React, Tailwind CSS, boto3 (DynamoDB)
**Storage**: DynamoDB (evidence metadata), Qdrant (embeddings - read-only for this feature)
**Testing**: pytest (Backend), Jest + React Testing Library (Frontend)
**Target Platform**: Web (Chrome, Safari, Firefox, Edge - latest 2 versions)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: <2s initial load (100 items), <500ms filter operations, 60fps scroll
**Constraints**: Max 1000 evidence items per case, Korean UTF-8 support required
**Scale/Scope**: ~100 concurrent users, ~500 evidence items per average case

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|:----------|:-------|:------|
| I. Evidence Integrity | PASS | Read-only timeline view. No evidence modification. Audit log entry on view access. |
| II. Case Isolation | PASS | Timeline queries scoped by case_id. No cross-case data access. |
| III. No Auto-Submit | PASS | Display-only feature. No AI output submission. |
| IV. AWS-Only Storage | PASS | Reads from DynamoDB/Qdrant on AWS. No external storage. |
| V. Clean Architecture | PASS | Router → TimelineService → EvidenceRepository → DynamoDB |
| VI. Branch Protection | PASS | Feature branch `002-evidence-timeline` → PR → dev → main |

**Constitution Gate**: PASSED

## Project Structure

### Documentation (this feature)

```text
specs/002-evidence-timeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── timeline.py           # NEW: Timeline router
│   ├── services/
│   │   └── timeline_service.py   # NEW: Timeline business logic
│   ├── repositories/
│   │   └── evidence_repository.py  # EXTEND: Add timeline queries
│   ├── schemas/
│   │   └── timeline.py           # NEW: Pydantic models
│   └── utils/
│       └── dynamo.py             # EXTEND: Timeline query helpers
└── tests/
    ├── test_api/
    │   └── test_timeline.py      # NEW: API endpoint tests
    └── test_services/
        └── test_timeline_service.py  # NEW: Service unit tests

frontend/
├── src/
│   ├── app/
│   │   └── cases/
│   │       └── [id]/
│   │           └── timeline/
│   │               └── page.tsx  # NEW: Timeline page route
│   ├── components/
│   │   └── evidence/
│   │       ├── Timeline.tsx      # EXTEND: Enhanced timeline component
│   │       ├── TimelineFilter.tsx    # NEW: Filter controls
│   │       ├── TimelineEvent.tsx     # NEW: Individual event component
│   │       └── TimelineTooltip.tsx   # NEW: Hover tooltip
│   ├── hooks/
│   │   └── useTimeline.ts        # NEW: Timeline data hook
│   ├── lib/
│   │   └── api/
│   │       └── timeline.ts       # NEW: Timeline API client
│   └── types/
│       └── timeline.ts           # NEW: TypeScript types
└── tests/
    └── components/
        └── evidence/
            └── Timeline.test.tsx # NEW: Component tests

ai_worker/
└── src/
    └── analysis/
        └── timeline_generator.py # REFERENCE: Existing implementation (read-only)
```

**Structure Decision**: Web application (Option 2) - LEH is a three-tier system with dedicated frontend and backend. New timeline feature adds API endpoint in backend and UI components in frontend, following existing patterns.

## Complexity Tracking

> No violations. Feature follows established patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
