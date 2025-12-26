-- v2.10 Keypoint Extraction Pipeline
-- Note: assumes you already have evidences, evidence_extracts, keypoints (v2.03+).

CREATE TABLE IF NOT EXISTS keypoint_rules (
  rule_id           BIGSERIAL PRIMARY KEY,
  version           VARCHAR(20) NOT NULL DEFAULT 'v2.10',
  evidence_type     VARCHAR(40) NOT NULL,
  kind              VARCHAR(40) NOT NULL,
  name              VARCHAR(120) NOT NULL,
  pattern           TEXT NOT NULL,
  flags             VARCHAR(40) DEFAULT '',
  value_template    JSONB NOT NULL DEFAULT '{}'::jsonb,
  ground_tags       TEXT[] DEFAULT ARRAY[]::TEXT[],
  base_confidence   NUMERIC(4,3) NOT NULL DEFAULT 0.500,
  base_materiality  INT NOT NULL DEFAULT 40,
  is_enabled        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS keypoint_extraction_runs (
  run_id        BIGSERIAL PRIMARY KEY,
  case_id       UUID NOT NULL,
  evidence_id   UUID NOT NULL,
  extractor     VARCHAR(40) NOT NULL DEFAULT 'rule_based',
  version       VARCHAR(20) NOT NULL DEFAULT 'v2.10',
  status        VARCHAR(20) NOT NULL DEFAULT 'DONE',
  started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  meta          JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS keypoint_candidates (
  candidate_id     BIGSERIAL PRIMARY KEY,
  case_id          UUID NOT NULL,
  evidence_id      UUID NOT NULL,
  extract_id       UUID NULL,
  rule_id          BIGINT NULL REFERENCES keypoint_rules(rule_id),
  kind             VARCHAR(40) NOT NULL,
  value            JSONB NOT NULL DEFAULT '{}'::jsonb,
  ground_tags      TEXT[] DEFAULT ARRAY[]::TEXT[],
  confidence       NUMERIC(4,3) NOT NULL DEFAULT 0.500,
  materiality      INT NOT NULL DEFAULT 40,
  source_span      JSONB NOT NULL DEFAULT '{}'::jsonb,
  status           VARCHAR(20) NOT NULL DEFAULT 'CANDIDATE',
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keypoint_candidates_case ON keypoint_candidates(case_id);
CREATE INDEX IF NOT EXISTS idx_keypoint_candidates_evidence ON keypoint_candidates(evidence_id);

CREATE TABLE IF NOT EXISTS keypoint_merge_groups (
  group_id     BIGSERIAL PRIMARY KEY,
  case_id      UUID NOT NULL,
  kind         VARCHAR(40) NOT NULL,
  canonical_keypoint_id UUID NULL,
  candidate_ids BIGINT[] NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS keypoint_candidate_links (
  candidate_id BIGINT PRIMARY KEY REFERENCES keypoint_candidates(candidate_id),
  keypoint_id  UUID NOT NULL,
  linked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
