# API Contract — Draft Builder v2.06

## POST /cases/{case_id}/drafts/generate
### request
{
  "draft_kind": "JUDICIAL_COMPLAINT | MEDIATION_REQUEST | CONSENSUAL_AGREEMENT",
  "selected_claims": ["DIVORCE", "ALIMONY", "PROPERTY_DIVISION", "CUSTODY", "CHILD_SUPPORT"],
  "selected_grounds": ["G1", "G3"],
  "options": {
    "tone": "NEUTRAL | FIRM",
    "include_timeline_table": true,
    "require_admissible_only": true
  }
}

### response
{
  "draft_id": "...",
  "status": "COMPLETE | INCOMPLETE",
  "warnings": [
    {"code":"DEADLINE_SOON","message":"...","ref":"timeline_event_id"},
    {"code":"LIMITATION_SOON","message":"...","ref":"ground_code"}
  ],
  "blocks": [
    {
      "block_id": "facts_timeline_summary",
      "title": "사실관계 요약",
      "html": "<p>...</p>",
      "citations": [
        {"evidence_id":"...","extract_id":"...","keypoint_id":"...","label":"갑 제1호증"}
      ],
      "missing": []
    }
  ]
}

## GET /cases/{case_id}/drafts/{draft_id}
- 저장된 초안 조회(블록/근거/누락/경고)

## PATCH /cases/{case_id}/drafts/{draft_id}/blocks/{block_instance_id}
- 블록 수동 편집(사용자 수정본 저장)
