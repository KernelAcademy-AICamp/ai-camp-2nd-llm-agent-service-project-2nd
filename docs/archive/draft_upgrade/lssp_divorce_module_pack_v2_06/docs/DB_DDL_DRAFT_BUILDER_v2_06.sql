-- DB_DDL_DRAFT_BUILDER_v2_06.sql
-- PostgreSQL 기준. (프로젝트 기존 스키마에 맞춰 FK/타입은 조정)

CREATE TABLE IF NOT EXISTS claim_templates (
  claim_code TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  required_inputs JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS draft_block_templates (
  block_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  body_template TEXT NOT NULL,
  required_claims TEXT[] NOT NULL DEFAULT '{}',
  required_grounds TEXT[] NOT NULL DEFAULT '{}',
  required_keypoint_kinds TEXT[] NOT NULL DEFAULT '{}',
  required_evidence_tags TEXT[] NOT NULL DEFAULT '{}',
  min_citations INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS drafts (
  draft_id UUID PRIMARY KEY,
  case_id UUID NOT NULL,
  draft_kind TEXT NOT NULL,
  selected_claims TEXT[] NOT NULL DEFAULT '{}',
  selected_grounds TEXT[] NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'INCOMPLETE',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS draft_block_instances (
  instance_id UUID PRIMARY KEY,
  draft_id UUID NOT NULL REFERENCES drafts(draft_id) ON DELETE CASCADE,
  block_id TEXT NOT NULL REFERENCES draft_block_templates(block_id),
  order_no INT NOT NULL,
  content_html TEXT NOT NULL,
  is_todo BOOLEAN NOT NULL DEFAULT FALSE,
  missing JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS draft_citations (
  citation_id UUID PRIMARY KEY,
  instance_id UUID NOT NULL REFERENCES draft_block_instances(instance_id) ON DELETE CASCADE,
  evidence_id UUID,
  extract_id UUID,
  keypoint_id UUID,
  label TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_drafts_case ON drafts(case_id);
CREATE INDEX IF NOT EXISTS idx_block_instances_draft ON draft_block_instances(draft_id);
