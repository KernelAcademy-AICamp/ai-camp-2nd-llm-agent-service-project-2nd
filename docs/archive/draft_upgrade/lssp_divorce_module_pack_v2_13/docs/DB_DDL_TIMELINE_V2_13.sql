-- LSSP / LEH v2.13 Timeline Consolidation
-- NOTE: adapt table/column names to your existing schema. This is an additive design.

-- 1) Canonical timeline events
CREATE TABLE IF NOT EXISTS timeline_events (
  id                  BIGSERIAL PRIMARY KEY,
  case_id             UUID NOT NULL,
  category            TEXT NOT NULL,          -- PROCEDURE | EVIDENCE | FACT | DEADLINE | CONSULTATION | SYSTEM
  event_type          TEXT NOT NULL,          -- e.g., STAGE_CHANGED, EVIDENCE_UPLOADED, KEYPOINT_APPROVED, DEADLINE_DUE
  event_subtype       TEXT NULL,              -- optional finer-grain classifier
  title               TEXT NOT NULL,
  summary             TEXT NULL,
  occurred_at         TIMESTAMPTZ NOT NULL,   -- the ordering timestamp for the timeline
  start_at            TIMESTAMPTZ NULL,       -- for ranges (e.g., protection order duration)
  end_at              TIMESTAMPTZ NULL,
  timezone            TEXT NULL,              -- store IANA if you use local interpretation

  -- Risk & severity
  severity            SMALLINT NOT NULL DEFAULT 0,      -- 0..5
  risk_score          NUMERIC(6,2) NOT NULL DEFAULT 0,  -- 0..100
  risk_reason         TEXT NULL,
  penalty_type        TEXT NULL,              -- EFFECT_LOSS | ADMIN_FINE | CLAIM_BARRED | NONE

  -- Provenance links (nullable)
  evidence_id         UUID NULL,
  evidence_extract_id UUID NULL,
  keypoint_id         UUID NULL,
  draft_id            UUID NULL,
  draft_block_id      UUID NULL,
  issue_id            UUID NULL,
  checklist_item_id   UUID NULL,
  consultation_id     UUID NULL,

  -- Generic metadata
  tags                JSONB NOT NULL DEFAULT '[]'::jsonb,
  meta                JSONB NOT NULL DEFAULT '{}'::jsonb,

  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_timeline_events_case_time ON timeline_events(case_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_timeline_events_case_category ON timeline_events(case_id, category);
CREATE INDEX IF NOT EXISTS idx_timeline_events_case_type ON timeline_events(case_id, event_type);

-- 2) Optional: stable "anchors" to prevent duplicates during recompute
CREATE TABLE IF NOT EXISTS timeline_event_anchors (
  id          BIGSERIAL PRIMARY KEY,
  case_id     UUID NOT NULL,
  anchor_key  TEXT NOT NULL,       -- e.g., DEADLINE:CONSENSUAL_CERT_EXPIRES:2025-12-31
  event_id    BIGINT NOT NULL REFERENCES timeline_events(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(case_id, anchor_key)
);

-- 3) Audit trail for recompute and manual edits
CREATE TABLE IF NOT EXISTS timeline_audit_logs (
  id           BIGSERIAL PRIMARY KEY,
  case_id      UUID NOT NULL,
  action       TEXT NOT NULL,      -- RECOMPUTE | CREATE | UPDATE | DELETE
  actor_type   TEXT NOT NULL,      -- SYSTEM | USER | ADMIN
  actor_id     TEXT NULL,
  details      JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

