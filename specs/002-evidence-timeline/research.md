# Research: Evidence Timeline

**Feature**: 002-evidence-timeline
**Date**: 2025-12-04
**Phase**: 0 - Research

## Executive Summary

The Evidence Timeline feature provides chronological visualization of case evidence with filtering and significance highlighting. Analysis of existing codebase reveals:

1. **AI Worker has complete timeline generation logic** - `ai_worker/src/analysis/timeline_generator.py` contains TimelineEvent, TimelineResult models and filtering methods
2. **Frontend has basic timeline component** - `frontend/src/components/evidence/Timeline.tsx` needs enhancement
3. **Backend API exists for evidence retrieval** - `GET /cases/{case_id}/evidence` returns evidence list
4. **Gap**: No dedicated timeline API endpoint with filtering parameters

## Existing Code Analysis

### 1. AI Worker Timeline Generator

**File**: `ai_worker/src/analysis/timeline_generator.py`

**Key Components**:

| Component | Description | Reusability |
|:----------|:------------|:------------|
| `TimelineEventType` | Enum: MESSAGE, DOCUMENT, IMAGE, AUDIO, VIDEO, INCIDENT | Direct reuse in backend |
| `TimelineEvent` | Pydantic model with 15+ fields | Direct reuse in backend |
| `TimelineResult` | Container with events, stats, date_range | Direct reuse in backend |
| `TimelineGenerator` | Generator class with filtering methods | Methods to port to service |

**Significance Calculation Logic**:
```python
SIGNIFICANCE_WEIGHTS = {
    "부정행위": 5, "폭행": 5, "학대": 5,
    "유기": 4, "협박": 4, "위협": 4,
    "폭언": 3, "계속적_불화": 3, "혼인_파탄": 3,
    "재산_문제": 2, "양육_문제": 2
}

KEY_EVIDENCE_LABELS = {"부정행위", "폭행", "학대", "유기", "협박", "위협"}
```

**Filtering Methods Available**:
- `filter_by_date_range(start_date, end_date)` - Date range filter
- `filter_by_labels(labels)` - Label filter
- `filter_by_speaker(speaker)` - Speaker filter
- `get_key_events()` - Key evidence only

### 2. Frontend Timeline Component

**File**: `frontend/src/components/evidence/Timeline.tsx`

**Current State**:
- Basic vertical timeline with date markers
- Type icons (FileText, Image, Mic, Video)
- Click handler to select evidence
- Sorts by `uploadDate` (not event timestamp)
- No filtering, no significance highlighting

**Current Props**:
```typescript
interface TimelineProps {
    items: Evidence[];
    onSelect: (id: string) => void;
}
```

**Enhancement Needed**:
- Add filter state and callbacks
- Add significance visual indicators
- Support event timestamp vs upload date
- Virtual scroll for large lists
- Tooltip for details

### 3. Evidence Types

**File**: `frontend/src/types/evidence.ts`

```typescript
export interface Evidence {
    id: string;
    caseId: string;
    filename: string;
    type: EvidenceType;  // 'text' | 'image' | 'audio' | 'video' | 'pdf'
    status: EvidenceStatus;
    uploadDate: string;
    summary?: string;
    size: number;
    speaker?: SpeakerType;  // '원고' | '피고' | '제3자' | 'unknown'
    labels?: string[];
    timestamp?: string;  // Event timestamp
}
```

### 4. Backend Evidence API

**File**: `backend/app/api/evidence.py`, `backend/app/api/cases.py`

**Existing Endpoints**:
| Endpoint | Method | Returns | Notes |
|:---------|:-------|:--------|:------|
| `GET /cases/{case_id}/evidence` | GET | List[EvidenceSummary] | No filtering params |
| `GET /evidence/{evidence_id}` | GET | EvidenceDetail | Single evidence |

**DynamoDB Schema** (`backend/app/utils/dynamo.py`):
- Table: `leh_evidence`
- PK: `evidence_id`
- GSI: `case_id-index`
- Fields: evidence_id, case_id, type, filename, s3_key, status, created_at, ai_summary, labels, speaker, timestamp, article_840_tags

## Gap Analysis

| Requirement | Existing | Gap | Solution |
|:------------|:---------|:----|:---------|
| Chronological timeline | uploadDate sort only | Event timestamp sort | Use `timestamp` field from AI Worker |
| Date range filter | None | Backend/Frontend | Add query params to API |
| Label filter | Frontend only (categories) | Backend | Add query params to API |
| Speaker filter | None | Backend/Frontend | Add query params to API |
| Significance highlighting | AI Worker calculates | Not exposed to frontend | Add `significance` field to response |
| Key evidence toggle | AI Worker has `is_key_evidence` | Not exposed to frontend | Add field to response |
| Pagination | None | Performance | Add limit/offset params |

## Recommended Approach

### Backend Changes

1. **New Timeline Router**: `backend/app/api/timeline.py`
   - `GET /cases/{case_id}/timeline` with filter query params

2. **New Timeline Service**: `backend/app/services/timeline_service.py`
   - Port `TimelineGenerator` logic from ai_worker
   - Add `get_timeline(case_id, filters)` method

3. **Extend Evidence Repository**:
   - Add timeline-specific query with timestamp sorting

4. **New Schemas**: `backend/app/schemas/timeline.py`
   - Port `TimelineEvent`, `TimelineResult` from ai_worker
   - Add `TimelineFilter` for query params

### Frontend Changes

1. **New Types**: `frontend/src/types/timeline.ts`
   - TimelineEvent, TimelineFilter, TimelineResult

2. **Enhanced Timeline Component**: Extend `Timeline.tsx`
   - Add visual significance indicators
   - Add key evidence badge
   - Support filtering callbacks

3. **New Components**:
   - `TimelineFilter.tsx` - Date range, label, speaker dropdowns
   - `TimelineEvent.tsx` - Individual event with tooltip
   - `TimelineTooltip.tsx` - Hover details

4. **New Hook**: `useTimeline.ts`
   - Fetch timeline data with filters
   - Handle loading/error states

5. **New API Client**: `frontend/src/lib/api/timeline.ts`
   - `fetchTimeline(caseId, filters)`

## Technical Decisions

### D1: Reuse AI Worker Models vs Create Backend Models

**Decision**: Port models to backend, don't import from ai_worker

**Rationale**:
- ai_worker is Lambda deployment, separate package
- Backend needs Pydantic models for FastAPI schemas
- Avoid coupling between deployment units

### D2: Server-side vs Client-side Filtering

**Decision**: Server-side filtering with query parameters

**Rationale**:
- DynamoDB query can filter efficiently
- Reduces payload size for large cases
- Consistent pagination behavior

### D3: Pagination Strategy

**Decision**: Offset-based pagination (limit + offset)

**Rationale**:
- Simpler implementation
- DynamoDB supports limit
- Cursor-based not needed for <1000 items

## Dependencies

| Dependency | Version | Purpose | Status |
|:-----------|:--------|:--------|:-------|
| FastAPI | 0.104+ | Backend framework | Existing |
| Pydantic | 2.x | Schema validation | Existing |
| boto3 | 1.34+ | DynamoDB client | Existing |
| React | 18.x | Frontend framework | Existing |
| TanStack Query | 5.x | Data fetching | Existing |
| lucide-react | 0.263+ | Icons | Existing |

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|:-----|:-------|:------------|:-----------|
| Large cases (500+ items) slow render | Medium | Low | Virtual scrolling, pagination |
| Timestamp parsing errors | Low | Medium | Fallback to created_at |
| Article 840 label mismatch | Low | Low | Use existing enum values |

## Open Questions

1. **Q**: Should timeline persist filter state in URL?
   **A**: Yes, use query params for shareable links

2. **Q**: Show empty events (no timestamp)?
   **A**: Yes, group at end with "날짜 미상" marker

3. **Q**: Default sort order?
   **A**: Oldest first (chronological) for legal narrative

## References

- [AI Worker Timeline Generator](../../ai_worker/src/analysis/timeline_generator.py)
- [Frontend Timeline Component](../../frontend/src/components/evidence/Timeline.tsx)
- [Evidence API](../../backend/app/api/evidence.py)
- [DynamoDB Schema](../../backend/app/utils/dynamo.py)
- [Article 840 Categories](../../backend/app/db/schemas.py)
