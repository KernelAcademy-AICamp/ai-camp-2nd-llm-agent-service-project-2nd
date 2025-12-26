# API Contract: Consultations v2.07

Base: /cases/{caseId}

## 1) Sessions
### POST /consultations/sessions
Create a session.
Request:
- channel, title?, started_at?, ended_at?, participants[], summary_text?, tags[]
Response: session

### GET /consultations/sessions
List sessions (order by started_at desc)
Query: limit, offset

### GET /consultations/sessions/{sessionId}
Get one session (includes counts)

### PATCH /consultations/sessions/{sessionId}
Update meta fields (title, started_at, ended_at, summary, tags)

## 2) Messages
### POST /consultations/sessions/{sessionId}/messages
Body: role, content, occurred_at?, attachments[]
Server should store:
- content_redacted (PII masked) for default UI rendering.

### GET /consultations/sessions/{sessionId}/messages
Query: limit, offset

## 3) Extracts
### POST /consultations/sessions/{sessionId}/extract
Run extraction (heuristic or LLM)
Options:
- mode=heuristic|llm
- overwrite=false|true
Response: {extracts[]}

### GET /consultations/sessions/{sessionId}/extracts
List extracts

### PATCH /consultations/extracts/{extractId}
Confirm/Dismiss + edit payload + attach source_spans

## 4) Promotions
### POST /consultations/extracts/{extractId}/promote/keypoint
Convert FACT extract to Keypoint (v2.03 keypoints) + create timeline event.
Hard rule: requires CONFIRMED + source_spans not empty.

### POST /consultations/extracts/{extractId}/promote/action-item
Convert ACTION_ITEM extract to case_action_items.

### POST /consultations/extracts/{extractId}/promote/evidence-request
Convert EVIDENCE_REQUEST extract to evidence_requests (+ checklist link optional).

## 5) Security
- default responses return content_redacted
- privileged flag (role-based) can return raw content; any raw access must log to consultation_audit_logs.
