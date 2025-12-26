# UI Spec: Process Stage Widget v2.14

## 목적
detail/case 상단에 "절차 진행도 + 다음 해야 할 일 + 막힌 것 + 마감"을 한 줄로 보여준다.

## 구성
1) Stage Chips (현재 state 강조)
2) Next Actions (가능 이벤트 버튼)
3) Blockers (Missing Step Warnings)
4) Deadlines Strip (EFFECT_LOSS / ADMIN_FINE / CLAIM_BARRED 분리 색상은 UI에서)

## 상호작용
- 칩 클릭: 관련 타임라인 이벤트 필터링
- Blocker 클릭: 입력폼/해당 탭으로 점프
- Next Action 클릭: 이벤트 적용(POST /process/events)
