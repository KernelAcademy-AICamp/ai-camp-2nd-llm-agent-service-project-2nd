-- DB DDL Appendix: Consultations v2.07
-- Postgres 기준 (UUID는 gen_random_uuid() 필요)

CREATE TABLE IF NOT EXISTS consultation_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  channel text NOT NULL CHECK (channel IN ('IN_PERSON','PHONE','CHAT','VIDEO','EMAIL','OTHER')),
  title text,
  started_at timestamptz,
  ended_at timestamptz,
  participants jsonb NOT NULL DEFAULT '[]'::jsonb,
  summary_text text,
  tags jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS consultation_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('CLIENT','LAWYER','SYSTEM')),
  content text NOT NULL,
  content_redacted text,
  occurred_at timestamptz,
  attachments jsonb NOT NULL DEFAULT '[]'::jsonb,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS consultation_extracts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  session_id uuid NOT NULL REFERENCES consultation_sessions(id) ON DELETE CASCADE,
  extract_type text NOT NULL CHECK (extract_type IN ('ISSUE','FACT','EVIDENCE_REQUEST','ACTION_ITEM','RISK','DEADLINE','OTHER')),
  payload jsonb NOT NULL,
  confidence numeric NOT NULL DEFAULT 0.0,
  materiality integer NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'TODO' CHECK (status IN ('TODO','CONFIRMED','DISMISSED')),
  source_spans jsonb NOT NULL DEFAULT '[]'::jsonb,
  linked_entities jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Optional: promote extracts into action_items / evidence_requests
CREATE TABLE IF NOT EXISTS case_action_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  source_session_id uuid,
  source_extract_id uuid,
  title text NOT NULL,
  priority text NOT NULL CHECK (priority IN ('P0','P1','P2')),
  owner text NOT NULL CHECK (owner IN ('CLIENT','LAWYER','SYSTEM')),
  due_at timestamptz,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','DONE','BLOCKED','CANCELLED')),
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL,
  source_session_id uuid,
  source_extract_id uuid,
  requested_for text NOT NULL, -- G1..G6 or COMMON
  evidence_types jsonb NOT NULL DEFAULT '[]'::jsonb,
  why text,
  priority text NOT NULL CHECK (priority IN ('P0','P1','P2')),
  due_at timestamptz,
  status text NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','SATISFIED','WAIVED','CANCELLED')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Audit log for redaction overrides / privileged access
CREATE TABLE IF NOT EXISTS consultation_audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid,
  message_id uuid,
  actor_id uuid,
  action text NOT NULL,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
