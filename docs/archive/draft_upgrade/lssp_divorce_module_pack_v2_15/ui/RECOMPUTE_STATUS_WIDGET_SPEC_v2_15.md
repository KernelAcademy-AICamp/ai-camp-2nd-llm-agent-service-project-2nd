# UI Spec: Recompute Status Widget v2.15

## Placement
- `detail/case` 상단 오른쪽 (상태/타임라인 요약 옆)
- 변호사/스태프만 표시 (일반 의뢰인 계정에는 숨김)

## What to show
1) 최근 Job 1개 상태
   - 상태: Running / Succeeded / Failed / Skipped
   - 트리거: evidence_uploaded 등
   - 시작/종료 시간
   - 수행 step 수

2) Step breakdown (collapsed by default)
   - process_engine / timeline / evidence_keypoints / checklists / recommender / draft_preview / warnings
   - 각 step: status + metrics 요약(예: keypoints=12)

3) 실패 시 (critical)
   - error_message 1줄 요약
   - "해결 힌트" (예: confirmation_date 누락 → 프로세스 이벤트 입력 필요)

## Actions
- 버튼: "수동 재계산"
  - role: staff/lawyer
  - POST /cases/{case_id}/recompute { trigger_event: "manual_recompute" }
  - rate limit: case당 5분 1회

## Empty states
- Job 없음: "아직 재계산 이력이 없습니다. (첫 증거 업로드 후 자동 생성)"
