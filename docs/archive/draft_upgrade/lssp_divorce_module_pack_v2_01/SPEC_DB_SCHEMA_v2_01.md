# SPEC_DB_SCHEMA_v2_01

> 아래는 기존 `cases / evidence / drafts` 구조에 '이혼 도메인'을 **최소 변경으로 덧씌우는** 설계입니다.  
> 이미 테이블이 있으면 이름만 매핑해서 쓰면 됩니다.

## 1) Case 확장: divorce_case_profile
- case_id (FK cases.id, PK)
- divorce_type ENUM('CONSENSUAL','JUDICIAL','DE_FACTO')
- has_minor_child BOOLEAN
- is_pregnant BOOLEAN
- jurisdiction_region TEXT (관할 법원 매핑 키)
- current_state TEXT (state machine code)
- guidance_received_at TIMESTAMPTZ NULL
- certificate_received_at TIMESTAMPTZ NULL
- finalized_at TIMESTAMPTZ NULL
- divorce_effective_at TIMESTAMPTZ NULL  # 협의=신고일, 재판=확정일
- created_at / updated_at

## 2) Deadline 엔진: case_deadlines
- id (PK)
- case_id (FK)
- rule_id TEXT            # DL-CONS-REPORT-3M 등
- trigger_event TEXT      # certificate_received_at 등
- trigger_at TIMESTAMPTZ
- deadline_at TIMESTAMPTZ
- severity ENUM('INFO','SOFT','HARD')
- status ENUM('OPEN','WARNED','MISSED','CLOSED')
- missed_effect TEXT      # EXPIRED / PENALTY_POSSIBLE
- last_notified_at TIMESTAMPTZ NULL
- metadata JSONB

## 3) Evidence 요구사항: evidence_requirements
- id (PK)
- ground_code TEXT        # G1~G6
- evidence_item_id TEXT   # EV-G1-COMM-001 등
- title TEXT
- category TEXT
- priority TEXT           # P0/P1/P2
- required BOOLEAN
- key_points JSONB        # 추적 포인트 템플릿
- notes TEXT

## 4) Evidence 실제 업로드: evidences (기존 테이블이 있으면 확장)
- id (PK)
- case_id (FK)
- requirement_id (FK, NULL)  # 어떤 요구사항을 충족하는지
- file_id / storage_key
- mime_type
- captured_at TIMESTAMPTZ NULL
- source ENUM('USER_UPLOAD','GENERATED','EXTERNAL_DOC')
- hash_sha256 TEXT           # chain-of-custody
- redact_status ENUM('RAW','REDACTED')
- created_at

## 5) Evidence → Fact 구조화: evidence_extracts
- id (PK)
- evidence_id (FK)
- extracted_json JSONB       # timeline/events/amounts/people/quotes
- confidence REAL
- created_at

## 6) Draft 작성 연결: draft_evidence_links
- id (PK)
- draft_id (FK)
- section_key TEXT           # "facts.02_affair_timeline" 같은 키
- evidence_id (FK)
- how_used TEXT              # "날짜-장소 입증", "폭행 빈도 입증" 등
- created_at

## API (제안)
- GET /cases/{id}/divorce/profile
- PATCH /cases/{id}/divorce/profile
- GET /cases/{id}/divorce/requirements?ground=G1
- POST /cases/{id}/evidence (업로드)
- POST /evidence/{id}/extract (구조화)
- GET /cases/{id}/divorce/timeline (state+deadlines)
- POST /cases/{id}/drafts/generate (requirements + extracts 기반)

## UI (detail/case 페이지 반영)
- 좌측: "절차 타임라인" (STATE, 다음 행동, 마감 카운트다운)
- 중앙: "증거 체크리스트" (P0 먼저, 충족률, 빈칸만 보여주기)
- 우측: "중요 포인트" (추출된 Fact 카드: 날짜/금액/인물/핵심 발언)
