# LSSP Document Auto-Generation Module v2.05

목표: detail/case 페이지에서 **절차 진행에 필요한 서류를 자동 생성(DOCX)** 하고,
생성된 문서는 “초안 탭/증거 정리 탭/타임라인” 데이터와 **동일한 Case 데이터 모델**을 사용한다.

## 지원 문서 타입 (v2.05)
- CONSENSUAL_INTENT_FORM: 협의이혼의사확인신청서 (부부 + 성년 증인 2인)
- CHILD_CUSTODY_AGREEMENT: 자녀 양육·친권자결정 협의서 (미성년 자녀/임신 포함 시)
- EVIDENCE_INDEX: 증거목록표(갑1~) (G1~G6 연결 + 파일상태 포함)
- ASSET_INVENTORY: 재산목록표(자산/채무) (재산분할·위자료 초안과 연결)
- CASE_TIMELINE_SUMMARY: 사실관계 요지서(타임라인 기반)

## UI/UX 연결
- detail/case > Documents 탭(신규)
  - 문서 타입 선택 → 미리보기(서버 렌더링) → DOCX 다운로드
  - 문서 생성 시점의 입력값 스냅샷(payload_json)을 document_instances에 저장
  - 각 문서에는 근거(citation) 링크가 포함될 수 있다(증거목록표는 필수).

## 데이터 원천
- parties / children / assets / debts / keypoints / evidence_files / timeline_events
- 문서 생성은 **case_id 하나로 재현 가능**해야 함 (idempotent).

## PDF 변환(옵션)
- DOCX → PDF는 운영환경에 LibreOffice or docx2pdf 등을 설치한 경우에만 제공(기본 OFF).


## 법적 로직(알림/제재)과 문서의 연결 포인트
- 협의이혼: 확인서 등본 수령 후 3개월 내 신고, 경과 시 **확인의 효력 상실** → 문서 생성 화면에서 “마감 D-10/D-3/D-1” 경고를 함께 노출.
- 재판상/조정 이혼: 확정일로부터 1개월 내 신고, 미신고 시 과태료(효력은 유지) → 대시보드에서 “과태료 리스크”로 표시.
