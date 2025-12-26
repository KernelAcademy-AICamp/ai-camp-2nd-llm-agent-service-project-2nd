# API Contract v2.13 - Timeline

## GET /cases/{case_id}/timeline
Query:
- category?: PROCEDURE|EVIDENCE|FACT|DEADLINE|CONSULTATION|SYSTEM
- from?: ISO8601 datetime
- to?: ISO8601 datetime
- include_links?: bool (default true)
- limit?: int (default 200)

Response:
{
  "case_id": "...",
  "items": [
    {
      "id": 123,
      "category": "DEADLINE",
      "event_type": "DEADLINE_DUE",
      "title": "...",
      "summary": "...",
      "occurred_at": "...",
      "severity": 4,
      "risk_score": 92.5,
      "penalty_type": "EFFECT_LOSS",
      "links": {
        "evidence_id": null,
        "keypoint_id": null,
        "draft_block_id": null,
        "issue_id": "..."
      },
      "tags": ["G1","REPORTING"],
      "meta": { "rule_id": "CONSENSUAL_CERT_EXPIRES", "due_at": "..." }
    }
  ]
}

## POST /cases/{case_id}/timeline/events
Create a manual event (user/admin).
Body:
{
  "category": "...",
  "event_type": "...",
  "title": "...",
  "summary": "...",
  "occurred_at": "...",
  "start_at": null,
  "end_at": null,
  "tags": [],
  "meta": {},
  "links": { "evidence_id": "...", "keypoint_id": "..." }
}

## POST /cases/{case_id}/timeline/recompute
Rebuild timeline derived events:
- deadlines from notification_rules + case key dates
- procedure transitions from case state/stage
- approved keypoints promoted to FACT events
- evidence status changes to EVIDENCE events
- consultation extracts to CONSULTATION events
Body:
{
  "mode": "INCREMENTAL" | "FULL",
  "since": "ISO8601 datetime|null"
}
Response:
{
  "created": 12,
  "updated": 5,
  "deleted": 3
}

## Scoring rules (server-side)
- deadline risk is based on days_to_due, penalty_type, and whether user confirmed the key date
- evidence/fact events have risk_score = 0 unless they influence a deadline/issue

