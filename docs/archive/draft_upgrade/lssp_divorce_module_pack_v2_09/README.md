# LSSP Divorce Module Pack v2.09
## Evidence Completeness Checklist + Missing Evidence Requests

### What this adds
- G1~G6별 **증거 체크리스트(필수/선택)**를 DB에 시드로 넣고,
- 케이스의 evidence/keypoints 상태를 읽어서 **MISSING/PARTIAL/SATISFIED**로 자동 평가,
- 필수 항목이 비면 **누락 증거 요청 티켓**을 자동 생성합니다.

### Key UX outcomes
- 증거 정리 탭이 '보관'이 아니라 '진행률'이 됩니다.
- 초안/대시보드가 근거 없는 문장을 못 뱉습니다(충족도 기반).

### Apply
1) Run DB migration: `docs/DB_DDL_EVIDENCE_CHECKLIST_v2_09.sql`
2) Seed:
   - `data/requirement_sets.v2_09.json`
   - `data/requirement_item_rules.v2_09.json`
3) Implement endpoints per `docs/API_CONTRACT_EVIDENCE_CHECKLIST_v2_09.md`
4) Wire UI per `docs/UI_SPEC_EVIDENCE_CHECKLIST_v2_09.md`

### Notes
- Evidence auto-linking is *suggestion-only* until review (검토완료/증거적합).
