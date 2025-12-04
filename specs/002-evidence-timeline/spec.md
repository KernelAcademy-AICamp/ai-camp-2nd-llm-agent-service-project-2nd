# Feature Specification: Evidence Timeline

**Feature Branch**: `002-evidence-timeline`
**Created**: 2025-12-04
**Status**: Draft
**Input**: UC6 (증거 타임라인 조회) - Users need to view all evidence for a case arranged chronologically on a timeline, with filtering and significance highlighting to efficiently review case materials.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Evidence Timeline (Priority: P1)

As a lawyer reviewing a case, I want to see all evidence arranged chronologically on a timeline so that I can understand the sequence of events and identify patterns.

**Why this priority**: Chronological evidence visualization is the core feature that enables lawyers to reconstruct event sequences and identify legal relevance. Without this, lawyers must manually sort through evidence files.

**Independent Test**: Can be fully tested by loading a case with multiple evidence items and verifying they display in chronological order with proper date markers and summary information.

**Acceptance Scenarios**:

1. **Given** a lawyer opens a case with uploaded evidence, **When** they navigate to the timeline view, **Then** all evidence items are displayed in chronological order (oldest to newest by default).
2. **Given** evidence items exist with various timestamps, **When** viewing the timeline, **Then** each item shows its date, type icon, speaker label, and brief summary.
3. **Given** a lawyer clicks on a timeline event, **When** the event is selected, **Then** the full evidence details panel opens showing complete metadata and content preview.

---

### User Story 2 - Filter Timeline by Criteria (Priority: P2)

As a lawyer preparing for court, I want to filter the timeline by date range, speaker, or evidence labels so that I can focus on specific aspects of the case.

**Why this priority**: Filtering enables efficient evidence review for specific legal arguments. Cases may have hundreds of evidence items, making unfiltered viewing impractical for targeted analysis.

**Independent Test**: Can be fully tested by applying various filter combinations and verifying only matching evidence items appear in the timeline.

**Acceptance Scenarios**:

1. **Given** a lawyer is viewing the timeline, **When** they set a date range filter, **Then** only evidence within that date range is displayed.
2. **Given** evidence labeled with categories (폭언, 불륜, 재산분쟁), **When** a lawyer filters by specific label, **Then** only evidence with that label appears.
3. **Given** evidence from multiple speakers (원고, 피고, 제3자), **When** filtering by speaker, **Then** only evidence from the selected speaker is shown.
4. **Given** multiple filters are active, **When** a lawyer clears all filters, **Then** the timeline returns to showing all evidence.

---

### User Story 3 - Identify Key Evidence (Priority: P3)

As a lawyer building a legal argument, I want key evidence items to be visually highlighted on the timeline so that I can quickly identify the most legally significant materials.

**Why this priority**: Significance highlighting reduces review time by drawing attention to evidence most likely to impact the case outcome. This builds on the timeline foundation from US1.

**Independent Test**: Can be fully tested by loading a case with evidence of varying significance and verifying visual distinction between key and regular evidence items.

**Acceptance Scenarios**:

1. **Given** evidence has been analyzed for legal significance, **When** viewing the timeline, **Then** key evidence items are visually distinct (larger markers, different color, badge).
2. **Given** a lawyer hovers over a key evidence marker, **When** the tooltip appears, **Then** it shows the significance score and relevant legal labels.
3. **Given** the timeline contains both key and regular evidence, **When** a lawyer toggles "Show Key Evidence Only", **Then** only items flagged as key evidence are displayed.

---

### Edge Cases

- What happens when a case has no evidence uploaded yet? System MUST display an empty state with guidance to upload evidence first.
- What happens when evidence lacks timestamp information? System MUST place timestamp-less evidence at the end with "날짜 미상" (unknown date) marker.
- What happens with 500+ evidence items? System MUST implement pagination or virtual scrolling to maintain performance.
- What happens when filter results are empty? System MUST display "No matching evidence" message with option to clear filters.
- What happens when evidence timestamps are identical? System MUST maintain stable sort order using evidence ID as secondary sort key.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display all evidence for a case on a chronological timeline.
- **FR-002**: Timeline MUST show evidence date, type (image/audio/video/text/pdf), speaker, and brief summary for each item.
- **FR-003**: System MUST support date range filtering with start and end date selectors.
- **FR-004**: System MUST support filtering by evidence labels (Article 840 categories).
- **FR-005**: System MUST support filtering by speaker (원고/피고/제3자/불명).
- **FR-006**: System MUST visually distinguish key evidence items (significance score >= 0.7).
- **FR-007**: System MUST allow users to toggle between showing all evidence vs. key evidence only.
- **FR-008**: Clicking a timeline event MUST navigate to or open the evidence detail view.
- **FR-009**: System MUST display significance score and labels on hover/tooltip for each item.
- **FR-010**: Timeline view MUST be restricted to users with case access (VIEWER, MEMBER, OWNER roles).
- **FR-011**: System MUST support sorting toggle: oldest-first or newest-first.
- **FR-012**: System MUST handle pagination or infinite scroll for cases with >50 evidence items.

### Key Entities

- **TimelineEvent**: Represents a single evidence item on the timeline including evidence_id, timestamp, event_type, speaker, summary, labels, significance_score, is_key_evidence.
- **TimelineFilter**: User-applied filter criteria including date_start, date_end, labels[], speakers[], show_key_only boolean.
- **TimelineResult**: Container for timeline data including events[], total_count, filtered_count, date_range_min, date_range_max, statistics.

## Assumptions

- Evidence has been processed by AI Worker and has metadata in DynamoDB
- Significance scores are pre-calculated during evidence processing (0.0-1.0 scale)
- Legal labels follow Article 840 taxonomy (부정행위, 악의의유기, 배우자학대, etc.)
- Timeline displays evidence timestamps, not upload timestamps
- Maximum 1000 evidence items per case (soft limit)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Timeline renders initial view in under 2 seconds for cases with up to 100 evidence items.
- **SC-002**: Filter operations complete and re-render timeline in under 500ms.
- **SC-003**: 100% of evidence items for a case are represented on the timeline (no data loss).
- **SC-004**: Key evidence items are correctly identified with 90%+ accuracy against AI significance scores.
- **SC-005**: Timeline maintains responsive scroll performance (60fps) with up to 500 items visible.
- **SC-006**: All timeline interactions are logged in audit trail with user context.
