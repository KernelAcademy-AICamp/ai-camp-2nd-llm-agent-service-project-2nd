-- DB DDL: Recompute Orchestration v2.15
-- Target: PostgreSQL 14+
-- Goal:
--   1) Track every derived-state rebuild as a job (audit)
--   2) Track per-step status for debuggability
--   3) Store per-module last computed version/hash for "skip if unchanged"

CREATE TABLE IF NOT EXISTS recompute_jobs (
  job_id            UUID PRIMARY KEY,
  case_id           UUID NOT NULL,
  trigger_event     TEXT NOT NULL,
  trigger_entity    TEXT NULL,          -- e.g. "evidence:UUID", "process_event:UUID"
  requested_by      UUID NULL,
  requested_by_role TEXT NULL,          -- "lawyer" | "staff" | "system"
  mode              TEXT NOT NULL DEFAULT 'async', -- async | sync
  priority          INT  NOT NULL DEFAULT 100,
  status            TEXT NOT NULL,       -- queued | running | succeeded | failed | skipped | cancelled
  input_hash        TEXT NULL,
  output_hash       TEXT NULL,
  attempts          INT  NOT NULL DEFAULT 0,
  max_attempts      INT  NOT NULL DEFAULT 3,
  error_code        TEXT NULL,
  error_message     TEXT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  started_at        TIMESTAMPTZ NULL,
  finished_at       TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_recompute_jobs_case_created
  ON recompute_jobs (case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS recompute_job_steps (
  step_id        UUID PRIMARY KEY,
  job_id         UUID NOT NULL REFERENCES recompute_jobs(job_id) ON DELETE CASCADE,
  step_name      TEXT NOT NULL,          -- e.g. "process_engine", "timeline", "recommender"
  status         TEXT NOT NULL,          -- queued | running | succeeded | failed | skipped
  attempt        INT  NOT NULL DEFAULT 0,
  started_at     TIMESTAMPTZ NULL,
  finished_at    TIMESTAMPTZ NULL,
  metrics        JSONB NULL,             -- tokens, latency, counts
  error_code     TEXT NULL,
  error_message  TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_recompute_steps_job
  ON recompute_job_steps (job_id);

-- Optional: per-module "last computed" for fast skip.
CREATE TABLE IF NOT EXISTS case_derived_versions (
  case_id        UUID NOT NULL,
  module_name    TEXT NOT NULL,          -- "process_engine" | "timeline" | ...
  module_version TEXT NOT NULL,          -- "v2_14" etc
  input_hash     TEXT NULL,
  output_hash    TEXT NULL,
  computed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (case_id, module_name)
);

-- Recommended: case-level serialization using advisory lock:
--   SELECT pg_advisory_lock(hashtext(case_id::text));
--   SELECT pg_advisory_unlock(hashtext(case_id::text));
