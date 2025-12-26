# v2.08 UI Spec: Key Issues Dashboard (detail/case 상단)

## Layout
A) 상단 스트립(고정): 경고·알림(Deadlines/제척기간/서류누락)
B) 4개의 Health Card:
- Deadline Risk (0~100)
- Evidence Completeness (0~100)
- Draft Completeness (0~100)
- Procedure Progress (0~100)
C) "Top Issues" 리스트(최대 7개): severity desc, due_at asc

## Issue Card
- Badge: group (DEADLINE/EVIDENCE/CHILD/PROPERTY/DRAFT/PROCEDURE)
- Severity bar (0~100)
- Due date + Penalty label (효력상실/과태료/청구기각)
- CTA:
  - "근거 보기" → issue_links로 evidence/keypoint/event/draft_block/consult_extract jump
  - "해결로 표시" / "무시" / "검토됨"

## Linking behavior
- EVIDENCE issue → 해당 Gk 폴더로 이동 + 필수 증거/키포인트 체크리스트 강조
- DEADLINE issue → 타임라인 이벤트로 이동 + 알림 설정 표시
- DRAFT issue → 초안 탭의 해당 블록으로 이동 (citation 0개 강조)
- CHILD issue → 양육자/친권/양육비/면접교섭 입력 폼/문서 탭으로 이동
- PROPERTY issue → 자산/채무 입력 폼 + 재산목록표 문서 탭으로 이동

## Scoring
- deadline_risk: 가장 임박한 due_at 기준 (D-0이면 100, D-30이면 30 등), penalty_type 가중치
- evidence_completeness: (필수 evidence_types 충족률 * 0.6) + (필수 keypoints 충족률 * 0.4)
- draft_completeness: (완성 블록 / 전체 블록) * 100
- procedure_progress: process_templates steps 중 완료 체크 비율
