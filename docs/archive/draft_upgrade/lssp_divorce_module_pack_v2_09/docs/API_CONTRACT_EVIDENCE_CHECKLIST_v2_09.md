# Evidence Checklist & Requests API (v2.09)

This module turns **evidence storage** into an **evaluated checklist** per G1~G6.
- Upload evidence → auto-tag suggestion
- Review evidence → counts toward SATISFIED
- Missing required items → one-click generate evidence request tickets

## Entities (assumes existing)
- `evidences` (id, case_id, evidence_type, status, captured_at, tags, ...)
- `keypoints` (id, case_id, kind, occurred_at, ...)

New (v2.09)
- `evidence_requirement_sets`, `evidence_requirement_items`
- `case_requirement_item_status`, `case_requirement_item_links`
- `case_evidence_requests`

## Endpoints

### GET /cases/{caseId}/evidence-checklist
Query:
- `grounds=G1,G3` (optional)
- `include_links=true|false` (default true)

Response (shape)
```json
{
  "case_id":"...",
  "computed_at":"2025-12-17T00:00:00Z",
  "by_ground":[
    {
      "code":"G1",
      "title":"...",
      "score":70,
      "required_total":4,
      "required_satisfied":3,
      "items":[
        {
          "item_key":"G1_CHAT_EXPORT",
          "title":"통신 기록 확보",
          "is_required":true,
          "status":"PARTIAL",
          "required_min_count":1,
          "satisfied_count":0,
          "suggested_links":[{"evidence_id":"...","reason":"evidence_type=CHAT_EXPORT"}],
          "links":[{"evidence_id":"..."}]
        }
      ]
    }
  ],
  "overall_score":63,
  "missing_required":[{"ground":"G1","item_key":"G1_FINANCE","title":"금융 내역 정황"}]
}
```

### POST /cases/{caseId}/evidence-checklist/evaluate
Body:
```json
{
  "create_requests": true,
  "request_due_days": 7
}
```
Behavior:
- recompute `case_requirement_item_status`
- if `create_requests=true`, create `case_evidence_requests` for required items that are MISSING
  (skip if existing OPEN/IN_PROGRESS request exists)

### POST /cases/{caseId}/evidence-requests
Body:
```json
{
  "requirement_item_id": 123,
  "title":"카드 명세서 확보 요청",
  "message":"모텔/선물 지출 정황이 확인되는 카드/계좌 자료가 필요합니다. (기간: 2025-09~2025-12)",
  "due_at":"2025-12-24T00:00:00Z"
}
```

### PATCH /cases/{caseId}/evidence-checklist/items/{requirementItemId}/waive
Body:
```json
{"reason":"상대방이 자료제출 거부 / 대체 증거로 충족 예정"}
```
Sets status to `WAIVED` (still visible in UI for audit).

## Evaluation Rules (default)
- Evidence counts only if status ∈ `allowed_evidence_statuses` (default: ADMISSIBLE/REVIEWED)
- Requirement is:
  - SATISFIED if satisfied_count ≥ required_min_count
  - PARTIAL if 0 < satisfied_count < required_min_count
  - MISSING if satisfied_count = 0
- Satisfied_count can be computed by:
  - linked evidences (by evidence_type/tag) + linked keypoints (by kind)
  - keypoints are the “fact atoms”; evidence is the “proof container”
