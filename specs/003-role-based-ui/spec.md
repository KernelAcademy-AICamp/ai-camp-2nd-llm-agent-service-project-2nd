# Feature Specification: Role-Based UI System

**Feature ID**: 003-role-based-ui
**Version**: 1.0.0
**Status**: Complete

---

## Overview

Legal Evidence Hub의 역할 기반 UI 시스템 구현. 변호사(Lawyer), 의뢰인(Client), 탐정(Detective) 3가지 역할에 대한 전용 포털 및 화면 구현.

## User Stories

### US1: 역할 및 인증 시스템 확장 (Priority: P1) - Foundation

**As a** system administrator
**I want to** have CLIENT and DETECTIVE roles in the system
**So that** different users can access role-specific features

**Acceptance Criteria:**
- [X] UserRole enum에 CLIENT, DETECTIVE 추가
- [X] 역할별 권한 정의 (RolePermissions)
- [X] 역할 기반 라우팅 미들웨어
- [X] 로그인 후 역할별 리다이렉션

---

### US2: 변호사 대시보드 (Priority: P1) - MVP

**As a** lawyer
**I want to** see my case overview on a dashboard
**So that** I can quickly understand my workload and priorities

**Acceptance Criteria:**
- [X] 진행중/검토필요/완료 케이스 통계 카드
- [X] 최근 케이스 목록 (5건)
- [X] 오늘/이번주 일정 요약
- [X] 최근 알림 피드
- [X] 월간 업무 통계 차트

**Screen Reference:** L-01 in SCREEN_DEFINITION.md

---

### US3: 변호사 케이스 관리 (Priority: P1) - MVP

**As a** lawyer
**I want to** manage my cases with filtering and bulk actions
**So that** I can efficiently handle multiple cases

**Acceptance Criteria:**
- [X] 케이스 목록 테이블/카드 뷰
- [X] 검색 및 필터 (유형/상태/기간/키워드)
- [X] 일괄 선택 및 작업 (AI 분석, 상태 변경)
- [X] 케이스 상세 페이지
- [X] 증거 목록 및 AI 요약 표시

**Screen Reference:** L-02, L-03 in SCREEN_DEFINITION.md

---

### US4: 의뢰인 포털 (Priority: P2)

**As a** client
**I want to** view my case status and communicate with my lawyer
**So that** I can stay informed about my case progress

**Acceptance Criteria:**
- [X] 의뢰인 대시보드 (케이스 진행 상황)
- [X] 진행 단계 시각화 (Progress Bar)
- [X] 증거 제출 페이지 (드래그&드롭)
- [X] 변호사 소통 메시지
- [X] 일정 및 알림 확인

**Screen Reference:** C-01 ~ C-05 in SCREEN_DEFINITION.md

---

### US5: 탐정 포털 (Priority: P2)

**As a** detective
**I want to** manage investigation requests and submit evidence
**So that** I can support lawyers with investigation tasks

**Acceptance Criteria:**
- [X] 탐정 대시보드 (의뢰 현황, 수익 요약)
- [X] 의뢰 목록 및 상세 (수락/거절)
- [X] 증거 업로드 (기존 Evidence 시스템 활용)
- [X] 조사 보고서 작성 및 제출
- [X] 정산/수익 확인

**Screen Reference:** D-01 ~ D-06 in SCREEN_DEFINITION.md

**Note:** GPS 추적 및 현장 기록 기능은 플랫폼 범위 외로 제외됨. LEH는 증거 수집/관리/분석 플랫폼이며, 현장 채집 도구가 아님.

---

### US6: 역할 간 소통 시스템 (Priority: P3)

**As a** user (lawyer/client/detective)
**I want to** communicate with other parties in real-time
**So that** we can coordinate on case activities

**Acceptance Criteria:**
- [X] 실시간 메시지 (WebSocket)
- [X] 파일 첨부 기능
- [X] 읽음 확인
- [X] 알림 푸시
- [X] **메시지 영구 저장** (DB에 모든 메시지 저장)
- [X] **오프라인 큐** (접속 시 읽지 않은 메시지 전달)

**Screen Reference:** L-11, C-05, D-07 in SCREEN_DEFINITION.md

---

### US7: 일정 관리 (Priority: P3)

**As a** lawyer
**I want to** manage my calendar with case-linked events
**So that** I never miss important court dates or meetings

**Acceptance Criteria:**
- [X] 월/주/일 캘린더 뷰
- [X] 케이스 연동 일정
- [X] 리마인더 알림
- [X] 일정 유형별 색상 구분

**Screen Reference:** L-09 in SCREEN_DEFINITION.md

---

### US8: 청구/정산 시스템 (Priority: P4)

**As a** lawyer
**I want to** manage billing for my cases
**So that** I can track payments and invoices

**Acceptance Criteria:**
- [X] 착수금/성공보수 관리
- [X] 청구서 생성
- [X] 결제 현황 추적
- [X] 의뢰인 결제 페이지

**Screen Reference:** L-10, C-07 in SCREEN_DEFINITION.md

---

## Out of Scope

- Admin 역할 화면 (기존 구현 유지)
- 결제 게이트웨이 연동 (Phase 2)
- 모바일 앱 (웹 반응형으로 대체)

## Dependencies

- 기존 인증 시스템 (JWT)
- 기존 케이스/증거 API
- 타임라인 기능 (002-evidence-timeline)

## Technical Notes

- Frontend: Next.js 14 App Router
- Backend: FastAPI
- Real-time: WebSocket (FastAPI)
- State: React Context + SWR

## Data Model

### Case Status Lifecycle
```
OPEN → IN_PROGRESS → REVIEW → CLOSED
```
- **OPEN**: 신규 케이스 생성 시 초기 상태
- **IN_PROGRESS**: 변호사가 작업 중인 케이스
- **REVIEW**: AI 분석 완료 후 검토 대기 상태
- **CLOSED**: 종료된 케이스

### Role-Based Permissions

| Role | Case Access | Evidence | Reports | Scope |
|------|-------------|----------|---------|-------|
| **Lawyer** | Full CRUD | Full CRUD | Full CRUD | All assigned cases |
| **Client** | Read only | Read + Submit | Read only | Own cases only |
| **Detective** | Read only | Read + Submit | Read + Submit | Assigned investigations only |

---

## Clarifications

### Session 2024-12-04
- Q: 케이스 상태 전환(lifecycle) 흐름은? → A: OPEN → IN_PROGRESS → REVIEW → CLOSED (검토 단계 포함)
- Q: 역할별 권한 모델은? → A: Lawyer: Full CRUD / Client: Read + Submit evidence / Detective: Read + Submit reports (assigned only)
- Q: 실시간 메시지 저장 방식은? → A: DB 영구 저장 + 오프라인 큐 (접속 시 읽지 않은 메시지 전달)
