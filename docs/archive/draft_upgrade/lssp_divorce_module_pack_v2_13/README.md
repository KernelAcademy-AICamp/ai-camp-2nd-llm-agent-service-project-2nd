# LSSP / LEH Divorce Module Pack v2.13
## Timeline Consolidation & Risk Scoring

This pack extends the case timeline into a single canonical event stream that merges:
- Procedure events (stages, court dates, mediation/judgment milestones)
- Evidence events (uploads, extracts, reviews)
- Fact/Keypoint events (approved keypoints promoted to timeline)
- Deadline events (derived from notification_rules / due dates)
- Consultation events (session summaries, actions)

### Goals
1) One timeline to rule them all (detail/case Timeline tab)
2) Real-time deadline risk scoring + badges
3) Strong linking: every event can link to Evidence/Keypoints/Draft blocks/Issues/Checklist items

### What you get
- DB DDL for v2.13 timeline tables
- API contract (REST) for timeline queries & recompute
- Seed JSON for event types, grouping rules, and deadline->event rules
- FastAPI stub implementation
- Demo script to generate/recompute timeline for a case

