# LEH 서비스 구현 현황

**최종 업데이트:** 2025-12-12
**현재 브랜치:** `011-production-bug-fixes`
**참고 문서:** `docs/IDEAS_IMPLEMENTATION_PLAN.md`, `docs/guides/plan.md`

---

## 이번 스프린트 요약 (011-production-bug-fixes)

| 상태 | 항목 | 내용 |
|------|------|------|
| ✅ 완료 | `useBeforeUnload` 도입 | InvoiceForm/EventForm에 공통 훅 적용, 더티 상태 확인 후 confirmNavigation 수행 |
| ✅ 완료 | 모달 URL 동기화 | Billing/Calendar 페이지의 생성·수정 모달을 `useModalState`로 이관, 뒤로가기와 deep link 지원 |
| ✅ 완료 | Landing/Login 네비게이션 | `LandingNav` 에 인증 상태 주입, 로그인 사용자는 로그아웃 CTA 노출 |
| ⚠️ 모니터링 | 모달 딥링크 UX | URL에서 바로 열린 모달을 닫을 때 `router.back()`이 이전 페이지로 이동할 수 있어 QA 필요 |

### 완료된 작업
- `frontend/src/components/lawyer/InvoiceForm.tsx`  
  - `handleCancel` 경유로 취소 버튼을 통합해 `useBeforeUnload` 경고가 항상 노출되도록 수정.
- `frontend/src/app/lawyer/billing/page.tsx`, `frontend/src/app/lawyer/calendar/page.tsx`  
  - `useModalState` 기반으로 모달을 열고 닫아 URL 파라미터와 브라우저 히스토리를 일치.
  - Billing/Calendar 양쪽에서 동일한 모달 컴포넌트(`Modal`) 사용.
- `frontend/src/app/login/page.tsx`, `frontend/src/app/page.tsx`, `frontend/src/components/landing/LandingNav.tsx`  
  - Landing 헤더를 로그인 페이지에서도 재사용하고, 인증 상태에 따라 로그인/로그아웃 CTA 토글.

### 남은 리스크 / TODO
1. **모달 딥링크 UX** – `useModalState`의 기본 `router.back()` 동작이 URL로 직접 진입한 사용자를 이전 페이지로 되돌릴 수 있음. QA 후 필요 시 `replace` 옵션 고려.
2. **로그아웃 실패 핸들링** – LandingNav에서 로그아웃 실패 시 사용자 알림 미구현. 토스트/Alert 추가 검토.
3. **문서 반영 범위 확대** – `docs/guides/plan.md` TDD 섹션은 Phase 기반이라 최신 버그픽스 플로우와 괴리가 있음. 차기 스프린트에서 정리.

### QA & 모니터링
- Billing ↔ Calendar 모달을 URL 파라미터로 직접 열고, 뒤로가기로 닫히는지 수동 확인.
- Invoice/Event 폼에서 값 수정 후 창/라우팅 시도 시 confirm 다이얼로그가 노출되는지 브라우저별 확인.
- 로그인 상태에서 Landing → 로그아웃 → 로그인 화면 이동 플로우 리그레션 테스트.

### 참고 이슈 / 파일
- Hooks: `frontend/src/hooks/useModalState.ts`, `frontend/src/hooks/useBeforeUnload.ts`
- UI: `frontend/src/components/primitives/Modal/Modal.tsx`
- Auth: `frontend/src/contexts/AuthContext.tsx`, `frontend/src/hooks/useAuth.ts`

---

## Legacy Phase 기록 (보존용)

> 아래 내용은 2025-12-04 기준 Phase 1~3 진행 상황을 정리한 히스토리입니다. 최신 스프린트 정보는 위 "이번 스프린트 요약"을 참고하세요.

## 전체 진행 현황

| Phase | 기능 | Backend | Frontend | 상태 |
|-------|------|---------|----------|------|
| **Phase 1** | 재산분할 실시간 시각화 | ✅ 완료 | ✅ 완료 | **완료** |
| **Phase 2** | 타임라인 마인드맵 | ⏳ 대기 | ⏳ 대기 | 대기 |
| **Phase 3** | 인물관계 그래프 | ⏳ 대기 | ✅ 완료 | 진행중 |

---

## 커밋 이력 (L-integration)

### Phase 1: 재산분할 실시간 시각화

| 커밋 | 설명 | 날짜 |
|------|------|------|
| `827ad38` | Backend: DB 모델 (CaseProperty, DivisionPrediction) | 2025-12-04 |
| `5dd1a37` | Backend: 재산 CRUD API | 2025-12-04 |
| `fff0335` | Backend: 예측 API (AI Worker 연동) | 2025-12-04 |
| `a4264e6` | Frontend: UI 컴포넌트 전체 | 2025-12-04 |
| `00a62da` | Frontend: Dashboard 페이지 통합 | 2025-12-04 |
| `a700534` | Backend: import 경로 수정 | 2025-12-04 |

### Phase 3: 인물관계 그래프

| 커밋 | 설명 | 날짜 |
|------|------|------|
| `b26cae2` | Frontend: RelationshipFlow 컴포넌트 | 2025-12-04 |
| `b83804b` | Frontend: 관계도 링크 추가, auth 수정 | 2025-12-04 |

---

## Phase 1: 재산분할 실시간 시각화 (완료)

### Backend 파일

```
backend/app/
├── db/
│   ├── models.py          # + CaseProperty, DivisionPrediction
│   └── schemas.py         # + Property/Prediction 스키마
├── repositories/
│   ├── property_repository.py
│   └── prediction_repository.py
├── services/
│   ├── property_service.py
│   └── prediction_service.py
└── api/
    └── properties.py      # 8개 엔드포인트
```

### Frontend 파일

```
frontend/src/
├── types/property.ts
├── lib/api/properties.ts
└── components/property-division/
    ├── PropertyDivisionDashboard.tsx
    ├── DivisionGauge.tsx
    ├── PropertyInputForm.tsx
    └── index.ts
```

### API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/cases/{id}/properties` | 재산 추가 |
| `GET` | `/cases/{id}/properties` | 재산 목록 |
| `GET` | `/cases/{id}/properties/{prop_id}` | 단일 조회 |
| `PATCH` | `/cases/{id}/properties/{prop_id}` | 재산 수정 |
| `DELETE` | `/cases/{id}/properties/{prop_id}` | 재산 삭제 |
| `GET` | `/cases/{id}/properties/summary` | 요약 통계 |
| `GET` | `/cases/{id}/division-prediction` | 최신 예측 |
| `POST` | `/cases/{id}/division-prediction` | 새 예측 생성 |

---

## Phase 3: 인물관계 그래프 (진행중)

### Frontend 파일 (완료)

```
frontend/src/
├── types/relationship.ts
├── lib/api/relationship.ts
├── app/lawyer/cases/[id]/relationship/
│   ├── page.tsx
│   └── RelationshipClient.tsx
└── components/relationship/
    ├── RelationshipFlow.tsx       # 메인 그래프 (React Flow)
    ├── PersonNode.tsx             # 인물 노드
    ├── PersonDetailModal.tsx      # 인물 상세 모달
    ├── RelationshipEdge.tsx       # 관계 엣지
    ├── RelationshipDetailModal.tsx # 관계 상세 모달
    ├── RelationshipLegend.tsx     # 범례
    └── index.ts
```

### 추가 수정사항

- `CaseDetailClient.tsx`: 인물 관계도 링크 추가
- `LoginForm.tsx`: role 정규화, access_token 쿠키 설정
- `next.config.js`: 로컬 개발용 export 비활성화
- `package.json`: reactflow 의존성 추가

### Backend 작업 (대기)

| 항목 | 상태 |
|------|------|
| 인물 CRUD API (`/cases/{id}/persons`) | ⏳ 대기 |
| 관계 CRUD API (`/cases/{id}/relationships`) | ⏳ 대기 |
| 그래프 조회 API (`/cases/{id}/relationship-graph`) | ⏳ 대기 |

---

## Phase 2: 타임라인 마인드맵 (대기)

아직 착수하지 않음

---

## 기타 수정사항

| 커밋 | 설명 |
|------|------|
| `a23242b` | docs: Phase 1 구현 현황 문서 |

---

**Last Updated:** 2025-12-04 18:30
