# LEH 기능 테스트 가이드

**작성일:** 2025-12-05
**목적:** 구현된 기능들의 동작 검증

---

## 📋 테스트 대상 기능 목록

| # | 기능 | 위치 | 상태 |
|---|------|------|------|
| 1 | 인물 관계도 | Frontend + Demo API | 구현 완료 |
| 2 | 재산분할 대시보드 | Frontend + Backend API | 구현 완료 |
| 3 | 타임라인 뷰 | Frontend + Demo API | 구현 완료 |
| 4 | AI 분석 API | Backend Demo API | 구현 완료 |

---

## 🔧 테스트 환경 설정

### 1. 서버 실행

**Frontend (터미널 1)**
```bash
cd C:\fastmain\frontend
npm run dev
# → http://localhost:3000
```

**Backend (터미널 2)**
```bash
cd C:\fastmain\backend
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
```

### 2. API 문서 접속
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🧪 테스트 1: 인물 관계도 (Relationship Graph)

### 1.1 페이지 접속 테스트

**URL:** `http://localhost:3000/cases/1/relationship`

**확인 사항:**
- [ ] 페이지가 정상적으로 로드되는가?
- [ ] React Flow 캔버스가 표시되는가?
- [ ] 로딩 상태가 표시되는가?

### 1.2 Demo API 테스트

**API 엔드포인트:** `POST http://localhost:8000/l-demo/analyze/relationships`

**테스트 요청:**
```bash
curl -X POST "http://localhost:8000/l-demo/analyze/relationships" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "김철수와 이영희는 2020년에 결혼했습니다. 그러나 김철수는 박지영과 외도 관계를 맺었습니다. 김철수와 이영희 사이에는 아들 김민수가 있습니다."
  }'
```

**예상 응답:**
```json
{
  "status": "success",
  "result": {
    "nodes": [
      {"id": "person-0", "name": "김철수", "role": "unknown", "side": "unknown"},
      {"id": "person-1", "name": "이영희", "role": "unknown", "side": "unknown"},
      {"id": "person-2", "name": "박지영", "role": "third_party", "side": "unknown"},
      {"id": "person-3", "name": "김민수", "role": "child", "side": "unknown"}
    ],
    "edges": [
      {"source": "person-0", "target": "person-1", "relationship": "spouse", "label": "배우자"},
      {"source": "person-0", "target": "person-2", "relationship": "affair", "label": "외도"},
      {"source": "person-0", "target": "person-3", "relationship": "parent", "label": "부모-자녀"}
    ]
  }
}
```

**확인 사항:**
- [ ] API가 200 응답을 반환하는가?
- [ ] nodes 배열에 인물들이 추출되었는가?
- [ ] edges 배열에 관계가 추론되었는가?
- [ ] 외도 관계가 정확히 추론되었는가?

### 1.3 인물 추출 API 테스트

**API 엔드포인트:** `POST http://localhost:8000/l-demo/analyze/persons`

**테스트 요청:**
```bash
curl -X POST "http://localhost:8000/l-demo/analyze/persons" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "원고 김철수는 피고 이영희에게 위자료를 청구합니다. 제3자 박지영과의 불륜이 발각되었습니다."
  }'
```

**확인 사항:**
- [ ] 원고(김철수)가 plaintiff로 분류되는가?
- [ ] 피고(이영희)가 defendant로 분류되는가?
- [ ] 제3자(박지영)가 third_party로 분류되는가?

---

## 🧪 테스트 2: 재산분할 대시보드 (Property Division)

### 2.1 컴포넌트 확인

**파일 위치:** `frontend/src/components/property-division/`

**컴포넌트 목록:**
- `PropertyDivisionDashboard.tsx` - 메인 대시보드
- `DivisionGauge.tsx` - 분할 비율 게이지
- `EvidenceImpactList.tsx` - 증거 영향도 목록

### 2.2 영향도 분석 API 테스트

**API 엔드포인트:** `POST http://localhost:8000/l-demo/analyze/impact`

**테스트 요청:**
```bash
curl -X POST "http://localhost:8000/l-demo/analyze/impact" \
  -H "Content-Type: application/json" \
  -d '{
    "evidences": [
      {"evidence_id": "ev1", "evidence_type": "chat_log", "fault_types": ["adultery"]},
      {"evidence_id": "ev2", "evidence_type": "photo", "fault_types": ["violence"]},
      {"evidence_id": "ev3", "evidence_type": "recording", "fault_types": ["verbal_abuse"]}
    ],
    "case_id": "test-001"
  }'
```

**예상 응답:**
```json
{
  "status": "success",
  "case_id": "test-001",
  "result": {
    "plaintiff_ratio": 60,
    "defendant_ratio": 40,
    "confidence_level": "medium",
    "evidence_impacts": [
      {
        "evidence_id": "ev1",
        "evidence_type": "chat_log",
        "impact_type": "adultery",
        "impact_percent": 6.0,
        "direction": "plaintiff_favor",
        "reason": "외도 증거로 유책배우자 판정 가능성"
      }
    ],
    "similar_cases": []
  }
}
```

**확인 사항:**
- [ ] plaintiff_ratio + defendant_ratio = 100인가?
- [ ] 외도(adultery) 증거가 원고에게 유리하게 반영되는가?
- [ ] 폭행(violence) 증거가 영향도에 포함되는가?
- [ ] confidence_level이 반환되는가?

### 2.3 Properties Backend API 테스트

**API 엔드포인트:** `POST http://localhost:8000/cases/{case_id}/properties`

**테스트 요청 (재산 추가):**
```bash
curl -X POST "http://localhost:8000/cases/test-case-001/properties" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "강남 아파트",
    "property_type": "real_estate",
    "estimated_value": 800000000,
    "owner": "joint",
    "is_premarital": false
  }'
```

**테스트 요청 (재산 목록 조회):**
```bash
curl -X GET "http://localhost:8000/cases/test-case-001/properties"
```

**확인 사항:**
- [ ] 재산 항목이 정상적으로 생성되는가?
- [ ] 재산 목록 조회가 작동하는가?
- [ ] property_type enum이 올바르게 적용되는가?

---

## 🧪 테스트 3: 타임라인 뷰 (Timeline View)

### 3.1 컴포넌트 확인

**파일 위치:** `frontend/src/components/timeline/`

**컴포넌트 목록:**
- `TimelineView.tsx` - 메인 타임라인 뷰
- `TimelineEventCard.tsx` - 이벤트 카드

### 3.2 날짜 추출 API 테스트

**API 엔드포인트:** `POST http://localhost:8000/l-demo/analyze/dates`

**테스트 요청:**
```bash
curl -X POST "http://localhost:8000/l-demo/analyze/dates" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "2024년 3월 15일에 폭행 사건이 발생했습니다. 그 후 4월 20일에 외도가 발각되었고, 5월 1일에 별거를 시작했습니다."
  }'
```

**예상 응답:**
```json
{
  "status": "success",
  "result": {
    "dates": [
      {"original": "2024년 3월 15일", "datetime": "2024-03-15T00:00:00", "confidence": 0.95},
      {"original": "4월 20일", "datetime": "2024-04-20T00:00:00", "confidence": 0.85},
      {"original": "5월 1일", "datetime": "2024-05-01T00:00:00", "confidence": 0.85}
    ]
  }
}
```

**확인 사항:**
- [ ] 다양한 날짜 포맷이 추출되는가?
- [ ] datetime이 ISO 포맷으로 변환되는가?
- [ ] confidence 값이 반환되는가?

### 3.3 이벤트 요약 API 테스트

**API 엔드포인트:** `POST http://localhost:8000/l-demo/analyze/summarize`

**테스트 요청:**
```bash
curl -X POST "http://localhost:8000/l-demo/analyze/summarize?fault_types=violence,verbal_abuse" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "피고는 원고에게 '넌 아무것도 아니야'라고 말하며 뺨을 때렸습니다. 이로 인해 원고는 정신적 충격을 받았습니다."
  }'
```

**확인 사항:**
- [ ] 요약이 생성되는가?
- [ ] 키워드가 추출되는가?
- [ ] fault_label이 분류되는가?

---

## 🧪 테스트 4: AI Worker 모듈 직접 테스트

### 4.1 Health Check

**API 엔드포인트:** `GET http://localhost:8000/l-demo/health`

```bash
curl http://localhost:8000/l-demo/health
```

**예상 응답:**
```json
{
  "status": "ok",
  "module": "L-work Demo",
  "modules": {
    "person_extractor": "ok",
    "relationship_inferrer": "ok",
    "impact_analyzer": "ok"
  }
}
```

**확인 사항:**
- [ ] 모든 모듈 상태가 "ok"인가?
- [ ] AI Worker 경로가 올바르게 설정되었는가?

---

## 🧪 테스트 5: Frontend 통합 테스트

### 5.1 E2E 테스트 실행

```bash
cd C:\fastmain\frontend
npx playwright test e2e/production.spec.ts --headed
```

**확인 사항:**
- [ ] 홈페이지 접속 성공
- [ ] 로그인 페이지 로드
- [ ] 회원가입 페이지 로드
- [ ] 관계도 페이지 접속 가능
- [ ] 모바일 뷰 정상 렌더링
- [ ] 다크모드 정상 렌더링

### 5.2 수동 UI 테스트

| 페이지 | URL | 확인 사항 |
|--------|-----|-----------|
| 홈 | `/` | 랜딩 페이지 표시 |
| 로그인 | `/login` | 이메일/비밀번호 폼 |
| 회원가입 | `/signup` | 가입 폼 표시 |
| 관계도 | `/cases/1/relationship` | React Flow 캔버스 |

---

## 📊 테스트 결과 체크리스트

### API 테스트 결과

| API | 엔드포인트 | 상태 |
|-----|-----------|------|
| Health Check | `GET /l-demo/health` | ⬜ |
| 인물 추출 | `POST /l-demo/analyze/persons` | ⬜ |
| 관계 추론 | `POST /l-demo/analyze/relationships` | ⬜ |
| 영향도 분석 | `POST /l-demo/analyze/impact` | ⬜ |
| 날짜 추출 | `POST /l-demo/analyze/dates` | ⬜ |
| 이벤트 요약 | `POST /l-demo/analyze/summarize` | ⬜ |
| 재산 CRUD | `POST/GET /cases/{id}/properties` | ⬜ |

### Frontend 테스트 결과

| 페이지 | URL | 상태 |
|--------|-----|------|
| 홈페이지 | `/` | ⬜ |
| 로그인 | `/login` | ⬜ |
| 회원가입 | `/signup` | ⬜ |
| 관계도 | `/cases/1/relationship` | ⬜ |

### E2E 테스트 결과

| 테스트 | 상태 |
|--------|------|
| 메인 페이지 접속 | ⬜ |
| 로그인 페이지 접속 | ⬜ |
| 회원가입 페이지 접속 | ⬜ |
| 관계도 페이지 접속 | ⬜ |
| 404 페이지 처리 | ⬜ |
| 페이지 로드 성능 | ⬜ |
| 모바일 뷰 테스트 | ⬜ |
| 다크모드 테스트 | ⬜ |

---

## 🔍 문제 발생 시 디버깅

### Backend 로그 확인
```bash
# uvicorn 실행 시 --reload 옵션으로 로그 확인
cd C:\fastmain\backend
uvicorn app.main:app --reload --port 8000
```

### Frontend 로그 확인
```bash
# 브라우저 개발자 도구 Console 탭 확인
# Network 탭에서 API 요청/응답 확인
```

### AI Worker 모듈 직접 테스트
```bash
cd C:\fastmain\ai_worker
python -c "from src.analysis.person_extractor import PersonExtractor; print('OK')"
python -c "from src.analysis.relationship_inferrer import RelationshipInferrer; print('OK')"
python -c "from src.analysis.impact_analyzer import ImpactAnalyzer; print('OK')"
```

---

## 📝 테스트 완료 보고서

```
테스트 일시: YYYY-MM-DD HH:MM
테스터:
환경: Windows / localhost

[API 테스트]
- Health Check: PASS/FAIL
- 인물 추출: PASS/FAIL
- 관계 추론: PASS/FAIL
- 영향도 분석: PASS/FAIL
- 날짜 추출: PASS/FAIL

[Frontend 테스트]
- 페이지 접속: PASS/FAIL
- E2E 테스트: X/8 통과

[발견된 이슈]
1.
2.

[비고]
```
