# Data Model: Evidence Timeline

**Feature**: 002-evidence-timeline
**Date**: 2025-12-04
**Phase**: 1 - Design

## Overview

This document defines the data models for the Evidence Timeline feature. Models are designed to be portable across backend (Python/Pydantic) and frontend (TypeScript).

## Core Models

### TimelineEventType (Enum)

Evidence type classification for timeline display.

```python
# Python (backend/app/schemas/timeline.py)
class TimelineEventType(str, Enum):
    MESSAGE = "message"      # 카카오톡/문자/대화
    DOCUMENT = "document"    # PDF/문서
    IMAGE = "image"          # 이미지
    AUDIO = "audio"          # 음성
    VIDEO = "video"          # 비디오
    INCIDENT = "incident"    # AI 추출 사건/이슈
```

```typescript
// TypeScript (frontend/src/types/timeline.ts)
export type TimelineEventType =
  | 'message'
  | 'document'
  | 'image'
  | 'audio'
  | 'video'
  | 'incident';
```

### TimelineEvent

Single event on the timeline.

```python
# Python (backend/app/schemas/timeline.py)
class TimelineEvent(BaseModel):
    event_id: str                     # Unique event ID
    evidence_id: str                  # Reference to evidence record
    case_id: str                      # Case ID

    # Time
    timestamp: datetime               # Event occurrence time
    date: str                         # YYYY-MM-DD
    time: str                         # HH:MM

    # Content
    description: str                  # Brief description (max 100 chars)
    content_preview: Optional[str]    # Original content preview

    # Classification
    event_type: TimelineEventType
    labels: List[str]                 # Article 840 labels
    speaker: Optional[str]            # 원고/피고/제3자/unknown
    source_file: str                  # Original filename

    # Significance
    significance: int                 # 1-5 scale
    is_key_evidence: bool             # High importance flag

    # Metadata
    metadata: Dict[str, Any] = {}
```

```typescript
// TypeScript (frontend/src/types/timeline.ts)
export interface TimelineEvent {
    eventId: string;
    evidenceId: string;
    caseId: string;

    timestamp: string;  // ISO 8601
    date: string;       // YYYY-MM-DD
    time: string;       // HH:MM

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
```

### TimelineFilter

Filter criteria for timeline queries.

```python
# Python (backend/app/schemas/timeline.py)
class TimelineFilter(BaseModel):
    date_start: Optional[str] = None    # YYYY-MM-DD
    date_end: Optional[str] = None      # YYYY-MM-DD
    labels: Optional[List[str]] = None  # Filter by labels
    speakers: Optional[List[str]] = None # Filter by speakers
    event_types: Optional[List[TimelineEventType]] = None
    key_only: bool = False              # Show key evidence only

    # Pagination
    limit: int = 50                     # Max items per page
    offset: int = 0                     # Skip items

    # Sort
    sort_order: Literal["asc", "desc"] = "asc"  # Chronological order
```

```typescript
// TypeScript (frontend/src/types/timeline.ts)
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
```

### TimelineResult

API response container for timeline data.

```python
# Python (backend/app/schemas/timeline.py)
class TimelineResult(BaseModel):
    case_id: str
    events: List[TimelineEvent]

    # Pagination
    total_count: int                    # Total matching events
    filtered_count: int                 # After filters applied
    has_more: bool                      # More pages available

    # Statistics
    date_range: Dict[str, Optional[str]]  # {start, end}
    events_by_type: Dict[str, int]
    events_by_label: Dict[str, int]
    key_events_count: int

    # Meta
    generated_at: datetime
```

```typescript
// TypeScript (frontend/src/types/timeline.ts)
export interface TimelineResult {
    caseId: string;
    events: TimelineEvent[];

    totalCount: number;
    filteredCount: number;
    hasMore: boolean;

    dateRange: {
        start: string | null;
        end: string | null;
    };
    eventsByType: Record<string, number>;
    eventsByLabel: Record<string, number>;
    keyEventsCount: number;

    generatedAt: string;
}
```

## DynamoDB Schema Extension

The existing `leh_evidence` table already contains all required fields. No schema changes needed.

**Existing Fields Used**:
| Field | Type | Used For |
|:------|:-----|:---------|
| `evidence_id` | String | PK, maps to event_id |
| `case_id` | String | GSI partition key |
| `timestamp` | String (ISO) | Event time |
| `type` | String | Event type |
| `filename` | String | source_file |
| `ai_summary` | String | description |
| `content` | String | content_preview |
| `labels` | List[String] | labels |
| `speaker` | String | speaker |
| `article_840_tags` | Map | significance calculation |

## Significance Calculation

Significance score (1-5) is calculated from Article 840 labels:

```python
SIGNIFICANCE_WEIGHTS = {
    # Severity 5 (Critical)
    "부정행위": 5,
    "폭행": 5,
    "학대": 5,

    # Severity 4 (High)
    "유기": 4,
    "협박": 4,
    "위협": 4,
    "악의의유기": 4,

    # Severity 3 (Medium)
    "폭언": 3,
    "계속적_불화": 3,
    "혼인_파탄": 3,

    # Severity 2 (Low)
    "재산_문제": 2,
    "양육_문제": 2,
}

KEY_EVIDENCE_THRESHOLD = 4  # significance >= 4 is key evidence
```

## Relationships

```
┌─────────────┐     1:N      ┌──────────────┐
│    Case     │─────────────▶│   Evidence   │
│             │              │  (DynamoDB)  │
└─────────────┘              └──────┬───────┘
                                    │
                                    │ 1:1
                                    ▼
                             ┌──────────────┐
                             │TimelineEvent │
                             │  (computed)  │
                             └──────────────┘
```

## Validation Rules

| Field | Rule |
|:------|:-----|
| `timestamp` | Must be valid ISO 8601, nullable |
| `significance` | Integer 1-5, default 1 |
| `labels` | Array of valid Article840Category values |
| `speaker` | One of: 원고, 피고, 제3자, unknown, null |
| `limit` | Integer 1-100, default 50 |
| `offset` | Integer >= 0, default 0 |
| `date_start`, `date_end` | YYYY-MM-DD format |
