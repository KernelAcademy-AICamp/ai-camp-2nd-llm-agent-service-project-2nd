# Draft Guardrails (v2.06)

## 1) Citation-First
- 어떤 문단이든 citations=0이면 “완성된 문단”으로 출력 금지.
- 반드시 TODO 블록으로 바꾸고, ‘필요한 증거/포인트’를 제시한다.

## 2) Date Discipline
- 날짜/기간은 keypoint.DATE_EVENT 또는 timeline_events에서만 가져온다.
- 사용자가 확정하지 않은 날짜는 “추정”으로만 표기.

## 3) Legal Reference
- 법조항/절차는 code-db(legal_refs.json)에서만 참조한다.
- 외부 판례 인용은 “요지/적용요소”만. 원문 장문 인용 금지.

## 4) Safety/Compliance
- 불법 증거수집을 유도하는 가이드는 제공하지 않는다.
- 폭력/상해는 비(非)그래픽으로만 요약 태그 처리.
