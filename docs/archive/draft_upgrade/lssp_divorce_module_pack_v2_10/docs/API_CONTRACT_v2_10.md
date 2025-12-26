# API Contract v2.10 — Keypoint Pipeline

## Extract candidates
POST /cases/{caseId}/evidences/{evidenceId}/keypoints/extract
Request: { "extract_id": "uuid|null", "mode": "rule_based", "evidence_type": "CHAT_EXPORT|..." }

## Review candidates
GET /cases/{caseId}/keypoints/candidates?status=CANDIDATE&evidence_id=...

## Accept/Reject/Edit
PATCH /cases/{caseId}/keypoints/candidates/{candidateId}

## Promote to canonical keypoints (with optional merge)
POST /cases/{caseId}/keypoints/promote
