# UI Spec: Consultations Tab v2.07

Route: /cases/{caseId}/consultations

Layout (3 columns):
- Left: session list
- Center: transcript + message highlight
- Right: extracted cards (Issues / Facts / Evidence Requests / Actions / Risks)

Interactions:
1) Create Session: choose channel + title + started_at
2) Import transcript: paste text -> server splits into messages (by newline or timestamp pattern)
3) Run Extract: heuristic/llm
4) Confirm extract: forces picking source span (drag highlight or select message range)
5) Promote:
   - Fact -> Keypoint
   - EvidenceRequest -> Evidence checklist item
   - ActionItem -> NextActionsQueue

Visual rules:
- Show content_redacted by default
- Severity pill for risks (WARN/CRITICAL)
- Unconfirmed extracts are gray + TODO badge

Empty states:
- No sessions -> CTA "Add first consultation"
- Session no extracts -> CTA "Run extraction"
