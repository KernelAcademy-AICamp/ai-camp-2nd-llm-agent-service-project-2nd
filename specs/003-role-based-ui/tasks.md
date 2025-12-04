# Tasks: Role-Based UI System

**Input**: Design documents from `/specs/003-role-based-ui/`
**Prerequisites**: plan.md ✓, spec.md ✓
**Screen Reference**: `docs/screens/SCREEN_DEFINITION.md`

**Tests**: NOT explicitly requested in feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Summary

| Metric | Value |
|:-------|:------|
| Total Tasks | 78 |
| User Story 1 Tasks | 8 |
| User Story 2 Tasks | 10 |
| User Story 3 Tasks | 12 |
| User Story 4 Tasks | 15 |
| User Story 5 Tasks | 17 |
| User Story 6 Tasks | 7 |
| User Story 7 Tasks | 5 |
| User Story 8 Tasks | 3 |
| Setup Tasks | 4 |
| Foundational Tasks | 6 |
| Parallel Opportunities | 28 |
| Audit Compliance Tasks | 5 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for role-based UI

- [ ] T001 Create feature branch `003-role-based-ui` from dev
- [ ] T002 [P] Install frontend dependencies (recharts, react-big-calendar, @kakao/kakao-maps-sdk) in frontend/package.json
- [ ] T003 [P] Create Alembic migration for new tables (messages, calendar_events, investigation_records, invoices) in backend/alembic/versions/
- [ ] T004 Run database migration and verify schema

**Checkpoint**: Environment ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Add CLIENT and DETECTIVE to UserRole enum in backend/app/db/models.py
- [ ] T006 [P] Create Message model in backend/app/db/models.py
- [ ] T007 [P] Create CalendarEvent model in backend/app/db/models.py
- [ ] T008 [P] Create InvestigationRecord model in backend/app/db/models.py
- [ ] T009 [P] Create Invoice model in backend/app/db/models.py
- [ ] T010 Update role permissions in backend/app/db/schemas.py to include CLIENT and DETECTIVE

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Role & Auth System Extension (Priority: P1)

**Goal**: Extend authentication system with CLIENT and DETECTIVE roles

**Independent Test**: Create test users with CLIENT/DETECTIVE roles and verify role-based routing works correctly

### Backend Implementation for User Story 1

- [ ] T011 [US1] Update signup endpoint to accept CLIENT and DETECTIVE roles in backend/app/api/auth.py
- [ ] T012 [US1] Create role validation helper function in backend/app/core/dependencies.py
- [ ] T013 [US1] Add role-based permission checks to existing endpoints in backend/app/api/cases.py

### Frontend Implementation for User Story 1

- [ ] T014 [P] [US1] Create role redirect logic after login in frontend/src/app/(auth)/login/page.tsx
- [ ] T015 [P] [US1] Create middleware for role-based routing in frontend/src/middleware.ts
- [ ] T016 [US1] Create useRole hook for role checking in frontend/src/hooks/useRole.ts
- [ ] T017 [US1] Update AuthContext to include role information in frontend/src/contexts/AuthContext.tsx
- [ ] T018 [US1] Create RoleGuard component for protected routes in frontend/src/components/auth/RoleGuard.tsx

**Checkpoint**: User Story 1 complete - role-based authentication works

---

## Phase 4: User Story 2 - Lawyer Dashboard (Priority: P1) - MVP

**Goal**: Create lawyer dashboard with case overview and statistics

**Independent Test**: Login as lawyer and verify dashboard displays correct statistics, recent cases, and calendar events

### Backend Implementation for User Story 2

- [ ] T019 [US2] Create dashboard stats endpoint GET /lawyer/dashboard in backend/app/api/lawyer_portal.py
- [ ] T020 [US2] Create LawyerDashboardService with stats calculation in backend/app/services/lawyer_dashboard_service.py
- [ ] T021 [US2] Create dashboard schemas (StatsCard, RecentCase, etc.) in backend/app/schemas/lawyer_dashboard.py

### Frontend Implementation for User Story 2

- [ ] T022 [P] [US2] Create lawyer portal layout in frontend/src/app/lawyer/layout.tsx
- [ ] T023 [P] [US2] Create LawyerNav component with menu items in frontend/src/components/lawyer/LawyerNav.tsx
- [ ] T024 [P] [US2] Create StatsCard component in frontend/src/components/lawyer/StatsCard.tsx
- [ ] T025 [P] [US2] Create CaseStatsChart component using Recharts in frontend/src/components/charts/CaseStatsChart.tsx
- [ ] T026 [US2] Create lawyer dashboard page in frontend/src/app/lawyer/dashboard/page.tsx
- [ ] T027 [US2] Create useLawyerDashboard hook in frontend/src/hooks/useLawyerDashboard.ts
- [ ] T028 [US2] Register lawyer_portal router in backend/app/main.py

**Checkpoint**: User Story 2 complete - lawyer dashboard displays statistics and recent activity

---

## Phase 5: User Story 3 - Lawyer Case Management (Priority: P1) - MVP

**Goal**: Enable lawyers to manage cases with filtering and bulk actions

**Independent Test**: List cases with various filters, perform bulk AI analysis request, view case detail with evidence

### Backend Implementation for User Story 3

- [ ] T029 [US3] Create case list endpoint with filters GET /lawyer/cases in backend/app/api/lawyer_portal.py
- [ ] T030 [US3] Add bulk action endpoint POST /lawyer/cases/bulk-action in backend/app/api/lawyer_portal.py
- [ ] T031 [US3] Create CaseListService with filtering logic in backend/app/services/case_list_service.py
- [ ] T032 [US3] Create case list schemas (CaseFilter, CaseListItem, BulkAction) in backend/app/schemas/case_list.py

### Frontend Implementation for User Story 3

- [ ] T033 [P] [US3] Create CaseCard component in frontend/src/components/lawyer/CaseCard.tsx
- [ ] T034 [P] [US3] Create CaseTable component with sorting in frontend/src/components/lawyer/CaseTable.tsx
- [ ] T035 [P] [US3] Create CaseFilter component in frontend/src/components/lawyer/CaseFilter.tsx
- [ ] T036 [P] [US3] Create BulkActionBar component in frontend/src/components/lawyer/BulkActionBar.tsx
- [ ] T037 [US3] Create case list page in frontend/src/app/lawyer/cases/page.tsx
- [ ] T038 [US3] Create case detail page in frontend/src/app/lawyer/cases/[id]/page.tsx
- [ ] T039 [US3] Create useCaseList hook with filtering in frontend/src/hooks/useCaseList.ts
- [ ] T040 [US3] Integrate evidence list and AI summary display in case detail page

**Checkpoint**: User Story 3 complete - lawyers can manage cases with full filtering and bulk actions

---

## Phase 6: User Story 4 - Client Portal (Priority: P2)

**Goal**: Create client portal for case tracking and evidence submission

**Independent Test**: Login as client, view case progress, upload evidence, send message to lawyer

### Backend Implementation for User Story 4

- [ ] T041 [US4] Create client portal router in backend/app/api/client_portal.py
- [ ] T042 [US4] Create client dashboard endpoint GET /client/dashboard in backend/app/api/client_portal.py
- [ ] T043 [US4] Create client case view endpoint GET /client/cases/{id} in backend/app/api/client_portal.py
- [ ] T044 [US4] Create client evidence upload endpoint POST /client/cases/{id}/evidence in backend/app/api/client_portal.py
- [ ] T044a [US4] [AUDIT] Add audit logging for evidence upload (Constitution Principle I) in backend/app/api/client_portal.py
- [ ] T045 [US4] Create ClientPortalService in backend/app/services/client_portal_service.py
- [ ] T046 [US4] Create client portal schemas in backend/app/schemas/client_portal.py
- [ ] T047 [US4] Register client_portal router in backend/app/main.py

### Frontend Implementation for User Story 4

- [ ] T048 [P] [US4] Create client portal layout in frontend/src/app/client/layout.tsx
- [ ] T049 [P] [US4] Create ClientNav component in frontend/src/components/client/ClientNav.tsx
- [ ] T050 [P] [US4] Create ProgressTracker component in frontend/src/components/client/ProgressTracker.tsx
- [ ] T051 [P] [US4] Create EvidenceUploader component in frontend/src/components/client/EvidenceUploader.tsx
- [ ] T052 [US4] Create client dashboard page in frontend/src/app/client/dashboard/page.tsx
- [ ] T053 [US4] Create client case detail page in frontend/src/app/client/cases/[id]/page.tsx
- [ ] T054 [US4] Create evidence submission page in frontend/src/app/client/cases/[id]/evidence/page.tsx

**Checkpoint**: User Story 4 complete - clients can view cases and submit evidence

---

## Phase 7: User Story 5 - Detective Portal (Priority: P2)

**Goal**: Create detective portal for investigation management and field recording

**Independent Test**: Login as detective, view assigned investigations, record field data with GPS, submit report

### Backend Implementation for User Story 5

- [ ] T055 [US5] Create detective portal router in backend/app/api/detective_portal.py
- [ ] T056 [US5] Create detective dashboard endpoint GET /detective/dashboard in backend/app/api/detective_portal.py
- [ ] T057 [US5] Create investigation list endpoint GET /detective/cases in backend/app/api/detective_portal.py
- [ ] T058 [US5] Create field record endpoint POST /detective/cases/{id}/records in backend/app/api/detective_portal.py
- [ ] T058a [US5] [AUDIT] Add audit logging for field records and reports (Constitution Principle I) in backend/app/api/detective_portal.py
- [ ] T059 [US5] Create report submission endpoint POST /detective/cases/{id}/report in backend/app/api/detective_portal.py
- [ ] T060 [US5] Create DetectivePortalService in backend/app/services/detective_portal_service.py
- [ ] T061 [US5] Create detective portal schemas in backend/app/schemas/detective_portal.py
- [ ] T062 [US5] Register detective_portal router in backend/app/main.py

### Frontend Implementation for User Story 5

- [ ] T063 [P] [US5] Create detective portal layout in frontend/src/app/detective/layout.tsx
- [ ] T064 [P] [US5] Create DetectiveNav component in frontend/src/components/detective/DetectiveNav.tsx
- [ ] T065 [P] [US5] Create GPSTracker component with Kakao Maps in frontend/src/components/detective/GPSTracker.tsx
- [ ] T066 [P] [US5] Create FieldRecorder component in frontend/src/components/detective/FieldRecorder.tsx
- [ ] T067 [P] [US5] Create ReportEditor component in frontend/src/components/detective/ReportEditor.tsx
- [ ] T068 [US5] Create detective dashboard page in frontend/src/app/detective/dashboard/page.tsx
- [ ] T069 [US5] Create investigation detail page in frontend/src/app/detective/cases/[id]/page.tsx
- [ ] T070 [US5] Create field investigation page in frontend/src/app/detective/cases/[id]/field/page.tsx

**Checkpoint**: User Story 5 complete - detectives can manage investigations and record field data

---

## Phase 8: User Story 6 - Cross-Role Messaging (Priority: P3)

**Goal**: Enable real-time communication between lawyers, clients, and detectives

**Independent Test**: Send message from client to lawyer, verify real-time delivery and read receipt

### Backend Implementation for User Story 6

- [ ] T071 [US6] Create messaging router with WebSocket support in backend/app/api/messaging.py
- [ ] T072 [US6] Create MessagingService in backend/app/services/messaging_service.py
- [ ] T073 [US6] Create messaging schemas in backend/app/schemas/messaging.py
- [ ] T074 [US6] Register messaging router and WebSocket endpoint in backend/app/main.py
- [ ] T074a [US6] [AUDIT] Add audit logging for message send/read operations (Constitution Principle I) in backend/app/api/messaging.py

### Frontend Implementation for User Story 6

- [ ] T075 [P] [US6] Create MessageThread component in frontend/src/components/shared/MessageThread.tsx
- [ ] T076 [US6] Create useMessages hook with WebSocket in frontend/src/hooks/useMessages.ts

**Checkpoint**: User Story 6 complete - real-time messaging works across roles

---

## Phase 9: User Story 7 - Calendar Management (Priority: P3)

**Goal**: Create calendar system for lawyers with case-linked events

**Independent Test**: Create, view, and delete calendar events, verify case linkage

### Backend Implementation for User Story 7

- [ ] T077 [US7] Create calendar router in backend/app/api/calendar.py
- [ ] T078 [US7] Create CalendarService in backend/app/services/calendar_service.py
- [ ] T078a [US7] Register calendar router in backend/app/main.py
- [ ] T078b [US7] [AUDIT] Add audit logging for calendar CRUD operations (Constitution Principle I) in backend/app/api/calendar.py

### Frontend Implementation for User Story 7

- [ ] T079 [P] [US7] Create Calendar component using react-big-calendar in frontend/src/components/shared/Calendar.tsx
- [ ] T080 [US7] Create calendar page in frontend/src/app/lawyer/calendar/page.tsx

**Checkpoint**: User Story 7 complete - calendar management works

---

## Phase 10: User Story 8 - Billing System (Priority: P4)

**Goal**: Basic billing/invoice management

**Independent Test**: Create invoice, view client payment status

- [ ] T081 [US8] Create billing router and service in backend/app/api/billing.py
- [ ] T081a [US8] [AUDIT] Add audit logging for invoice creation and payment (Constitution Principle I) in backend/app/api/billing.py
- [ ] T082 [US8] Create billing page in frontend/src/app/lawyer/billing/page.tsx

**Checkpoint**: User Story 8 complete - basic billing works

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Performance optimization and edge case handling

- [ ] T083 [P] Add loading skeletons for all dashboard pages
- [ ] T084 [P] Add error boundaries for each portal
- [ ] T085 [P] Implement responsive design for mobile views
- [ ] T086 Add notification bell component with real-time updates in frontend/src/components/shared/NotificationBell.tsx
- [ ] T087 Create empty state components for lists
- [ ] T088 Run manual testing across all three portals and document issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on US1 completion (role routing)
- **User Story 3 (Phase 5)**: Depends on US2 completion (lawyer layout)
- **User Story 4 (Phase 6)**: Depends on US1 completion (client role)
- **User Story 5 (Phase 7)**: Depends on US1 completion (detective role)
- **User Story 6 (Phase 8)**: Depends on US4 and US5 (messaging between roles)
- **User Story 7 (Phase 9)**: Depends on US2 (lawyer portal)
- **User Story 8 (Phase 10)**: Depends on US4 (client billing view)
- **Polish (Phase 11)**: Depends on all user stories being complete

### User Story Dependencies

```
US1 (Roles) ──┬── US2 (Lawyer Dashboard) ── US3 (Case Mgmt) ── US7 (Calendar)
              │                                              └── US8 (Billing)
              ├── US4 (Client Portal) ──────────────┬── US6 (Messaging)
              └── US5 (Detective Portal) ───────────┘
```

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T006 || T007 || T008 || T009 - Different models

**Phase 3 (US1)**:
- T014 || T015 - Different files

**Phase 4 (US2)**:
- T022 || T023 || T024 || T025 - Different components

**Phase 5 (US3)**:
- T033 || T034 || T035 || T036 - Different components

**Phase 6 (US4)**:
- T048 || T049 || T050 || T051 - Different components

**Phase 7 (US5)**:
- T063 || T064 || T065 || T066 || T067 - Different components

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (roles, models)
3. Complete Phase 3: User Story 1 (role authentication)
4. Complete Phase 4: User Story 2 (lawyer dashboard)
5. Complete Phase 5: User Story 3 (case management)
6. **STOP and VALIDATE**: Test lawyer portal functionality
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational + US1 → Role system ready
2. Add US2 + US3 → Lawyer Portal MVP (Demo 1)
3. Add US4 → Client Portal (Demo 2)
4. Add US5 → Detective Portal (Demo 3)
5. Add US6 + US7 → Cross-cutting features (Demo 4)
6. Add US8 → Billing (Demo 5)

### Suggested MVP Scope

**Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5** = Minimum Viable Role-Based UI

This delivers:
- Role-based authentication (CLIENT, DETECTIVE)
- Lawyer dashboard with statistics
- Case list with filtering
- Case detail with evidence view
- Role-specific routing

---

## File Summary

### New Files to Create (50+ files)

| Category | Count |
|:---------|:-----:|
| Backend Routers | 5 |
| Backend Services | 6 |
| Backend Schemas | 6 |
| Frontend Pages | 15+ |
| Frontend Components | 20+ |
| Frontend Hooks | 5 |

### Key Backend Files

| File | Purpose |
|:-----|:--------|
| `backend/app/api/lawyer_portal.py` | Lawyer portal endpoints |
| `backend/app/api/client_portal.py` | Client portal endpoints |
| `backend/app/api/detective_portal.py` | Detective portal endpoints |
| `backend/app/api/messaging.py` | Real-time messaging |
| `backend/app/api/calendar.py` | Calendar management |

### Key Frontend Files

| File | Purpose |
|:-----|:--------|
| `frontend/src/app/lawyer/layout.tsx` | Lawyer portal layout |
| `frontend/src/app/client/layout.tsx` | Client portal layout |
| `frontend/src/app/detective/layout.tsx` | Detective portal layout |
| `frontend/src/middleware.ts` | Role-based routing |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after completion
- MVP = US1 + US2 + US3 (Lawyer Portal)
- Korean UTF-8 support required for all UI text
- Commit after each task or logical group
