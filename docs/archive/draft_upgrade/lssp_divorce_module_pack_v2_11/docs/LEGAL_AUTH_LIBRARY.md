# Legal Authority Library v2.11

목표: detail/case의 **법적근거 탭**과 **초안(Draft Builder)**이 동일한 “근거 라이브러리”를 공유하도록 만든다.

## 1) 왜 필요한가
- 초안 문단은 반드시 **근거(Citation)**를 가져야 한다.
- 근거는 크게 2종류:
  1) 법령/판례/가이드(Authority)
  2) 사건 증거(Evidence) + 핵심포인트(Keypoint)

## 2) 데이터 구조(요약)
- `legal_authorities` : 법령/판례/가이드 메타데이터
- `legal_authority_snippets` : 조문/요지의 “짧은 발췌” 저장(핀포인트)
- `draft_citations` (기존) : 초안 블록 인용(법령/증거 모두 지원하도록 확장)

## 3) 인용(Citation) 포맷 표준
- 법령: `[법] 민법 제840조` 처럼 **코드+조문**을 고정 표시
- 증거: `[증거] 갑1 카카오톡 대화(YYYY-MM-DD)` 처럼 **갑호+타입+날짜** 고정 표시
- 핀포인트(발췌):
  - 조문/판례 텍스트를 길게 복사하지 않는다(최대 25단어 권장).
  - `snippet`은 반드시 `source_ref`(출처 식별자)와 함께 저장한다.

## 4) 법적근거 탭(UX 규칙)
- G1~G6 각 카드에:
  - 관련 조문 자동 노출(ground_to_authorities_map)
  - 제척기간/요건 입력필드(인지일/발생일 등) + 계산 결과
  - “초안에 삽입” 버튼 → Draft Builder 블록에 Authority Citation 추가
- 국제/가정폭력/양육비 이행확보는 별도 섹션으로 노출

## 5) 확장 지점
- 판례(KR Supreme Court 등)를 추가하려면 `kind=PRECEDENT`로 확장하고,
  `elements[]`(적용요소) + `holding_summary`(요지) + `source_ref`를 저장한다.
