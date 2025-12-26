# v2.08 API Contract: Issues Dashboard (Key Issues)

목표: detail/case 상단에 "주요쟁점"을 카드/리스트로 보여주고, 클릭 시 근거(증거/키포인트/이벤트/초안블록/상담발췌)로 점프.

## Endpoints

### GET /cases/{case_id}/dashboard
Return:
- scores: deadline_risk, evidence_completeness, draft_completeness, procedure_progress, child_issues, property_issues
- counters: evidences, keypoints, open_issues, due_soon_issues
- top_issues: severity desc, due_at asc

```json
{
  "case_id": "uuid",
  "scores": {
    "deadline_risk": 80,
    "evidence_completeness": 55,
    "draft_completeness": 30,
    "procedure_progress": 40
  },
  "counters": {
    "evidences": 12,
    "keypoints": 48,
    "open_issues": 7,
    "due_soon": 2
  },
  "top_issues": [
    {
      "issue_id": "uuid",
      "issue_code": "DEADLINE_REPORTING",
      "issue_group": "DEADLINE",
      "severity": 95,
      "status": "OPEN",
      "title": "이혼신고 기한 임박",
      "summary": "판결확정일 기준 1개월 신고 기한이 7일 남았습니다.",
      "due_at": "2026-01-05T00:00:00Z",
      "penalty_type": "ADMIN_FINE",
      "related_ground_code": null
    }
  ]
}
```

### GET /cases/{case_id}/issues?status=OPEN&group=EVIDENCE
List issues (filters: status, group, ground_code, due_before)

### POST /cases/{case_id}/issues/recompute
서버가 아래 신호들을 기반으로 이슈를 재생성/갱신:
- notification_rules + case_dates
- ground_satisfaction score(G1~G6) + evidence/keypoints
- draft block completeness
- consultation action items / evidence requests
Return: number created/updated/resolved

### PATCH /cases/{case_id}/issues/{issue_id}
Body:
- status: ACKED|RESOLVED|DISMISSED
- note (optional)

### GET /cases/{case_id}/issues/{issue_id}/links
Return linked references (type+ref_id) + summary for UI.

## Server-side rules (요지)
- DEADLINE: notification_rules의 trigger가 생성하는 due_at + penalty_type 기반.
- EVIDENCE: 각 G1~G6 템플릿(필수 증거 타입/필수 keypoint)이 부족하면 OPEN.
- DRAFT: Citation 없는 블록이 남아있으면 OPEN.
- CHILD: 양육자/친권/양육비/면접교섭 관련 입력/증거/합의서 누락 시 OPEN.
- PROPERTY: 적극/소극재산 입력 누락, 특유재산 주장 근거 부족 등.
