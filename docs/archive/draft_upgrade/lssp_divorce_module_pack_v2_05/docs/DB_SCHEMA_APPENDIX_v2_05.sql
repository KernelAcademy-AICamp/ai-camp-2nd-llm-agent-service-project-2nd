-- DB Schema Appendix v2.05: Document Generation

CREATE TABLE IF NOT EXISTS document_templates (
  template_id UUID PRIMARY KEY,
  doc_type TEXT NOT NULL,
  version TEXT NOT NULL,
  locale TEXT NOT NULL DEFAULT 'ko-KR',
  format TEXT NOT NULL DEFAULT 'docx',
  -- optional stored template file key (S3/local)
  template_file_key TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_instances (
  document_id UUID PRIMARY KEY,
  case_id UUID NOT NULL,
  doc_type TEXT NOT NULL,
  locale TEXT NOT NULL DEFAULT 'ko-KR',
  format TEXT NOT NULL DEFAULT 'docx',
  status TEXT NOT NULL DEFAULT 'READY',
  payload_json JSONB NOT NULL,   -- snapshot used to render
  file_key TEXT NOT NULL,        -- output file storage key
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_instances_case ON document_instances(case_id, created_at DESC);
