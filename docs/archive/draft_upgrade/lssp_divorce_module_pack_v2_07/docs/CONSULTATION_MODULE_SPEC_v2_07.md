# LSSP / LEH Consultation Module v2.07

Purpose: turn 상담(상담/미팅/전화/카톡 상담) 기록을 **사건 진행 데이터**로 바꾼다.
- 상담 로그 -> (1) 쟁점(issues) (2) 사실(facts/keypoints) (3) 증거요청(evidence requests) (4) 할일(next actions) (5) 리스크/마감(warnings/deadlines)
- 모든 추출물(Extract)은 반드시 **근거(원문 message span / time span)** 를 가진다. 없으면 TODO로 남긴다.

## 1. UX 목표 (detail/case > Consultations 탭)
1) 세션 목록(좌): 상담별 카드(일시/채널/요약/태그/미처리 action 수)
2) 본문(중앙): 원문(전사/메모) + 하이라이트(추출된 span)
3) 추출물(우): Issues / Facts(Keypoints 후보) / Evidence Requests / Action Items / Risks
4) 원클릭 변환:
   - Fact -> Keypoint 생성(기존 v2.03 keypoints 테이블로) + 타임라인 이벤트 생성
   - Evidence Request -> Checklist 항목 생성/연결
   - Action Item -> NextActionsQueue 반영

## 2. 데이터 흐름
### 2.1 입력
- 상담 메모(텍스트), 전화/대면 요약, 채팅 로그(복사), 첨부파일(사진/서류)

### 2.2 처리 파이프라인(권장)
1) Ingest: Session + Messages 저장
2) Normalize: PII 자동 마스킹(전화번호/주민번호/계좌/주소 일부 등)
3) Extract:
   - Issue Extract (쟁점)
   - Fact Extract (사실/날짜/금액/행위)
   - Evidence Request Extract (필요 증거)
   - Task Extract (할 일)
   - Risk/Deadline Extract (기한/리스크)
4) Link:
   - extracts <-> messages (span)
   - extracts <-> grounds(G1~G6), issues, docs, evidence types
5) Publish:
   - action_items / evidence_requests / timeline_events / keypoints

## 3. 추출물(Extract) 종류와 규칙
### 3.1 Extract 공통 필드
- extract_id, case_id, session_id
- extract_type: ISSUE | FACT | EVIDENCE_REQUEST | ACTION_ITEM | RISK | DEADLINE | OTHER
- payload_json: type별 구조
- confidence: 0~1
- materiality: 0~100
- source_spans: [{message_id, start, end}] 또는 {timecode_start, timecode_end}
- status: TODO | CONFIRMED | DISMISSED
- linked_entities: (optional) keypoint_id, evidence_id, action_item_id, etc.

**Hard rule:** source_spans가 비어 있으면 status는 TODO로 고정.

### 3.2 Issue Extract payload
```json
{
  "issue_code": "CUSTODY|PROPERTY|ALIMONY|DV|ADULTERY|ABANDONMENT|VISITATION|INTERNATIONAL|DOCUMENTS|ETC",
  "title": "쟁점 제목",
  "summary": "한 줄 요약",
  "ground_tags": ["G1","G3"],
  "severity": "LOW|MED|HIGH"
}
```

### 3.3 Fact Extract payload (Keypoint 후보)
```json
{
  "kind": "DATE_EVENT|SPENDING|VIOLENCE|SEPARATION|ADMISSION|POLICE_CASE|MEDICAL|MISSING|OTHER",
  "what": "사실 문장(중립)",
  "when": "2025-12-01T00:00:00+09:00",
  "who": ["본인","상대","제3자?"],
  "where": "장소?",
  "amount": {"value": 500000, "currency": "KRW", "merchant": "가맹점?"},
  "ground_tags": ["G1"]
}
```

### 3.4 Evidence Request payload
```json
{
  "requested_for": "G1|G2|G3|G4|G5|G6|COMMON",
  "evidence_types": ["CHAT_EXPORT","CARD_STATEMENT","POLICE_RECORD"],
  "why": "왜 필요한지",
  "priority": "P0|P1|P2",
  "due_at": "optional"
}
```

### 3.5 Action Item payload
```json
{
  "title": "해야 할 일",
  "priority": "P0|P1|P2",
  "owner": "CLIENT|LAWYER|SYSTEM",
  "due_at": "optional",
  "depends_on": ["extract_id or evidence_type"],
  "notes": "optional"
}
```

### 3.6 Risk/Deadline payload
```json
{
  "risk_type": "DEADLINE|EVIDENCE_WEAK|CONTRADICTION|PII_RISK|OTHER",
  "message": "경고 문구",
  "severity": "WARN|CRITICAL",
  "due_at": "optional",
  "penalty_type": "EFFECT_LOSS|ADMIN_FINE|CLAIM_BARRED|NONE",
  "rule_id": "optional"
}
```

## 4. PII/민감정보 마스킹(운영 규칙)
- 전화번호/계좌/주민번호/주소(상세) 등은 저장 시 기본 마스킹
- 원문이 반드시 필요하면: 별도 권한(ADMIN/LAWYER) + 감사로그

## 5. 평가 지표
- 상담 1회 입력 후 자동 생성되는 Action Item 수
- Action Item의 완료율
- Extract -> Keypoint 전환율
- 증거 요청 충족도(Checklist satisfied%)

