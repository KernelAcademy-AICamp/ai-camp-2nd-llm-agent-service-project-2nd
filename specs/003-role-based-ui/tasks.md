# Tasks: Role-Based UI System

**Input**: Design documents from `/specs/003-role-based-ui/`
**Prerequisites**: plan.md ✓, spec.md ✓
**Screen Reference**: `docs/screens/SCREEN_DEFINITION.md`

**Tests**: TDD approach requested. Test tasks included for each user story.

**TDD Cycle**: RED → GREEN → REFACTOR
- Write tests FIRST (they must FAIL initially)
- Implement minimum code to pass tests
- Refactor while tests stay GREEN

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Summary

| Metric | Value |
|:-------|:------|
| Total Tasks | 154 |
| Test Tasks | 40 |
| Implementation Tasks | 106 |
| Setup Tasks | 4 |
| Polish Tasks | 8 |
| User Story 1 Tasks | 14 (6 tests + 8 impl) |
| User Story 2 Tasks | 14 (4 tests + 10 impl) |
| User Story 3 Tasks | 16 (4 tests + 12 impl) |
| User Story 4 Tasks | 22 (6 tests + 16 impl) |
| User Story 5 Tasks | 29 (8 tests + 21 impl) |
| User Story 6 Tasks | 19 (6 tests + 13 impl) |
| User Story 7 Tasks | 16 (4 tests + 12 impl) |
| User Story 8 Tasks | 13 (2 tests + 11 impl) |
| Parallel Opportunities | 48 |
| Audit Compliance Tasks | 5 |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for role-based UI

- [X] T001 Create feature branch `003-role-based-ui` from dev
- [X] T002 [P] Install frontend dependencies (recharts, react-big-calendar, @kakao/kakao-maps-sdk) in frontend/package.json
- [X] T003 [P] Create Alembic migration for new tables (messages, calendar_events, investigation_records, invoices) in backend/alembic/versions/
- [X] T004 Run database migration and verify schema

**Checkpoint**: Environment ready for development

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add CLIENT and DETECTIVE to UserRole enum in backend/app/db/models.py
- [X] T006 [P] Create Message model in backend/app/db/models.py
- [X] T007 [P] Create CalendarEvent model in backend/app/db/models.py
- [X] T008 [P] Create InvestigationRecord model in backend/app/db/models.py
- [X] T009 [P] Create Invoice model in backend/app/db/models.py
- [X] T010 Update role permissions in backend/app/db/schemas.py to include CLIENT and DETECTIVE

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Role & Auth System Extension (Priority: P1)

**Goal**: Extend authentication system with CLIENT and DETECTIVE roles

**Independent Test**: Create test users with CLIENT/DETECTIVE roles and verify role-based routing works correctly

### Tests for User Story 1 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [X] T011 [P] [US1] Contract test for role validation helper in backend/tests/contract/test_role_validation.py
- [X] T012 [P] [US1] Contract test for signup endpoint with CLIENT/DETECTIVE roles in backend/tests/contract/test_auth_roles.py
- [X] T013 [P] [US1] Contract test for role-based permission checks in backend/tests/contract/test_case_permissions.py
- [X] T014 [P] [US1] Integration test for role-based routing middleware in frontend/src/__tests__/middleware.test.ts
- [X] T015 [P] [US1] Integration test for useRole hook in frontend/src/__tests__/hooks/useRole.test.ts
- [X] T016 [P] [US1] Integration test for RoleGuard component in frontend/src/__tests__/components/RoleGuard.test.tsx

### Backend Implementation for User Story 1

- [X] T017 [US1] Update signup endpoint to accept CLIENT and DETECTIVE roles in backend/app/api/auth.py
- [X] T018 [US1] Create role validation helper function in backend/app/core/dependencies.py
- [X] T019 [US1] Add role-based permission checks to existing endpoints in backend/app/api/cases.py

### Frontend Implementation for User Story 1

- [X] T020 [P] [US1] Create role redirect logic after login in frontend/src/app/(auth)/login/page.tsx
- [X] T021 [P] [US1] Create middleware for role-based routing in frontend/src/middleware.ts
- [X] T022 [US1] Create useRole hook for role checking in frontend/src/hooks/useRole.ts
- [X] T023 [US1] Update AuthContext to include role information in frontend/src/contexts/AuthContext.tsx
- [X] T024 [US1] Create RoleGuard component for protected routes in frontend/src/components/auth/RoleGuard.tsx

**Checkpoint**: User Story 1 complete - role-based authentication works (all tests GREEN)

---

## Phase 4: User Story 2 - Lawyer Dashboard (Priority: P1) - MVP

**Goal**: Create lawyer dashboard with case overview and statistics

**Independent Test**: Login as lawyer and verify dashboard displays correct statistics, recent cases, and calendar events

### Tests for User Story 2 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [X] T025 [P] [US2] Contract test for GET /lawyer/dashboard endpoint in backend/tests/contract/test_lawyer_dashboard.py
- [ ] T026 [P] [US2] Contract test for dashboard stats calculation in backend/tests/unit/test_lawyer_dashboard_service.py
- [X] T027 [P] [US2] Integration test for lawyer dashboard page rendering in frontend/src/__tests__/app/lawyer/dashboard.test.tsx
- [ ] T028 [P] [US2] Integration test for StatsCard component in frontend/src/__tests__/components/lawyer/StatsCard.test.tsx

### Backend Implementation for User Story 2

- [X] T029 [US2] Create dashboard stats endpoint GET /lawyer/dashboard in backend/app/api/lawyer_portal.py
- [X] T030 [US2] Create LawyerDashboardService with stats calculation in backend/app/services/lawyer_dashboard_service.py
- [X] T031 [US2] Create dashboard schemas (StatsCard, RecentCase, etc.) in backend/app/schemas/lawyer_dashboard.py

### Frontend Implementation for User Story 2

- [X] T032 [P] [US2] Create lawyer portal layout in frontend/src/app/lawyer/layout.tsx
- [X] T033 [P] [US2] Create LawyerNav component with menu items in frontend/src/components/lawyer/LawyerNav.tsx
- [X] T034 [P] [US2] Create StatsCard component in frontend/src/components/lawyer/StatsCard.tsx
- [X] T035 [P] [US2] Create CaseStatsChart component using Recharts in frontend/src/components/charts/CaseStatsChart.tsx
- [X] T036 [US2] Create lawyer dashboard page in frontend/src/app/lawyer/dashboard/page.tsx
- [X] T037 [US2] Create useLawyerDashboard hook in frontend/src/hooks/useLawyerDashboard.ts
- [X] T038 [US2] Register lawyer_portal router in backend/app/main.py

**Checkpoint**: User Story 2 complete - lawyer dashboard displays statistics and recent activity (all tests GREEN)

---

## Phase 5: User Story 3 - Lawyer Case Management (Priority: P1) - MVP

**Goal**: Enable lawyers to manage cases with filtering and bulk actions

**Independent Test**: List cases with various filters, perform bulk AI analysis request, view case detail with evidence

### Tests for User Story 3 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [X] T039 [P] [US3] Contract test for GET /lawyer/cases with filters in backend/tests/contract/test_lawyer_cases.py
- [X] T040 [P] [US3] Contract test for POST /lawyer/cases/bulk-action in backend/tests/contract/test_bulk_actions.py
- [ ] T041 [P] [US3] Integration test for CaseTable with sorting in frontend/src/__tests__/components/lawyer/CaseTable.test.tsx
- [ ] T042 [P] [US3] Integration test for case list page filtering in frontend/src/__tests__/app/lawyer/cases.test.tsx

### Backend Implementation for User Story 3

- [X] T043 [US3] Create case list endpoint with filters GET /lawyer/cases in backend/app/api/lawyer_portal.py
- [X] T044 [US3] Add bulk action endpoint POST /lawyer/cases/bulk-action in backend/app/api/lawyer_portal.py
- [X] T045 [US3] Create CaseListService with filtering logic in backend/app/services/case_list_service.py
- [X] T046 [US3] Create case list schemas (CaseFilter, CaseListItem, BulkAction) in backend/app/schemas/case_list.py

### Frontend Implementation for User Story 3

- [X] T047 [P] [US3] Create CaseCard component in frontend/src/components/lawyer/CaseCard.tsx
- [X] T048 [P] [US3] Create CaseTable component with sorting in frontend/src/components/lawyer/CaseTable.tsx
- [X] T049 [P] [US3] Create CaseFilter component in frontend/src/components/lawyer/CaseFilter.tsx
- [X] T050 [P] [US3] Create BulkActionBar component in frontend/src/components/lawyer/BulkActionBar.tsx
- [X] T051 [US3] Create case list page in frontend/src/app/lawyer/cases/page.tsx
- [X] T052 [US3] Create case detail page in frontend/src/app/lawyer/cases/[id]/page.tsx
- [X] T053 [US3] Create useCaseList hook with filtering in frontend/src/hooks/useCaseList.ts
- [X] T054 [US3] Integrate evidence list and AI summary display in case detail page

**Checkpoint**: User Story 3 complete - lawyers can manage cases with full filtering and bulk actions (all tests GREEN)

---

## Phase 6: User Story 4 - Client Portal (Priority: P2)

**Goal**: Create client portal for case tracking and evidence submission

**Independent Test**: Login as client, view case progress, upload evidence, send message to lawyer

### Tests for User Story 4 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [ ] T055 [P] [US4] Contract test for GET /client/dashboard in backend/tests/contract/test_client_dashboard.py
- [ ] T056 [P] [US4] Contract test for GET /client/cases and GET /client/cases/{id} in backend/tests/contract/test_client_cases.py
- [ ] T057 [P] [US4] Contract test for POST /client/cases/{id}/evidence in backend/tests/contract/test_client_evidence.py
- [ ] T058 [P] [US4] Integration test for client dashboard page in frontend/src/__tests__/app/client/dashboard.test.tsx
- [ ] T059 [P] [US4] Integration test for ProgressTracker component in frontend/src/__tests__/components/client/ProgressTracker.test.tsx
- [ ] T060 [P] [US4] Integration test for EvidenceUploader component in frontend/src/__tests__/components/client/EvidenceUploader.test.tsx

### Backend Implementation for User Story 4

- [ ] T061 [US4] Create client portal router in backend/app/api/client_portal.py
- [ ] T062 [US4] Create client dashboard endpoint GET /client/dashboard in backend/app/api/client_portal.py
- [ ] T063 [US4] Create client case list endpoint GET /client/cases in backend/app/api/client_portal.py
- [ ] T064 [US4] Create client case view endpoint GET /client/cases/{id} in backend/app/api/client_portal.py
- [ ] T065 [US4] Create client evidence upload endpoint POST /client/cases/{id}/evidence in backend/app/api/client_portal.py
- [ ] T066 [US4] [AUDIT] Add audit logging for evidence upload (Constitution Principle I) in backend/app/api/client_portal.py
- [ ] T067 [US4] Create ClientPortalService in backend/app/services/client_portal_service.py
- [ ] T068 [US4] Create client portal schemas in backend/app/schemas/client_portal.py
- [ ] T069 [US4] Register client_portal router in backend/app/main.py

### Frontend Implementation for User Story 4

- [X] T070 [P] [US4] Create client portal layout in frontend/src/app/client/layout.tsx
- [ ] T071 [P] [US4] Create ClientNav component in frontend/src/components/client/ClientNav.tsx
- [ ] T072 [P] [US4] Create ProgressTracker component in frontend/src/components/client/ProgressTracker.tsx
- [ ] T073 [P] [US4] Create EvidenceUploader component in frontend/src/components/client/EvidenceUploader.tsx
- [X] T074 [US4] Create client dashboard page in frontend/src/app/client/dashboard/page.tsx
- [ ] T075 [US4] Create client case detail page in frontend/src/app/client/cases/[id]/page.tsx
- [ ] T076 [US4] Create evidence submission page in frontend/src/app/client/cases/[id]/evidence/page.tsx

**Checkpoint**: User Story 4 complete - clients can view cases and submit evidence (all tests GREEN)

---

## Phase 7: User Story 5 - Detective Portal (Priority: P2)

**Goal**: Create detective portal for investigation management and field recording

**Independent Test**: Login as detective, view assigned investigations, record field data with GPS, submit report

### Tests for User Story 5 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [ ] T077 [P] [US5] Contract test for GET /detective/dashboard in backend/tests/contract/test_detective_dashboard.py
- [ ] T078 [P] [US5] Contract test for GET /detective/cases and GET /detective/cases/{id} in backend/tests/contract/test_detective_cases.py
- [ ] T079 [P] [US5] Contract test for POST /detective/cases/{id}/accept, /reject in backend/tests/contract/test_detective_actions.py
- [ ] T080 [P] [US5] Contract test for POST /detective/cases/{id}/records and /report in backend/tests/contract/test_detective_records.py
- [ ] T081 [P] [US5] Contract test for GET /detective/earnings in backend/tests/contract/test_detective_earnings.py
- [ ] T082 [P] [US5] Integration test for detective dashboard page in frontend/src/__tests__/app/detective/dashboard.test.tsx
- [ ] T083 [P] [US5] Integration test for GPSTracker component in frontend/src/__tests__/components/detective/GPSTracker.test.tsx
- [ ] T084 [P] [US5] Integration test for FieldRecorder component in frontend/src/__tests__/components/detective/FieldRecorder.test.tsx

### Backend Implementation for User Story 5

- [ ] T085 [US5] Create detective portal router in backend/app/api/detective_portal.py
- [ ] T086 [US5] Create detective dashboard endpoint GET /detective/dashboard in backend/app/api/detective_portal.py
- [ ] T087 [US5] Create investigation list endpoint GET /detective/cases in backend/app/api/detective_portal.py
- [ ] T088 [US5] Create investigation detail endpoint GET /detective/cases/{id} in backend/app/api/detective_portal.py
- [ ] T089 [US5] Create accept/reject endpoints POST /detective/cases/{id}/accept, /reject in backend/app/api/detective_portal.py
- [ ] T090 [US5] Create field record endpoint POST /detective/cases/{id}/records in backend/app/api/detective_portal.py
- [ ] T091 [US5] [AUDIT] Add audit logging for field records and reports (Constitution Principle I) in backend/app/api/detective_portal.py
- [ ] T092 [US5] Create report submission endpoint POST /detective/cases/{id}/report in backend/app/api/detective_portal.py
- [ ] T093 [US5] Create earnings endpoint GET /detective/earnings in backend/app/api/detective_portal.py
- [ ] T094 [US5] Create DetectivePortalService in backend/app/services/detective_portal_service.py
- [ ] T095 [US5] Create detective portal schemas in backend/app/schemas/detective_portal.py
- [ ] T096 [US5] Register detective_portal router in backend/app/main.py

### Frontend Implementation for User Story 5

- [X] T097 [P] [US5] Create detective portal layout in frontend/src/app/detective/layout.tsx
- [ ] T098 [P] [US5] Create DetectiveNav component in frontend/src/components/detective/DetectiveNav.tsx
- [ ] T099 [P] [US5] Create GPSTracker component with Kakao Maps in frontend/src/components/detective/GPSTracker.tsx
- [ ] T100 [P] [US5] Create FieldRecorder component in frontend/src/components/detective/FieldRecorder.tsx
- [ ] T101 [P] [US5] Create ReportEditor component in frontend/src/components/detective/ReportEditor.tsx
- [X] T102 [US5] Create detective dashboard page in frontend/src/app/detective/dashboard/page.tsx
- [ ] T103 [US5] Create investigation detail page in frontend/src/app/detective/cases/[id]/page.tsx
- [ ] T104 [US5] Create field investigation page in frontend/src/app/detective/cases/[id]/field/page.tsx
- [ ] T105 [US5] Create earnings page in frontend/src/app/detective/earnings/page.tsx

**Checkpoint**: User Story 5 complete - detectives can manage investigations and record field data (all tests GREEN)

---

## Phase 8: User Story 6 - Cross-Role Messaging (Priority: P3)

**Goal**: Enable real-time communication between lawyers, clients, and detectives

**Independent Test**: Send message from client to lawyer, verify real-time delivery and read receipt

### Tests for User Story 6 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [ ] T106 [P] [US6] Contract test for GET /messages/{caseId} in backend/tests/contract/test_messaging_read.py
- [ ] T107 [P] [US6] Contract test for POST /messages and PUT /messages/{id}/read in backend/tests/contract/test_messaging_write.py
- [ ] T108 [P] [US6] Contract test for POST /messages/upload (attachment presigned URL) in backend/tests/contract/test_messaging_upload.py
- [ ] T109 [P] [US6] WebSocket connection test for /ws/messages/{caseId} in backend/tests/integration/test_websocket_messaging.py
- [ ] T110 [P] [US6] Integration test for MessageThread component in frontend/src/__tests__/components/shared/MessageThread.test.tsx
- [ ] T111 [P] [US6] Integration test for useMessages hook with WebSocket in frontend/src/__tests__/hooks/useMessages.test.ts

### Backend Implementation for User Story 6

- [ ] T112 [US6] Create messaging router with REST endpoints in backend/app/api/messaging.py
- [ ] T113 [US6] Create GET /messages/{caseId}, POST /messages endpoints in backend/app/api/messaging.py
- [ ] T114 [US6] Create PUT /messages/{id}/read endpoint in backend/app/api/messaging.py
- [ ] T115 [US6] Create POST /messages/upload for attachment presigned URLs in backend/app/api/messaging.py
- [ ] T116 [US6] Create WebSocket endpoint /ws/messages/{caseId} with ConnectionManager in backend/app/api/messaging.py
- [ ] T117 [US6] Create MessagingService with optimistic update support in backend/app/services/messaging_service.py
- [ ] T118 [US6] Create messaging schemas in backend/app/schemas/messaging.py
- [ ] T119 [US6] Register messaging router and WebSocket endpoint in backend/app/main.py
- [ ] T120 [US6] [AUDIT] Add audit logging for message send/read operations (Constitution Principle I) in backend/app/api/messaging.py

### Frontend Implementation for User Story 6

- [ ] T121 [P] [US6] Create MessageThread component in frontend/src/components/shared/MessageThread.tsx
- [ ] T122 [P] [US6] Create MessageInput component with attachment support in frontend/src/components/shared/MessageInput.tsx
- [ ] T123 [US6] Create useMessages hook with WebSocket reconnection in frontend/src/hooks/useMessages.ts
- [ ] T124 [US6] Create messages page for each portal in frontend/src/app/[role]/messages/page.tsx

**Checkpoint**: User Story 6 complete - real-time messaging works across roles (all tests GREEN)

---

## Phase 9: User Story 7 - Calendar Management (Priority: P3)

**Goal**: Create calendar system for lawyers with case-linked events

**Independent Test**: Create, view, and delete calendar events, verify case linkage

### Tests for User Story 7 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [ ] T125 [P] [US7] Contract test for GET /calendar/events with date range filter in backend/tests/contract/test_calendar_read.py
- [ ] T126 [P] [US7] Contract test for POST, PUT, DELETE /calendar/events in backend/tests/contract/test_calendar_write.py
- [ ] T127 [P] [US7] Integration test for Calendar component in frontend/src/__tests__/components/shared/Calendar.test.tsx
- [ ] T128 [P] [US7] Integration test for useCalendar hook in frontend/src/__tests__/hooks/useCalendar.test.ts

### Backend Implementation for User Story 7

- [ ] T129 [US7] Create calendar router with CRUD endpoints in backend/app/api/calendar.py
- [ ] T130 [US7] Create GET /calendar/events endpoint with date range filter in backend/app/api/calendar.py
- [ ] T131 [US7] Create POST, PUT, DELETE /calendar/events endpoints in backend/app/api/calendar.py
- [ ] T132 [US7] Create GET /calendar/upcoming endpoint (next 7 days) in backend/app/api/calendar.py
- [ ] T133 [US7] Create GET /calendar/reminders endpoint in backend/app/api/calendar.py
- [ ] T134 [US7] Create CalendarService with event type colors in backend/app/services/calendar_service.py
- [ ] T135 [US7] Register calendar router in backend/app/main.py
- [ ] T136 [US7] [AUDIT] Add audit logging for calendar CRUD operations (Constitution Principle I) in backend/app/api/calendar.py

### Frontend Implementation for User Story 7

- [ ] T137 [P] [US7] Create Calendar component using react-big-calendar with Korean locale in frontend/src/components/shared/Calendar.tsx
- [ ] T138 [P] [US7] Create EventForm component for creating/editing events in frontend/src/components/shared/EventForm.tsx
- [ ] T139 [US7] Create calendar page in frontend/src/app/lawyer/calendar/page.tsx
- [ ] T140 [US7] Create useCalendar hook with SWR in frontend/src/hooks/useCalendar.ts

**Checkpoint**: User Story 7 complete - calendar management works (all tests GREEN)

---

## Phase 10: User Story 8 - Billing System (Priority: P4)

**Goal**: Basic billing/invoice management

**Independent Test**: Create invoice, view client payment status

### Tests for User Story 8 (Write FIRST, ensure they FAIL) ⚠️

> **TDD RED Phase**: These tests MUST fail before implementation

- [ ] T141 [P] [US8] Contract test for invoice CRUD and payment endpoints in backend/tests/contract/test_billing.py
- [ ] T142 [P] [US8] Integration test for InvoiceList and InvoiceForm components in frontend/src/__tests__/components/lawyer/Invoice.test.tsx

### Backend Implementation for User Story 8

- [ ] T143 [US8] Create billing router in backend/app/api/billing.py
- [ ] T144 [US8] Create invoice CRUD endpoints in backend/app/api/billing.py
- [ ] T145 [US8] Create payment initiation endpoint POST /client/billing/{id}/pay in backend/app/api/billing.py
- [ ] T146 [US8] Create BillingService with invoice number generation in backend/app/services/billing_service.py
- [ ] T147 [US8] Create billing schemas in backend/app/schemas/billing.py
- [ ] T148 [US8] [AUDIT] Add audit logging for invoice creation and payment (Constitution Principle I) in backend/app/api/billing.py

### Frontend Implementation for User Story 8

- [ ] T149 [P] [US8] Create InvoiceList component in frontend/src/components/lawyer/InvoiceList.tsx
- [ ] T150 [P] [US8] Create InvoiceForm component in frontend/src/components/lawyer/InvoiceForm.tsx
- [ ] T151 [US8] Create billing page in frontend/src/app/lawyer/billing/page.tsx
- [ ] T152 [US8] Create client billing page in frontend/src/app/client/billing/page.tsx
- [ ] T153 [US8] Create useBilling hook in frontend/src/hooks/useBilling.ts

**Checkpoint**: User Story 8 complete - basic billing works (all tests GREEN)

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Performance optimization and edge case handling

- [ ] T154 [P] Add loading skeletons for all dashboard pages
- [ ] T155 [P] Add error boundaries for each portal
- [ ] T156 [P] Implement responsive design for mobile views
- [ ] T157 Add notification bell component with real-time updates in frontend/src/components/shared/NotificationBell.tsx
- [ ] T158 Create empty state components for lists
- [ ] T159 Run quickstart.md validation (all setup steps work)
- [ ] T160 Run manual testing across all three portals and document issues
- [ ] T161 Validate contract compliance (OpenAPI specs match implementation)

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

### TDD Execution Order (Per User Story)

```
1. Write ALL tests for the user story (RED phase - tests FAIL)
2. Run tests to verify they FAIL correctly
3. Implement backend code (GREEN phase - tests pass)
4. Implement frontend code (GREEN phase - tests pass)
5. Refactor while keeping tests GREEN
6. Move to next user story
```

### User Story Dependencies

```
US1 (Roles) ──┬── US2 (Lawyer Dashboard) ── US3 (Case Mgmt) ── US7 (Calendar)
              │                                              └── US8 (Billing)
              ├── US4 (Client Portal) ──────────────┬── US6 (Messaging)
              └── US5 (Detective Portal) ───────────┘
```

### Parallel Opportunities

**Phase 3 (US1) Tests**:
- T011 || T012 || T013 || T014 || T015 || T016 - All test files

**Phase 4 (US2) Tests**:
- T025 || T026 || T027 || T028 - All test files

**Phase 5 (US3) Tests**:
- T039 || T040 || T041 || T042 - All test files

**Phase 6 (US4) Tests**:
- T055 || T056 || T057 || T058 || T059 || T060 - All test files

**Phase 7 (US5) Tests**:
- T077 || T078 || T079 || T080 || T081 || T082 || T083 || T084 - All test files

**Phase 8 (US6) Tests**:
- T106 || T107 || T108 || T109 || T110 || T111 - All test files

**Phase 9 (US7) Tests**:
- T125 || T126 || T127 || T128 - All test files

**Phase 10 (US8) Tests**:
- T141 || T142 - All test files

---

## Implementation Strategy

### TDD MVP First (US1 + US2 + US3)

1. **Phase 1**: Setup (T001-T004)
2. **Phase 2**: Foundational (T005-T010)
3. **US1 TDD Cycle**:
   - Write tests T011-T016 (RED - all fail)
   - Implement T017-T024 (GREEN - all pass)
4. **US2 TDD Cycle**:
   - Write tests T025-T028 (RED - all fail)
   - Implement T029-T038 (GREEN - all pass)
5. **US3 TDD Cycle**:
   - Write tests T039-T042 (RED - all fail)
   - Implement T043-T054 (GREEN - all pass)
6. **STOP and VALIDATE**: All MVP tests GREEN, manual testing
7. Deploy/demo if ready

### Incremental TDD Delivery

1. Setup + Foundational → Environment ready
2. US1 TDD → Role system ready (Demo 1)
3. US2 + US3 TDD → Lawyer Portal MVP (Demo 2)
4. US4 TDD → Client Portal (Demo 3)
5. US5 TDD → Detective Portal (Demo 4)
6. US6 + US7 TDD → Cross-cutting features (Demo 5)
7. US8 TDD → Billing (Demo 6)

---

## File Summary

### Test Files to Create (40 files)

| Category | Count |
|:---------|:-----:|
| Backend Contract Tests | 18 |
| Backend Unit Tests | 1 |
| Backend Integration Tests | 1 |
| Frontend Integration Tests | 20 |

### Implementation Files (50+ files)

| Category | Count |
|:---------|:-----:|
| Backend Routers | 5 |
| Backend Services | 6 |
| Backend Schemas | 6 |
| Frontend Pages | 15+ |
| Frontend Components | 20+ |
| Frontend Hooks | 8 |

### Key Test Files (Backend)

| File | Purpose |
|:-----|:--------|
| `backend/tests/contract/test_role_validation.py` | US1 role validation |
| `backend/tests/contract/test_lawyer_dashboard.py` | US2 dashboard endpoint |
| `backend/tests/contract/test_lawyer_cases.py` | US3 case list endpoint |
| `backend/tests/contract/test_client_*.py` | US4 client endpoints |
| `backend/tests/contract/test_detective_*.py` | US5 detective endpoints |
| `backend/tests/contract/test_messaging_*.py` | US6 messaging endpoints |
| `backend/tests/contract/test_calendar_*.py` | US7 calendar endpoints |
| `backend/tests/contract/test_billing.py` | US8 billing endpoints |

### Key Test Files (Frontend)

| File | Purpose |
|:-----|:--------|
| `frontend/src/__tests__/middleware.test.ts` | US1 role routing |
| `frontend/src/__tests__/app/lawyer/dashboard.test.tsx` | US2 dashboard |
| `frontend/src/__tests__/app/lawyer/cases.test.tsx` | US3 case list |
| `frontend/src/__tests__/components/client/*.test.tsx` | US4 client components |
| `frontend/src/__tests__/components/detective/*.test.tsx` | US5 detective components |
| `frontend/src/__tests__/components/shared/MessageThread.test.tsx` | US6 messaging |
| `frontend/src/__tests__/components/shared/Calendar.test.tsx` | US7 calendar |

---

## Notes

- **TDD Cycle**: RED → GREEN → REFACTOR for each user story
- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tests MUST fail before implementation begins
- Each user story is independently testable after completion
- MVP = US1 + US2 + US3 (Lawyer Portal)
- Korean UTF-8 support required for all UI text
- Commit after each TDD phase (tests, implementation, refactor)
