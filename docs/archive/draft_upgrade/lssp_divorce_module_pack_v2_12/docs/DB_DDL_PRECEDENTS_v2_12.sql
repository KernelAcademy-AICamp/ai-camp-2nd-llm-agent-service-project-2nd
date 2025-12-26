-- v2.12 precedents library (minimal)
CREATE TABLE IF NOT EXISTS precedents (
  precedent_id TEXT PRIMARY KEY,
  case_no TEXT NOT NULL,
  court TEXT,
  decided_date DATE,
  gist TEXT NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  factors JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS precedent_snippets (
  snippet_id TEXT PRIMARY KEY,
  precedent_id TEXT NOT NULL REFERENCES precedents(precedent_id) ON DELETE CASCADE,
  title TEXT,
  snippet TEXT NOT NULL,
  page_or_para TEXT,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
