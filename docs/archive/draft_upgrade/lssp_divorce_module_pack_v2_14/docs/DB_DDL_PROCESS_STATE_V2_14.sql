-- DB DDL: Process State Machine v2.14
-- Minimal schema for tracking process states & events. Adapt to your existing case table.

CREATE TABLE IF NOT EXISTS case_process_state (
  case_id            UUID PRIMARY KEY,
  machine_name       TEXT NOT NULL,
  state_code         TEXT NOT NULL,
  entered_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  no_show_count      INT NOT NULL DEFAULT 0,
  -- key dates used by guards / deadlines (can be moved to case table if you already have them)
  cooling_off_start_at TIMESTAMPTZ NULL,
  cooling_off_end_at   TIMESTAMPTZ NULL,
  confirmation_date    TIMESTAMPTZ NULL,
  confirmation_issued_at TIMESTAMPTZ NULL,
  reported_at          TIMESTAMPTZ NULL,
  report_due_at        TIMESTAMPTZ NULL,
  mediation_filed_at   TIMESTAMPTZ NULL,
  settled_at           TIMESTAMPTZ NULL,
  judgment_at          TIMESTAMPTZ NULL,
  finalized_at         TIMESTAMPTZ NULL,
  has_minor_child_or_pregnant BOOLEAN NULL,
  waiver_approved      BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS case_process_event (
  id                UUID PRIMARY KEY,
  case_id            UUID NOT NULL,
  machine_name       TEXT NOT NULL,
  event_code         TEXT NOT NULL,
  occurred_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  payload_json       JSONB NOT NULL DEFAULT '{}'::jsonb,
  actor_id           UUID NULL,
  actor_role         TEXT NULL,
  prev_state         TEXT NULL,
  next_state         TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_case_process_event_case ON case_process_event(case_id, occurred_at);

-- Optional: state machine definitions stored in DB for admin editing/versioning
CREATE TABLE IF NOT EXISTS state_machine_def (
  name             TEXT PRIMARY KEY,
  version          TEXT NOT NULL,
  def_json         JSONB NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
