-- Legal Authorities v2.11
-- 목적: 법령/판례/가이드 메타데이터와 핀포인트(짧은 발췌)를 저장하여
--      Draft Builder / Legal Grounds Tab에서 공용으로 사용한다.

CREATE TABLE IF NOT EXISTS legal_authorities (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('STATUTE','PRECEDENT','GUIDELINE')),
  jurisdiction TEXT NOT NULL DEFAULT 'KR',
  code TEXT NOT NULL,                -- 예: 민법, 가사소송법
  article TEXT NOT NULL,             -- 예: 제840조, 제836조의2
  title TEXT NOT NULL,
  summary TEXT,
  effective_from DATE,
  effective_to DATE,
  source_ref TEXT,                   -- 내부 링크/관리자 URL/문서 ID 등
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_legal_authorities_code_article
  ON legal_authorities(code, article);

CREATE TABLE IF NOT EXISTS legal_authority_snippets (
  id TEXT PRIMARY KEY,
  authority_id TEXT NOT NULL REFERENCES legal_authorities(id) ON DELETE CASCADE,
  snippet TEXT NOT NULL,             -- 짧은 발췌(25 단어 권장)
  pinpoint TEXT,                     -- 예: 제2항, 단서, 별표 등
  source_ref TEXT NOT NULL,          -- 발췌의 출처(문서/링크/페이지 등)
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_legal_authority_snippets_authority
  ON legal_authority_snippets(authority_id);

-- Draft citations 확장(이미 존재한다면 ALTER로 처리)
-- draft_citations: (draft_block_instance_id, cite_type, ref_id, label, snippet, source_ref, ...)
-- cite_type: 'AUTHORITY' | 'EVIDENCE' | 'KEYPOINT'
