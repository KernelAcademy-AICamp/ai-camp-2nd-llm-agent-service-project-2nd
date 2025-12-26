-- LSSP / LEH: Evidence Completeness Checklist v2.09
-- Postgres 14+ (jsonb, generated columns optional)
-- NOTE: If you already have similarly named tables, rename with suffix _v2_09.

DO $$ BEGIN
  CREATE TYPE requirement_status AS ENUM ('MISSING','PARTIAL','SATISFIED','WAIVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS evidence_requirement_sets (
  id                BIGSERIAL PRIMARY KEY,
  code              TEXT NOT NULL UNIQUE,      -- e.g., 'G1'
  title             TEXT NOT NULL,
  description       TEXT,
  priority          INT  NOT NULL DEFAULT 100,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_requirement_items (
  id                BIGSERIAL PRIMARY KEY,
  set_id            BIGINT NOT NULL REFERENCES evidence_requirement_sets(id) ON DELETE CASCADE,
  item_key          TEXT NOT NULL,                 -- stable key e.g., 'G1_CHAT_EXPORT'
  title             TEXT NOT NULL,
  description       TEXT,
  required_min_count INT NOT NULL DEFAULT 1,       -- how many evidences/keypoints needed
  evidence_types    TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  keypoint_kinds    TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  allowed_evidence_statuses TEXT[] NOT NULL DEFAULT ARRAY['ADMISSIBLE','REVIEWED']::TEXT[],
  is_required       BOOLEAN NOT NULL DEFAULT TRUE,
  weight            INT NOT NULL DEFAULT 10,       -- for scoring
  ui_group          TEXT NOT NULL DEFAULT 'CORE',  -- 'CORE'|'OPTIONAL'|'ENHANCER'
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(set_id, item_key)
);

CREATE TABLE IF NOT EXISTS case_requirement_item_status (
  case_id           UUID NOT NULL,
  requirement_item_id BIGINT NOT NULL REFERENCES evidence_requirement_items(id) ON DELETE CASCADE,
  status            requirement_status NOT NULL DEFAULT 'MISSING',
  satisfied_count   INT NOT NULL DEFAULT 0,
  last_evaluated_at TIMESTAMPTZ,
  note              TEXT,
  PRIMARY KEY(case_id, requirement_item_id)
);

CREATE TABLE IF NOT EXISTS case_requirement_item_links (
  id                BIGSERIAL PRIMARY KEY,
  case_id           UUID NOT NULL,
  requirement_item_id BIGINT NOT NULL REFERENCES evidence_requirement_items(id) ON DELETE CASCADE,
  evidence_id       UUID,  -- FK to evidences table (existing)
  keypoint_id       UUID,  -- FK to keypoints table (existing)
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (evidence_id IS NOT NULL OR keypoint_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_cril_case ON case_requirement_item_links(case_id);
CREATE INDEX IF NOT EXISTS idx_cris_case ON case_requirement_item_status(case_id);

-- Evidence request tickets generated from missing requirements
DO $$ BEGIN
  CREATE TYPE evidence_request_status AS ENUM ('OPEN','IN_PROGRESS','DONE','CANCELLED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS case_evidence_requests (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id            UUID NOT NULL,
  requirement_item_id BIGINT REFERENCES evidence_requirement_items(id) ON DELETE SET NULL,
  title             TEXT NOT NULL,
  message           TEXT NOT NULL,
  status            evidence_request_status NOT NULL DEFAULT 'OPEN',
  due_at            TIMESTAMPTZ,
  created_by        TEXT NOT NULL DEFAULT 'system',
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cer_case ON case_evidence_requests(case_id);

-- Optional: snapshot table for dashboard
CREATE TABLE IF NOT EXISTS case_evidence_completeness_snapshots (
  id                BIGSERIAL PRIMARY KEY,
  case_id            UUID NOT NULL,
  computed_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  by_ground          JSONB NOT NULL,  -- {"G1":{"score":70,"required_total":5,"satisfied":3},...}
  overall_score      INT NOT NULL,
  missing_required   JSONB NOT NULL   -- [{"ground":"G1","item_key":"G1_CHAT_EXPORT","title":"..."}]
);

CREATE INDEX IF NOT EXISTS idx_cecs_case ON case_evidence_completeness_snapshots(case_id);
