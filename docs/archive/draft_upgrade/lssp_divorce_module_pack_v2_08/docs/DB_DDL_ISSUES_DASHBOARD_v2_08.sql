-- v2.08 Issues Dashboard (Key Issues) - DB schema appendix
-- 목적: detail/case 상단에 "주요쟁점"을 점수화하여 보여주고, 증거/키포인트/마감/초안/상담과 연결한다.

CREATE TABLE IF NOT EXISTS case_issues (
  issue_id            UUID PRIMARY KEY,
  case_id             UUID NOT NULL,
  issue_code          VARCHAR(64) NOT NULL,      -- e.g., DEADLINE_REPORTING, EVIDENCE_G3_GAP, CHILD_CUSTODY_PENDING
  issue_group         VARCHAR(32) NOT NULL,      -- DEADLINE | EVIDENCE | PROCEDURE | DRAFT | CHILD | PROPERTY | OTHER
  severity            SMALLINT NOT NULL DEFAULT 50,   -- 0~100 (UI용)
  status              VARCHAR(16) NOT NULL DEFAULT 'OPEN', -- OPEN | ACKED | RESOLVED | DISMISSED
  title               VARCHAR(200) NOT NULL,
  summary             TEXT,
  due_at              TIMESTAMPTZ NULL,          -- 마감이 있는 경우
  penalty_type        VARCHAR(32) NULL,          -- EFFECT_LOSS | ADMIN_FINE | CLAIM_BARRED 등
  related_ground_code VARCHAR(8) NULL,           -- 'G1'..'G6' (해당 사유 관련이면)
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_issues_case ON case_issues(case_id);
CREATE INDEX IF NOT EXISTS idx_case_issues_status ON case_issues(status);
CREATE INDEX IF NOT EXISTS idx_case_issues_group ON case_issues(issue_group);

-- issue 근거(왜 이게 이슈인지) 연결: keypoint / evidence / timeline_event / draft_block_instance / consultation_extract 등
CREATE TABLE IF NOT EXISTS case_issue_links (
  link_id     UUID PRIMARY KEY,
  issue_id    UUID NOT NULL REFERENCES case_issues(issue_id) ON DELETE CASCADE,
  link_type   VARCHAR(32) NOT NULL,  -- KEYPOINT | EVIDENCE | EVENT | DRAFT_BLOCK | CONSULT_EXTRACT | DOC
  ref_id      UUID NOT NULL,
  note        TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_case_issue_links_issue ON case_issue_links(issue_id);
CREATE INDEX IF NOT EXISTS idx_case_issue_links_type ON case_issue_links(link_type);

-- 점수 스냅샷: 대시보드 성능/추세 표시용 (optional)
CREATE TABLE IF NOT EXISTS case_health_snapshots (
  snapshot_id UUID PRIMARY KEY,
  case_id     UUID NOT NULL,
  captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  scores      JSONB NOT NULL,     -- {"deadline_risk": 80, "evidence_completeness": 45, "draft_completeness": 30, ...}
  counters    JSONB NOT NULL      -- {"keypoints": 28, "evidences": 12, "open_issues": 6, ...}
);

CREATE INDEX IF NOT EXISTS idx_case_health_snapshots_case_time ON case_health_snapshots(case_id, captured_at);
