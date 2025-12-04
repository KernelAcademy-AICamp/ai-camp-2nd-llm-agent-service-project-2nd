# LEH 서비스 구현 현황

**최종 업데이트:** 2025-12-04
**브랜치:** L-integration
**관련 문서:** `IDEAS_IMPLEMENTATION_PLAN.md`

---

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
