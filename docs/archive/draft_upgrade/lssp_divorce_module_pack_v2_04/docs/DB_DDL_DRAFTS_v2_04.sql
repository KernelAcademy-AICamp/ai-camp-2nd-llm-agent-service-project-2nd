-- DB DDL Drafts v2.04 (append-only)

-- 1) draft_templates (seed)
CREATE TABLE IF NOT EXISTS draft_templates (
  id TEXT PRIMARY KEY,              -- e.g. PETITION_DIVORCE
  label TEXT NOT NULL,
  version TEXT NOT NULL DEFAULT 'v2.04',
  schema JSONB NOT NULL,            -- sections/blocks ordering
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2) draft_blocks (seed)
CREATE TABLE IF NOT EXISTS draft_blocks (
  id TEXT PRIMARY KEY,              -- e.g. PETITION_FACTS_G1_COMM
  label TEXT NOT NULL,
  block_tag TEXT NOT NULL,          -- FACTS | GROUNDS | RELIEF | ATTACHMENTS ...
  template TEXT NOT NULL,           -- text template
  required_keypoint_types JSONB NOT NULL DEFAULT '[]',
  required_evidence_tags JSONB NOT NULL DEFAULT '[]',
  conditions TEXT NULL,             -- expression string
  legal_refs JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3) drafts (case instance)
CREATE TABLE IF NOT EXISTS drafts (
  id UUID PRIMARY KEY,
  case_id UUID NOT NULL,
  template_id TEXT NOT NULL REFERENCES draft_templates(id),
  title TEXT NOT NULL,
  meta JSONB NOT NULL DEFAULT '{}',
  coverage_score INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'DRAFTING', -- DRAFTING|NEEDS_REVIEW|FINALIZED
  created_by UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_drafts_case ON drafts(case_id);

-- 4) draft_block_instances (ordered blocks)
CREATE TABLE IF NOT EXISTS draft_block_instances (
  id UUID PRIMARY KEY,
  draft_id UUID NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
  block_id TEXT NOT NULL REFERENCES draft_blocks(id),
  section_key TEXT NOT NULL,
  position INT NOT NULL,
  text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'AUTO', -- AUTO|EDITED|TODO|REMOVED
  coverage_score INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_dbi_draft ON draft_block_instances(draft_id);

-- 5) draft_citations (block ↔ keypoint/extract)
CREATE TABLE IF NOT EXISTS draft_citations (
  id UUID PRIMARY KEY,
  block_instance_id UUID NOT NULL REFERENCES draft_block_instances(id) ON DELETE CASCADE,
  keypoint_id UUID NULL,
  extract_id UUID NULL,
  note TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_one_ref CHECK (keypoint_id IS NOT NULL OR extract_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_cit_block ON draft_citations(block_instance_id);

-- 6) draft_precedent_links (optional)
CREATE TABLE IF NOT EXISTS draft_precedent_links (
  draft_id UUID NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
  precedent_id TEXT NOT NULL,
  reason TEXT NULL,
  PRIMARY KEY(draft_id, precedent_id)
);
