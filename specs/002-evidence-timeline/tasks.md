# Tasks: Evidence Timeline

**Input**: Design documents from `/specs/002-evidence-timeline/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/timeline-api.md ✓, quickstart.md ✓

**Tests**: NOT explicitly requested in feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Summary

| Metric | Value |
|:-------|:------|
| Total Tasks | 33 |
| User Story 1 Tasks | 11 |
| User Story 2 Tasks | 6 |
| User Story 3 Tasks | 6 |
| Setup Tasks | 2 |
| Foundational Tasks | 4 |
| Polish Tasks | 4 |
| Parallel Opportunities | 16 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for timeline feature

- [x] T001 Create feature branch `002-evidence-timeline` from dev
- [x] T002 [P] Verify DynamoDB table `leh_evidence` schema has required fields (timestamp, labels, speaker, article_840_tags)

**Checkpoint**: Environment ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create backend timeline schemas (TimelineEventType enum, TimelineEvent, TimelineFilter, TimelineResult) in backend/app/schemas/timeline.py
- [x] T004 [P] Create frontend TypeScript types (TimelineEventType, TimelineEvent, TimelineFilter, TimelineResult) in frontend/src/types/timeline.ts
- [x] T005 Use existing `get_evidence_by_case()` from dynamo.py (no new repository needed)
- [x] T006 Add significance calculation constants (SIGNIFICANCE_WEIGHTS, KEY_EVIDENCE_THRESHOLD) to backend/app/services/timeline_service.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - View Evidence Timeline (Priority: P1) 🎯 MVP

**Goal**: Display all evidence arranged chronologically on a timeline with date markers and summary information

**Independent Test**: Load a case with multiple evidence items and verify they display in chronological order with proper date markers and summary information

### Backend Implementation for User Story 1

- [x] T007 [US1] Implement `_build_events()` method in TimelineService to convert DynamoDB evidence to TimelineEvent objects in backend/app/services/timeline_service.py
- [x] T008 [US1] Implement `_calculate_significance()` method to compute significance score from Article 840 labels in backend/app/services/timeline_service.py
- [x] T009 [US1] Implement `get_timeline()` method with case access validation in backend/app/services/timeline_service.py
- [x] T010 [US1] Create timeline router with `GET /cases/{case_id}/timeline` endpoint in backend/app/api/timeline.py
- [x] T011 [US1] Register timeline router in FastAPI app in backend/app/main.py

### Frontend Implementation for User Story 1

- [x] T012 [P] [US1] Create timeline API client with `getTimeline()` function in frontend/src/lib/api/timeline.ts
- [x] T013 [P] [US1] Create `useTimeline` hook with useState/useCallback in frontend/src/hooks/useTimeline.ts
- [x] T014 [US1] Create TimelineEvent component with type icons, date/time display, speaker badge, and summary in frontend/src/components/evidence/TimelineEvent.tsx
- [x] T015 [US1] Enhance existing Timeline component to use TimelineEvent, support chronological sorting (asc/desc), and handle click navigation in frontend/src/components/evidence/Timeline.tsx
- [x] T016 [US1] Create timeline page route with data fetching and loading/empty states in frontend/src/app/cases/[id]/timeline/page.tsx
- [x] T017 [US1] Add audit log entry for TIMELINE_VIEW action in backend/app/services/timeline_service.py

**Checkpoint**: User Story 1 complete - timeline displays evidence chronologically with proper markers

---

## Phase 4: User Story 2 - Filter Timeline by Criteria (Priority: P2)

**Goal**: Enable filtering by date range, speaker, or evidence labels to focus on specific aspects of the case

**Independent Test**: Apply various filter combinations and verify only matching evidence items appear in the timeline

### Backend Implementation for User Story 2

- [ ] T018 [US2] Implement `_apply_filters()` method with date_range, labels, speakers, and event_types filtering in backend/app/services/timeline_service.py
- [ ] T019 [US2] Add filter query parameter parsing (comma-separated values) in backend/app/api/timeline.py
- [ ] T020 [US2] Implement pagination (limit/offset) in `_build_result()` method in backend/app/services/timeline_service.py

### Frontend Implementation for User Story 2

- [ ] T021 [P] [US2] Create TimelineFilter component with date range picker, label multiselect, and speaker dropdown in frontend/src/components/evidence/TimelineFilter.tsx
- [ ] T022 [US2] Add filter state management and URL query param synchronization in frontend/src/app/cases/[id]/timeline/page.tsx
- [ ] T023 [US2] Add "Clear All Filters" button and empty filter results message in frontend/src/components/evidence/TimelineFilter.tsx

**Checkpoint**: User Story 2 complete - all filtering capabilities work and persist in URL

---

## Phase 5: User Story 3 - Identify Key Evidence (Priority: P3)

**Goal**: Visually highlight key evidence items on the timeline for quick identification of legally significant materials

**Independent Test**: Load a case with evidence of varying significance and verify visual distinction between key and regular evidence items

### Backend Implementation for User Story 3

- [ ] T024 [US3] Implement `is_key_evidence` flag calculation (significance >= 4) in `_build_events()` method in backend/app/services/timeline_service.py
- [ ] T025 [US3] Add `key_only` filter parameter support to return only key evidence in backend/app/services/timeline_service.py

### Frontend Implementation for User Story 3

- [ ] T026 [P] [US3] Create TimelineTooltip component with significance score and legal labels display in frontend/src/components/evidence/TimelineTooltip.tsx
- [ ] T027 [US3] Add visual distinction for key evidence (larger markers, different color, badge) in frontend/src/components/evidence/TimelineEvent.tsx
- [ ] T028 [US3] Add "Show Key Evidence Only" toggle button in frontend/src/components/evidence/TimelineFilter.tsx
- [ ] T029 [US3] Integrate tooltip on hover for timeline events in frontend/src/components/evidence/Timeline.tsx

**Checkpoint**: User Story 3 complete - key evidence is visually distinct and filterable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Performance optimization and edge case handling

- [ ] T030 [P] Handle edge case: empty state when case has no evidence (display guidance message)
- [ ] T031 [P] Handle edge case: evidence without timestamp (display at end with "날짜 미상" marker)
- [ ] T032 Implement virtual scrolling or pagination UI for cases with >50 evidence items in frontend/src/components/evidence/Timeline.tsx
- [ ] T033 Run quickstart.md verification checklist and fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion, integrates with US1
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion, integrates with US1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core timeline display
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Adds filtering to US1 timeline
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Adds significance highlighting to US1 timeline

### Within Each User Story

- Backend models/schemas before services
- Services before endpoints/routers
- Backend endpoints before frontend API clients
- Frontend API clients before hooks
- Hooks before components
- Components before page integration

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T003 (backend schemas) || T004 (frontend types)

**Phase 3 (User Story 1)**:
- T012 (API client) || T013 (hook) - after T011
- T014 (TimelineEvent) || T015 (Timeline) - different components

**Phase 4 (User Story 2)**:
- T021 (TimelineFilter) can run parallel with backend filter work

**Phase 5 (User Story 3)**:
- T026 (TimelineTooltip) can run parallel with backend key evidence work

**Phase 6 (Polish)**:
- T030 || T031 - independent edge cases

---

## Parallel Example: Foundational Phase

```bash
# Launch backend and frontend type definitions together:
Task: "Create backend timeline schemas in backend/app/schemas/timeline.py"
Task: "Create frontend TypeScript types in frontend/src/types/timeline.ts"
```

## Parallel Example: User Story 1

```bash
# After backend router is registered, launch API client and hook together:
Task: "Create timeline API client in frontend/src/lib/api/timeline.ts"
Task: "Create useTimeline hook in frontend/src/hooks/useTimeline.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify branch and DynamoDB)
2. Complete Phase 2: Foundational (schemas and types)
3. Complete Phase 3: User Story 1 (core timeline view)
4. **STOP and VALIDATE**: Test timeline displays evidence chronologically
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test filtering → Deploy/Demo
4. Add User Story 3 → Test key evidence highlighting → Deploy/Demo
5. Each story adds value without breaking previous stories

### Suggested MVP Scope

**Phase 1 + Phase 2 + Phase 3 (User Story 1)** = Minimum Viable Timeline

This delivers:
- Chronological evidence display
- Date/time markers
- Type icons and speaker badges
- Click to view evidence details
- Audit logging

---

## File Summary

### New Files to Create

| File | Purpose |
|:-----|:--------|
| `backend/app/schemas/timeline.py` | Pydantic models for timeline |
| `backend/app/services/timeline_service.py` | Timeline business logic |
| `backend/app/api/timeline.py` | Timeline API router |
| `frontend/src/types/timeline.ts` | TypeScript type definitions |
| `frontend/src/lib/api/timeline.ts` | Timeline API client |
| `frontend/src/hooks/useTimeline.ts` | Timeline data hook |
| `frontend/src/components/evidence/TimelineEvent.tsx` | Individual event component |
| `frontend/src/components/evidence/TimelineFilter.tsx` | Filter controls |
| `frontend/src/components/evidence/TimelineTooltip.tsx` | Hover tooltip |
| `frontend/src/app/cases/[id]/timeline/page.tsx` | Timeline page route |

### Files to Modify

| File | Purpose |
|:-----|:--------|
| `backend/app/main.py` | Register timeline router |
| `backend/app/repositories/evidence_repository.py` | Add timeline query method |
| `frontend/src/components/evidence/Timeline.tsx` | Enhance existing component |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- Performance target: <2s initial load, <500ms filter, 60fps scroll
- Max 1000 evidence items per case (soft limit)
- Korean UTF-8 support required for labels and speaker names
- Commit after each task or logical group
