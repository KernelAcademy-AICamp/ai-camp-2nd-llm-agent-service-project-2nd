# LSSP / LEH Divorce Module Pack v2.08
Key Issues Dashboard (주요쟁점 대시보드)

## What this adds
- case_issues + case_issue_links tables
- dashboard scoring (deadline/evidence/draft/procedure)
- API contract + FastAPI stubs
- seed taxonomy + scoring_rules

## Wiring
- Inputs: notification_rules, process_templates, evidence/keypoints, draft blocks, consultation action items
- Output: detail/case 상단 "주요쟁점" 카드 + 링크 점프

## Intended UI placement
detail/case 상단: 경고·알림 영역 아래(또는 최상단) + Top Issues 리스트
