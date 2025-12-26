# Timeline View Spec v2.13 (detail/case)

## Layout
- Top: Deadline strip (highest risk first)
- Main: Timeline feed with grouping and filters

## Filters
- Category: Deadlines / Procedure / Facts / Evidence / Consultations
- Tags: G1..G6, Reporting, Violence, Finance, Custody, Property, etc.
- Risk: >=80, >=60, >=40

## Item card
- Left: date/time
- Center: title + summary
- Right: badges (penalty_type, risk_score, severity)
- Footer: links (Evidence, Keypoint, Draft block, Issue, Checklist item, Consultation)

## UX rules
- DEADLINE events pin to top until resolved.
- Clicking a DEADLINE opens the exact due date, rule source, and “how to fix” CTA.
- FACT events created only from approved keypoints (no raw extraction).
- Evidence events show status: UNREVIEWED/REVIEWED/ADMISSIBLE/QUESTIONABLE.

## Collapse/Grouping
- Collapse events within 180 minutes if same collapse key (see data/timeline_grouping_rules.v2_13.json)

