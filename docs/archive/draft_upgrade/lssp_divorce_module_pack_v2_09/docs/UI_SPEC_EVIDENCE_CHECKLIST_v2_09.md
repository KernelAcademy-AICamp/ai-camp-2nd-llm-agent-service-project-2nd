# UI Spec: Evidence Completeness Checklist (v2.09)

## Placement
`detail/case` page:
- Top: Warning/Alerts
- Tabs: 증거정리 / 핵심포인트 / 법적근거 / 타임라인 / 초안 / 문서

v2.09 focuses on **법적근거** tab + evidence request workflow.

## 법적근거 탭
### Ground Cards (G1~G6)
Each card shows:
- Status badge: OK / 부족 / 위험(제척기간)
- Progress bar: required_satisfied / required_total
- CTA: [체크리스트 보기] [누락 증거 요청 생성]

### Checklist Drawer (per ground)
Sections:
- CORE (필수) / OPTIONAL / ENHANCER
Rows:
- Item title + help text
- Needed count vs satisfied count
- Linked evidence chips (click → Evidence viewer)
- Linked keypoint chips (click → Keypoint viewer)
- Button: [요청 티켓 만들기] (only for required+MISSING)

## “누락 증거 요청” 버튼 동작
- For each missing required item:
  - if no OPEN ticket exists → create ticket with templated message
  - else → show “이미 요청됨”
- Template fields:
  - ground code/title
  - item title
  - recommended evidence types
  - suggested time range from timeline

## Evidence Upload 자동 제안 연결
When a file is uploaded:
- infer `evidence_type`
- suggest requirement item links (not final)
- user can approve → creates `case_requirement_item_links`

## Audit / Safety
- Any WAIVE requires reason (stored)
- Any SATISFIED from evidence requires evidence status REVIEWED/ADMISSIBLE
