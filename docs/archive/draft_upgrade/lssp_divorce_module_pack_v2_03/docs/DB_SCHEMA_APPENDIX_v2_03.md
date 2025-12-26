# DB Schema Appendix v2.03 (Keypoint Tracking)

> v2.01/02의 기본 스키마에 '핵심포인트 추적'을 붙이기 위한 추가 테이블/필드 제안입니다.
> (이미 유사 테이블이 있으면 이름만 맞춰서 병합하세요.)

## 핵심 엔티티
- EvidenceFile: 업로드된 원본
- EvidenceExtract: 발췌(페이지/시간/메시지 범위)
- Keypoint: 원자적 사실
- KeypointLink: Keypoint ↔ Ground(G1~G6), Keypoint ↔ DraftBlock, Keypoint ↔ TimelineEvent 연결
- TimelineEvent: 사건/절차 이벤트(자동/수동)

## 추천 테이블 (PostgreSQL DDL 예시)

### 1) evidence_extracts
- 증거 파일의 특정 구간(근거 조각)
```sql
CREATE TABLE evidence_extracts (
  id              UUID PRIMARY KEY,
  case_id          UUID NOT NULL,
  evidence_file_id UUID NOT NULL,
  kind            TEXT NOT NULL,            -- page_range | time_range | message_range | manual_note
  locator         JSONB NOT NULL,           -- {"page_from":1,"page_to":3} / {"t_from_ms":...}
  extracted_text  TEXT NULL,                -- OCR/ASR/수기 요약(선택)
  created_by      UUID NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_extracts_case ON evidence_extracts(case_id);
CREATE INDEX ix_extracts_file ON evidence_extracts(evidence_file_id);
```

### 2) keypoints
```sql
CREATE TABLE keypoints (
  id            UUID PRIMARY KEY,
  case_id        UUID NOT NULL,
  title         TEXT NOT NULL,              -- 한 줄 요약
  statement     TEXT NOT NULL,              -- 법원이 읽을 수 있는 사실 서술(중립)
  occurred_at   DATE NULL,                  -- 사건일(최소 날짜)
  occurred_at_precision TEXT NOT NULL DEFAULT 'DATE', -- DATE|DATETIME|RANGE|UNKNOWN
  actors        JSONB NOT NULL DEFAULT '[]',-- [{"role":"spouse","name":"상대방"}]
  location      TEXT NULL,
  amount        NUMERIC NULL,
  currency      TEXT NULL DEFAULT 'KRW',
  type_code     TEXT NOT NULL,              -- keypoint_types.v2_03.json 참조
  status        TEXT NOT NULL DEFAULT 'DRAFT', -- DRAFT|READY|CONTESTED|EXCLUDED
  risk_flags    JSONB NOT NULL DEFAULT '[]', -- ["illegal_collection_suspected", ...]
  created_by    UUID NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_keypoints_case ON keypoints(case_id);
CREATE INDEX ix_keypoints_status ON keypoints(status);
```

### 3) keypoint_extract_links (M:N)
```sql
CREATE TABLE keypoint_extract_links (
  keypoint_id UUID NOT NULL,
  extract_id  UUID NOT NULL,
  PRIMARY KEY(keypoint_id, extract_id)
);
```

### 4) keypoint_ground_links (M:N)
```sql
CREATE TABLE keypoint_ground_links (
  keypoint_id UUID NOT NULL,
  ground_code TEXT NOT NULL, -- G1..G6
  element_tag TEXT NULL,     -- 예: "제척기간_인지일", "폭행_진단서"
  PRIMARY KEY(keypoint_id, ground_code, COALESCE(element_tag,''))
);
CREATE INDEX ix_kgl_ground ON keypoint_ground_links(ground_code);
```

### 5) timeline_events (자동/수동)
```sql
CREATE TABLE timeline_events (
  id        UUID PRIMARY KEY,
  case_id    UUID NOT NULL,
  event_date DATE NOT NULL,
  event_type TEXT NOT NULL,    -- process|fact|deadline|hearing|filing
  title     TEXT NOT NULL,
  payload   JSONB NOT NULL DEFAULT '{}',
  source    TEXT NOT NULL DEFAULT 'USER', -- USER|SYSTEM|AI
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_tl_case_date ON timeline_events(case_id, event_date);
```

### 6) keypoint_timeline_links (옵션)
```sql
CREATE TABLE keypoint_timeline_links (
  keypoint_id UUID NOT NULL,
  timeline_event_id UUID NOT NULL,
  PRIMARY KEY(keypoint_id, timeline_event_id)
);
```

## 데이터 정합성 규칙(서버에서 검증)
- Keypoint가 READY로 전환되려면:
  - occurred_at(또는 unknown 사유) + actors 1개 이상 + extract 링크 1개 이상 + ground_code 1개 이상
- 동일 Keypoint 중복 감지(권장):
  - (case_id, occurred_at, type_code, normalized(statement))의 유사도 기반 경고
