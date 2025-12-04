# Quickstart: Evidence Timeline

**Feature**: 002-evidence-timeline
**Date**: 2025-12-04
**Phase**: 1 - Design

## Overview

This guide provides step-by-step instructions to implement the Evidence Timeline feature.

## Prerequisites

- [ ] Backend dev server running (`uvicorn app.main:app --reload`)
- [ ] Frontend dev server running (`npm run dev`)
- [ ] DynamoDB table `leh_evidence` accessible
- [ ] Test case with uploaded evidence in DynamoDB

## Implementation Steps

### Step 1: Backend Schemas (30 min)

Create Pydantic models for timeline data.

**File**: `backend/app/schemas/timeline.py`

```python
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field


class TimelineEventType(str, Enum):
    MESSAGE = "message"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INCIDENT = "incident"


class TimelineEvent(BaseModel):
    event_id: str
    evidence_id: str
    case_id: str
    timestamp: datetime
    date: str
    time: str
    description: str
    content_preview: Optional[str] = None
    event_type: TimelineEventType
    labels: List[str] = []
    speaker: Optional[str] = None
    source_file: str
    significance: int = Field(ge=1, le=5, default=1)
    is_key_evidence: bool = False
    metadata: Dict[str, Any] = {}

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TimelineFilter(BaseModel):
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    labels: Optional[List[str]] = None
    speakers: Optional[List[str]] = None
    event_types: Optional[List[TimelineEventType]] = None
    key_only: bool = False
    limit: int = Field(ge=1, le=100, default=50)
    offset: int = Field(ge=0, default=0)
    sort_order: Literal["asc", "desc"] = "asc"


class TimelineResult(BaseModel):
    case_id: str
    events: List[TimelineEvent]
    total_count: int
    filtered_count: int
    has_more: bool
    date_range: Dict[str, Optional[str]]
    events_by_type: Dict[str, int]
    events_by_label: Dict[str, int]
    key_events_count: int
    generated_at: datetime
```

### Step 2: Backend Service (45 min)

Create timeline business logic.

**File**: `backend/app/services/timeline_service.py`

```python
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.timeline import (
    TimelineEvent, TimelineEventType, TimelineFilter, TimelineResult
)
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.utils.dynamo import get_evidence_by_case
from app.middleware import NotFoundError, PermissionError


SIGNIFICANCE_WEIGHTS = {
    "부정행위": 5, "폭행": 5, "학대": 5,
    "유기": 4, "협박": 4, "위협": 4,
    "폭언": 3, "계속적_불화": 3, "혼인_파탄": 3,
    "재산_문제": 2, "양육_문제": 2,
}

KEY_EVIDENCE_LABELS = {"부정행위", "폭행", "학대", "유기", "협박", "위협"}


class TimelineService:
    def __init__(self, db: Session):
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)

    def get_timeline(
        self, case_id: str, user_id: str, filter: Optional[TimelineFilter] = None
    ) -> TimelineResult:
        # Validate access
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")
        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

        # Get evidence from DynamoDB
        evidence_list = get_evidence_by_case(case_id)

        # Convert to timeline events
        events = self._build_events(evidence_list, case_id)

        # Apply filters
        filter = filter or TimelineFilter()
        filtered_events = self._apply_filters(events, filter)

        # Build result
        return self._build_result(case_id, events, filtered_events, filter)

    def _build_events(self, evidence_list: List[dict], case_id: str) -> List[TimelineEvent]:
        # Implementation: convert evidence to TimelineEvent
        ...

    def _apply_filters(self, events: List[TimelineEvent], filter: TimelineFilter) -> List[TimelineEvent]:
        # Implementation: filter events
        ...

    def _build_result(self, case_id: str, all_events: List[TimelineEvent],
                      filtered_events: List[TimelineEvent], filter: TimelineFilter) -> TimelineResult:
        # Implementation: build response
        ...
```

### Step 3: Backend Router (20 min)

Create API endpoint.

**File**: `backend/app/api/timeline.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.timeline import TimelineResult, TimelineEventType
from app.services.timeline_service import TimelineService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.get("/{case_id}/timeline", response_model=TimelineResult)
def get_timeline(
    case_id: str,
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    labels: Optional[str] = Query(None),  # comma-separated
    speakers: Optional[str] = Query(None),  # comma-separated
    event_types: Optional[str] = Query(None),  # comma-separated
    key_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_order: str = Query("asc"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = TimelineService(db)

    # Parse comma-separated values
    filter = TimelineFilter(
        date_start=date_start,
        date_end=date_end,
        labels=labels.split(",") if labels else None,
        speakers=speakers.split(",") if speakers else None,
        event_types=[TimelineEventType(t) for t in event_types.split(",")] if event_types else None,
        key_only=key_only,
        limit=limit,
        offset=offset,
        sort_order=sort_order,
    )

    return service.get_timeline(case_id, user_id, filter)
```

**Register in**: `backend/app/main.py`

```python
from app.api import timeline
app.include_router(timeline.router, prefix="/cases", tags=["timeline"])
```

### Step 4: Frontend Types (15 min)

**File**: `frontend/src/types/timeline.ts`

```typescript
export type TimelineEventType =
  | 'message' | 'document' | 'image' | 'audio' | 'video' | 'incident';

export interface TimelineEvent {
    eventId: string;
    evidenceId: string;
    caseId: string;
    timestamp: string;
    date: string;
    time: string;
    description: string;
    contentPreview?: string;
    eventType: TimelineEventType;
    labels: string[];
    speaker?: string;
    sourceFile: string;
    significance: number;
    isKeyEvidence: boolean;
    metadata?: Record<string, unknown>;
}

export interface TimelineFilter {
    dateStart?: string;
    dateEnd?: string;
    labels?: string[];
    speakers?: string[];
    eventTypes?: TimelineEventType[];
    keyOnly?: boolean;
    limit?: number;
    offset?: number;
    sortOrder?: 'asc' | 'desc';
}

export interface TimelineResult {
    caseId: string;
    events: TimelineEvent[];
    totalCount: number;
    filteredCount: number;
    hasMore: boolean;
    dateRange: { start: string | null; end: string | null };
    eventsByType: Record<string, number>;
    eventsByLabel: Record<string, number>;
    keyEventsCount: number;
    generatedAt: string;
}
```

### Step 5: Frontend API Client (15 min)

**File**: `frontend/src/lib/api/timeline.ts`

```typescript
import { TimelineResult, TimelineFilter } from '@/types/timeline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function fetchTimeline(
    caseId: string,
    filter?: TimelineFilter
): Promise<TimelineResult> {
    const params = new URLSearchParams();
    if (filter?.dateStart) params.set('date_start', filter.dateStart);
    if (filter?.dateEnd) params.set('date_end', filter.dateEnd);
    if (filter?.labels?.length) params.set('labels', filter.labels.join(','));
    if (filter?.speakers?.length) params.set('speakers', filter.speakers.join(','));
    if (filter?.keyOnly) params.set('key_only', 'true');
    if (filter?.limit) params.set('limit', String(filter.limit));
    if (filter?.offset) params.set('offset', String(filter.offset));
    if (filter?.sortOrder) params.set('sort_order', filter.sortOrder);

    const url = `${API_BASE}/cases/${caseId}/timeline?${params}`;
    const res = await fetch(url, { credentials: 'include' });
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
}
```

### Step 6: Frontend Hook (15 min)

**File**: `frontend/src/hooks/useTimeline.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { fetchTimeline } from '@/lib/api/timeline';
import { TimelineFilter, TimelineResult } from '@/types/timeline';

export function useTimeline(caseId: string, filter?: TimelineFilter) {
    return useQuery<TimelineResult, Error>({
        queryKey: ['timeline', caseId, filter],
        queryFn: () => fetchTimeline(caseId, filter),
        staleTime: 30_000,
        enabled: !!caseId,
    });
}
```

### Step 7: Enhanced Timeline Component (60 min)

Update the existing Timeline component with filtering and significance.

**File**: `frontend/src/components/evidence/Timeline.tsx` (extend existing)

Key additions:
- Filter state management
- Significance visual indicators (colored markers)
- Key evidence badge
- Date grouping headers
- Loading/empty states

### Step 8: Testing (45 min)

**Backend Tests**: `backend/tests/test_api/test_timeline.py`
- Test timeline endpoint returns correct structure
- Test filtering works correctly
- Test access control

**Frontend Tests**: `frontend/tests/components/evidence/Timeline.test.tsx`
- Test rendering with events
- Test filter interactions
- Test empty state

## Verification Checklist

- [ ] `GET /cases/{id}/timeline` returns 200 with valid JWT
- [ ] Filtering by date range works
- [ ] Filtering by labels works
- [ ] Filtering by speaker works
- [ ] `key_only=true` shows only key evidence
- [ ] Pagination (limit/offset) works
- [ ] Sort order (asc/desc) works
- [ ] Timeline renders events chronologically
- [ ] Key evidence is visually highlighted
- [ ] Filter controls update URL query params
- [ ] Empty state displayed when no events

## Time Estimate

| Step | Estimated Time |
|:-----|:--------------|
| Backend Schemas | 30 min |
| Backend Service | 45 min |
| Backend Router | 20 min |
| Frontend Types | 15 min |
| Frontend API | 15 min |
| Frontend Hook | 15 min |
| Timeline Component | 60 min |
| Testing | 45 min |
| **Total** | **~4 hours** |
