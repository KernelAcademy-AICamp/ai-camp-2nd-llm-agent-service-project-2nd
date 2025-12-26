# Draft Engine Spec v2.04

## 0) 목표
- 사용자가 케이스(detail/case)에서 **증거 업로드 → 핵심포인트(Keypoint) 정리 → 초안(문서) 생성**까지 한 화면에서 진행
- 초안은 ‘문단 블록(Block)’ 단위로 조립되며, 각 블록은 **필요한 Keypoint / Evidence / TimelineEvent 조건**을 갖는다.
- 생성 결과는 (1) 화면에서 수정 가능, (2) 내보내기(DOCX/HWP)는 별도 어댑터로 처리.

---

## 1) 핵심 개념

### 1.1 DraftTemplate (문서 타입 템플릿)
- 예: `PETITION_DIVORCE`(이혼소장), `MEDIATION_APP`(조정신청서), `BRIEF_PREP`(준비서면),
  `EVIDENCE_LIST`(증거목록), `CHILD_CUSTODY_PLAN`(양육계획서), `PROPERTY_LIST`(재산목록)
- 템플릿은 섹션/블록 순서를 정의(‘표준 골격’).

### 1.2 DraftBlock (문단/블록)
- `text_template`: 변수 치환 템플릿(예: “피고는 {date}경 {action} 하였습니다.”)
- `required_keypoints`: 이 블록을 자동 생성하기 위한 Keypoint type_code 목록
- `required_evidence_tags`: 최소 요구 증거 태그(예: “진단서”, “112신고”, “카톡대화”)
- `conditions`: 포함/제외 조건(간단한 표현식)
- `legal_refs`: 관련 법조항/요건 태그(표시용)

### 1.3 Draft (케이스별 문서 인스턴스)
- 템플릿 기반으로 생성되며, 생성 후 **블록 단위로 편집/삭제/추가** 가능.
- “자동 생성”은 초안 1차 제출용, 최종 제출용이 아님(UX에서 강하게 표기).

### 1.4 Citation (근거 연결)
- `DraftBlockInstance` ↔ `Keypoint` ↔ `EvidenceExtract`
- 화면에서 “이 문단이 어떤 증거에서 왔는지” 바로 이동 가능해야 한다.

---

## 2) 생성 알고리즘 (결정적, 재현 가능)

### Step A — Input Assemble
- CaseContext:
  - Case type: 협의/재판/사실혼
  - Legal grounds: G1..G6 (복수)
  - Parties/children/assets summary
- Keypoints: status=READY 우선, DRAFT는 낮은 신뢰
- EvidenceExtracts: keypoint에 링크된 extract가 우선

### Step B — Template → Blocks 후보 생성
- DraftTemplate의 section 순서대로 블록 후보를 열거

### Step C — Block Inclusion 판단
- 조건 충족(conditions) AND
- required_keypoints 충족(해당 type_code keypoint ≥ N)
- required_evidence_tags 충족(증거 태그 또는 extract 유형)

충족하면:
- 블록 변수 값을 Keypoint에서 채움(occurred_at, amount, actors, statement 등)
- 블록 인용(Citation) 생성

불충족하면:
- (기본) 블록 생략
- (옵션) “TODO 블록”을 생성하여 누락 항목을 사용자에게 보여줌

### Step D — Precedent 추천(선택)
- Ground + BlockTag 기반으로 precedent 후보 3~5개 추천
- precedent는 **문장에 직접 인용하지 않고** “참고” 영역으로 표시

### Step E — Coverage Score
- 블록별: (필수 keypoint 충족 여부, extract 존재, 날짜/금액 등 핵심필드 존재)로 0~100
- 문서 전체: 블록 가중치 합산
- Coverage < 70이면 “제출 금지 배너”를 띄워야 함

---

## 3) 안전장치 (허위 사실/위조 방지)
- DraftBlockInstance에는 반드시 `source_keypoint_ids` 또는 `source_extract_ids`가 1개 이상 존재
- LLM 사용 시에도 “사실 생성 금지” 룰을 시스템 레벨에서 강제:
  - 없는 날짜/금액/행위는 `{UNKNOWN}` 또는 `[추가 확인 필요]`로 남김
- 사용자가 “증거 조작/위조”를 요청하면 생성 경로 차단

---

## 4) Export Adapter
- Draft는 내부적으로 “블록 + 변수 + 인용” 구조로 저장
- Export 단계에서:
  - docx: block 순서대로 paragraph 생성, 각주/주석에 citation 넣기
  - hwp: v1은 PDF/Docx 변환로 우회, v2에서 hwpers/hwp-bridge로 본격 대응
