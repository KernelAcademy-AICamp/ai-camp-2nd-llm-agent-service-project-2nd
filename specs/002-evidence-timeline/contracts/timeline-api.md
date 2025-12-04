# API Contract: Timeline

**Feature**: 002-evidence-timeline
**Date**: 2025-12-04
**Version**: 1.0.0

## Endpoints

### GET /cases/{case_id}/timeline

Retrieve evidence timeline for a case with optional filtering.

**Authentication**: Required (JWT)
**Authorization**: User must have VIEWER, MEMBER, or OWNER role on the case

#### Request

**Path Parameters**:
| Name | Type | Required | Description |
|:-----|:-----|:---------|:------------|
| `case_id` | string | Yes | Case UUID |

**Query Parameters**:
| Name | Type | Required | Default | Description |
|:-----|:-----|:---------|:--------|:------------|
| `date_start` | string | No | - | Filter start date (YYYY-MM-DD) |
| `date_end` | string | No | - | Filter end date (YYYY-MM-DD) |
| `labels` | string[] | No | - | Filter by Article 840 labels (comma-separated) |
| `speakers` | string[] | No | - | Filter by speaker (comma-separated: 원고,피고,제3자) |
| `event_types` | string[] | No | - | Filter by event type (comma-separated) |
| `key_only` | boolean | No | false | Show only key evidence |
| `limit` | integer | No | 50 | Items per page (1-100) |
| `offset` | integer | No | 0 | Pagination offset |
| `sort_order` | string | No | asc | Sort: "asc" (oldest first) or "desc" (newest first) |

**Example Request**:
```http
GET /cases/550e8400-e29b-41d4-a716-446655440000/timeline?labels=폭언,부정행위&key_only=true&limit=20
Authorization: Bearer <jwt_token>
```

#### Response

**Success (200 OK)**:
```json
{
  "case_id": "550e8400-e29b-41d4-a716-446655440000",
  "events": [
    {
      "event_id": "evt_abc123def456",
      "evidence_id": "ev_789xyz",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-03-15T14:30:00+09:00",
      "date": "2024-03-15",
      "time": "14:30",
      "description": "피고가 폭언을 사용한 카카오톡 메시지",
      "content_preview": "이 XXX이 뭘 알아? 당장 꺼져...",
      "event_type": "message",
      "labels": ["폭언", "혼인_파탄"],
      "speaker": "피고",
      "source_file": "kakao_2024.txt",
      "significance": 3,
      "is_key_evidence": false,
      "metadata": {}
    },
    {
      "event_id": "evt_def456ghi789",
      "evidence_id": "ev_456abc",
      "case_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-04-20T22:15:00+09:00",
      "date": "2024-04-20",
      "time": "22:15",
      "description": "불륜 현장 사진",
      "content_preview": null,
      "event_type": "image",
      "labels": ["부정행위"],
      "speaker": "피고",
      "source_file": "photo_20240420.jpg",
      "significance": 5,
      "is_key_evidence": true,
      "metadata": {
        "location": "서울시 강남구"
      }
    }
  ],
  "total_count": 150,
  "filtered_count": 2,
  "has_more": false,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "events_by_type": {
    "message": 120,
    "image": 15,
    "audio": 10,
    "video": 5
  },
  "events_by_label": {
    "폭언": 45,
    "부정행위": 3,
    "혼인_파탄": 12
  },
  "key_events_count": 5,
  "generated_at": "2025-12-04T10:30:00+09:00"
}
```

**Error Responses**:

| Status | Code | Description |
|:-------|:-----|:------------|
| 401 | `UNAUTHORIZED` | Missing or invalid JWT token |
| 403 | `FORBIDDEN` | User does not have access to case |
| 404 | `NOT_FOUND` | Case not found |
| 422 | `VALIDATION_ERROR` | Invalid query parameters |

**401 Unauthorized**:
```json
{
  "detail": "Not authenticated",
  "status_code": 401
}
```

**403 Forbidden**:
```json
{
  "detail": "You do not have access to this case",
  "status_code": 403
}
```

**404 Not Found**:
```json
{
  "detail": "Case not found",
  "status_code": 404
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["query", "date_start"],
      "msg": "Invalid date format. Use YYYY-MM-DD",
      "type": "value_error"
    }
  ],
  "status_code": 422
}
```

## TypeScript Client

```typescript
// frontend/src/lib/api/timeline.ts

import { TimelineResult, TimelineFilter } from '@/types/timeline';
import { apiClient } from './client';

export async function fetchTimeline(
  caseId: string,
  filter?: TimelineFilter
): Promise<TimelineResult> {
  const params = new URLSearchParams();

  if (filter?.dateStart) params.set('date_start', filter.dateStart);
  if (filter?.dateEnd) params.set('date_end', filter.dateEnd);
  if (filter?.labels?.length) params.set('labels', filter.labels.join(','));
  if (filter?.speakers?.length) params.set('speakers', filter.speakers.join(','));
  if (filter?.eventTypes?.length) params.set('event_types', filter.eventTypes.join(','));
  if (filter?.keyOnly) params.set('key_only', 'true');
  if (filter?.limit) params.set('limit', String(filter.limit));
  if (filter?.offset) params.set('offset', String(filter.offset));
  if (filter?.sortOrder) params.set('sort_order', filter.sortOrder);

  const queryString = params.toString();
  const url = `/cases/${caseId}/timeline${queryString ? `?${queryString}` : ''}`;

  const response = await apiClient.get<TimelineResult>(url);
  return response.data;
}
```

## React Hook

```typescript
// frontend/src/hooks/useTimeline.ts

import { useQuery } from '@tanstack/react-query';
import { fetchTimeline } from '@/lib/api/timeline';
import { TimelineFilter, TimelineResult } from '@/types/timeline';

export function useTimeline(caseId: string, filter?: TimelineFilter) {
  return useQuery<TimelineResult, Error>({
    queryKey: ['timeline', caseId, filter],
    queryFn: () => fetchTimeline(caseId, filter),
    staleTime: 30_000,  // 30 seconds
    enabled: !!caseId,
  });
}
```

## Audit Logging

All timeline access is logged to the `audit_logs` table:

```json
{
  "action": "TIMELINE_VIEW",
  "user_id": "user_123",
  "case_id": "case_456",
  "timestamp": "2025-12-04T10:30:00Z",
  "details": {
    "filters_applied": true,
    "labels_filter": ["폭언"],
    "events_returned": 25
  }
}
```
