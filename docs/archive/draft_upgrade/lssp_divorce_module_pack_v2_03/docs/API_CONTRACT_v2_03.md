# API Contract v2.03 (Keypoint Tracking)

> detail/case 페이지 구현을 위한 최소 계약입니다. 경로/인증은 프로젝트 규칙에 맞춰 조정.

## 1) Evidence Extract
### POST /api/cases/{caseId}/evidence/{fileId}/extracts
Request
```json
{
  "kind": "page_range",
  "locator": {"page_from": 1, "page_to": 3},
  "extracted_text": "선택(OCR 결과 또는 수기 요약)"
}
```
Response: 201 `{ "id": "...", ... }`

### GET /api/cases/{caseId}/extracts?fileId=
Response
```json
[{ "id":"...", "kind":"page_range", "locator":{...}, "created_at":"..." }]
```

## 2) Keypoint
### POST /api/cases/{caseId}/keypoints
Request
```json
{
  "title": "모텔 결제 내역",
  "statement": "2024-03-12 배우자가 숙박업소 결제를 했다.",
  "occurred_at": "2024-03-12",
  "occurred_at_precision": "DATE",
  "actors": [{"role":"spouse","name":"상대방"}],
  "location": "서울 ○○구",
  "amount": 120000,
  "type_code": "FINANCE_SPEND",
  "ground_links": [{"ground_code":"G1","element_tag":"금융_카드내역"}],
  "extract_ids": ["uuid-1", "uuid-2"]
}
```
Response: 201 `{ "id":"...", "status":"DRAFT" }`

### PATCH /api/cases/{caseId}/keypoints/{keypointId}
- status 전환(DRAFT→READY 등), 문구 수정, 링크 추가/삭제
```json
{ "status": "READY" }
```

### GET /api/cases/{caseId}/keypoints?ground=G1&status=READY
Response
```json
[
  {
    "id":"...",
    "title":"...",
    "statement":"...",
    "occurred_at":"2024-03-12",
    "actors":[...],
    "status":"READY",
    "ground_links":[...],
    "extracts":[...]
  }
]
```

## 3) Timeline (연동)
### POST /api/cases/{caseId}/timeline/events (user event)
```json
{ "event_date":"2024-03-12", "event_type":"fact", "title":"모텔 결제", "payload":{"keypoint_id":"..."} }
```

### GET /api/cases/{caseId}/timeline
- process + deadline + fact 이벤트를 날짜순으로 반환

## 4) Suggest (선택, AI 워커)
### POST /api/cases/{caseId}/keypoints/suggest
- 입력: extract_id 목록
- 출력: Keypoint draft 배열 (항상 DRAFT로만 생성, 유저 승인 필요)
