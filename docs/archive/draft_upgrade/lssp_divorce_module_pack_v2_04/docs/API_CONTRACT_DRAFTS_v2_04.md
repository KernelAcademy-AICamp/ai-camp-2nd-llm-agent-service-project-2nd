# API Contract — Drafts v2.04 (REST)

## Draft Templates
- GET /api/draft-templates
- GET /api/draft-templates/{template_id}

## Create Draft (Generate)
- POST /api/cases/{case_id}/drafts
Body:
{
  "template_id": "PETITION_DIVORCE",
  "ground_codes": ["G1","G3"],
  "options": {
    "include_todo_blocks": true,
    "max_precedents": 5
  }
}

Response:
{
  "draft_id": "...",
  "coverage_score": 74,
  "sections": [...]
}

## Draft CRUD
- GET /api/cases/{case_id}/drafts
- GET /api/drafts/{draft_id}
- PATCH /api/drafts/{draft_id}   (title, meta)
- DELETE /api/drafts/{draft_id}

## Block Instances
- PATCH /api/drafts/{draft_id}/blocks/{block_instance_id}
Body: { "text": "...", "status": "EDITED", "citations": [...] }

- POST /api/drafts/{draft_id}/blocks   (append custom block)
- DELETE /api/drafts/{draft_id}/blocks/{block_instance_id}

## Citations
- GET /api/drafts/{draft_id}/citations
- POST /api/drafts/{draft_id}/citations
Body: { "block_instance_id":"...", "keypoint_id":"...", "extract_id":"..." }

## Export
- POST /api/drafts/{draft_id}/export
Body: { "format":"DOCX" | "PDF" | "HWP" }
