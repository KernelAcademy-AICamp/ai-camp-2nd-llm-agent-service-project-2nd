# DATA_MODEL (v2.02)

## 1) 핵심 테이블(최소)
### Case
- id (uuid)
- user_id
- case_type: consensual | judicial | de_facto
- status: intake | evidence_collecting | drafting | filing | post_judgment | closed
- created_at, updated_at

### LegalGround (G1~G6)
- code (G1..G6)
- title, description
- proof_requirements_text
- limitation_rule (enum/JSON)

### CaseGround (케이스-사유 연결)
- case_id
- ground_code
- confidence_score (0~100)
- statute_deadline_date (nullable)
- deadline_reason (e.g., “인지일+6개월”)
- created_at

### EvidenceFile
- id
- case_id
- uploader_id
- original_filename, storage_url
- captured_at (evidence 발생일; 사용자 입력/메타에서 추출)
- status: unreviewed | reviewed | relevant | irrelevant
- tags: [ground_code, evidence_type, person, place...]
- extracted_facts (JSON)  # LLM/휴먼이 추출한 사실 주장

### KeyPoint
- id
- ground_code (nullable: 공통 쟁점용)
- title
- must_prove: boolean
- guidance_text

### EvidenceKeyPoint (근거-증거 연결)
- evidence_id
- keypoint_id
- strength: weak | medium | strong
- note

### Precedent
- id
- court, decision_date, case_no, source_url
- holding_summary
- factors (JSON)  # 적용요건/판단요소
- tags: [ground_code, limitation, property_division, etc.]

### DraftDoc
- id
- case_id
- doc_type: complaint | brief | agreement
- version
- content_md
- created_at

### DraftBlockLibrary
- id
- doc_type
- applies_to_tags: [G1..G6, property_division...]
- template_md
- required_keypoints: [keypoint_id...]
- precedent_refs: [precedent_id...]
- statute_refs: [law_ref...]

## 2) API 계약(초안)
- POST /cases/:id/evidence  (업로드 + 초기태깅)
- PATCH /evidence/:id/status
- POST /cases/:id/grounds/diagnose  (G1~G6 진단)
- POST /cases/:id/drafts/generate  (DraftBlock 조립)
- GET /cases/:id/timeline  (이벤트 스트림)
- POST /cases/:id/notifications/schedule  (deadline 기반 알림 등록)

## 3) 알림(Deadline/Penalty) 모델
notification_rules.json을 그대로 Rule 엔진으로 넣고,
- rule.trigger 발생 조건(이벤트/날짜)을 계산해서 schedule 등록
- penalty는 UI 배지/경고 문구에 즉시 반영
