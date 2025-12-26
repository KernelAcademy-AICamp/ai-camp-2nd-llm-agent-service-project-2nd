# API Contract: Process Engine v2.14

## POST /cases/{caseId}/process/events
케이스에 이벤트를 적용하고, 상태 전이/데드라인/타임라인/이슈 재계산을 트리거한다.

Request
```json
{
  "machine_name": "CONSENSUAL_DIVORCE",
  "event_code": "ISSUE_CONFIRMATION_CERT",
  "occurred_at": "2025-12-01T10:00:00+09:00",
  "payload": {
    "confirmation_issued_at": "2025-12-01T10:00:00+09:00"
  }
}
```

Response
```json
{
  "case_id": "...",
  "machine_name": "CONSENSUAL_DIVORCE",
  "prev_state": "CONFIRMATION_SCHEDULED",
  "next_state": "CONFIRMED",
  "deadlines_created": ["CONSENSUAL_REPORT_DUE"],
  "warnings": [
    {"rule_id":"CNSL_REPORT_DUE_SOON","severity":"CRITICAL","message":"..."}
  ]
}
```

## GET /cases/{caseId}/process/state
현재 상태와 핵심 날짜, 다음 가능한 이벤트 목록을 반환.

## POST /cases/{caseId}/process/recompute
키 날짜 변경/데이터 마이그레이션 시, 상태/기한/경고를 재계산한다.
