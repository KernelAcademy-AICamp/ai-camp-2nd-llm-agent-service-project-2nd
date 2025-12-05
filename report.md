## [L-work-v2] 작업 보고
- **시간**: 2025-12-05
- **브랜치**: `L-work-v2` (upstream/dev 기반)
- **상태**: ✅ Track A + Track B 완료
- **작업 내용**: 인물 관계도 + 재산분할 UI 구현 (TDD 방식)

---

### 🆕 최신 상태 (2025-12-05)

#### Track A: 인물 관계도 (React Flow)

| 단계 | 파일 | 상태 | 커밋 메시지 |
|------|------|------|------------|
| A-1.1 | React Flow 설치 | ✅ 완료 (이미 설치됨 v11.11.4) | - |
| A-1.2 | `types/relationship.ts` | ✅ 완료 (16 tests) | `feat(behavior): add relationship type definitions with tests` |
| A-1.3 | `lib/api/relationship.ts` | ✅ 완료 (7 tests) | `feat(behavior): add relationship API client with tests` |
| A-2.1 | `app/cases/[id]/relationship/page.tsx` | ✅ 완료 | `feat(behavior): add relationship page route` |
| A-2.2 | `RelationshipClient.tsx` | ✅ 완료 | `feat(behavior): add RelationshipClient component` |
| A-2.3 | `RelationshipFlow.tsx` | ✅ 완료 | `feat(behavior): add RelationshipFlow component` |
| A-3.1 | `PersonNode.tsx` | ✅ 완료 | `feat(behavior): add PersonNode custom component` |
| A-3.2 | `RelationshipEdge.tsx` | ✅ 완료 | `feat(behavior): add RelationshipEdge custom component` |
| A-4 | `RelationshipLegend.tsx` | ✅ 완료 | `feat(behavior): add RelationshipLegend component` |
| A-5 | `index.ts` (배럴) | ✅ 완료 | `chore(structure): add relationship component barrel exports` |

#### Track B: 재산분할 대시보드

| 단계 | 파일 | 상태 | 커밋 메시지 |
|------|------|------|------------|
| B-1.1 | `types/property.ts` | ✅ 완료 (18 tests) | `feat(behavior): add property type definitions with tests` |
| B-1.2 | `lib/api/properties.ts` | ✅ 완료 (6 tests) | `feat(behavior): add properties API client with tests` |
| B-2.1 | `DivisionGauge.tsx` | ✅ 완료 | `feat(behavior): add DivisionGauge component` |
| B-2.2 | `EvidenceImpactList.tsx` | ✅ 완료 | `feat(behavior): add EvidenceImpactList component` |
| B-2.3 | `PropertyDivisionDashboard.tsx` | ✅ 완료 | `feat(behavior): add PropertyDivisionDashboard component` |
| B-3 | `index.ts` (배럴) | ✅ 완료 | `chore(structure): add property-division component barrel exports` |

#### 생성된 파일 목록

```
frontend/src/
├── types/
│   ├── relationship.ts              # ✅ Track A
│   ├── property.ts                  # ✅ Track B
│   └── __tests__/
│       ├── relationship.test.ts     # ✅ Track A (16 tests)
│       └── property.test.ts         # ✅ Track B (18 tests)
├── lib/api/
│   ├── relationship.ts              # ✅ Track A
│   ├── properties.ts                # ✅ Track B
│   └── __tests__/
│       ├── relationship.test.ts     # ✅ Track A (7 tests)
│       └── properties.test.ts       # ✅ Track B (6 tests)
├── app/cases/[id]/relationship/
│   ├── page.tsx                     # ✅ Track A
│   └── RelationshipClient.tsx       # ✅ Track A
├── components/relationship/
│   ├── index.ts                     # ✅ Track A
│   ├── RelationshipFlow.tsx         # ✅ Track A
│   ├── PersonNode.tsx               # ✅ Track A
│   ├── RelationshipEdge.tsx         # ✅ Track A
│   └── RelationshipLegend.tsx       # ✅ Track A
└── components/property-division/
    ├── index.ts                     # ✅ Track B
    ├── PropertyDivisionDashboard.tsx # ✅ Track B
    ├── DivisionGauge.tsx            # ✅ Track B
    └── EvidenceImpactList.tsx       # ✅ Track B
```

---

### 📝 커밋 대기열

커밋이 필요한 작업 완료 시 아래에 기록합니다:

1. **✅ 커밋 준비 완료**: A-1.2 타입 정의
   - 파일: `frontend/src/types/relationship.ts`, `frontend/src/types/__tests__/relationship.test.ts`
   - 커밋 메시지: `feat(behavior): add relationship type definitions with tests`
   - 테스트: 16개 통과

2. **✅ 커밋 준비 완료**: A-1.3 API 클라이언트
   - 파일: `frontend/src/lib/api/relationship.ts`, `frontend/src/lib/api/__tests__/relationship.test.ts`
   - 커밋 메시지: `feat(behavior): add relationship API client with tests`
   - 테스트: 7개 통과

3. **✅ 커밋 준비 완료**: Track A + Track B 전체 (권장: 단일 커밋)
   - **Track A 파일 (11개)**:
     - `frontend/src/types/relationship.ts`
     - `frontend/src/types/__tests__/relationship.test.ts`
     - `frontend/src/lib/api/relationship.ts`
     - `frontend/src/lib/api/__tests__/relationship.test.ts`
     - `frontend/src/app/cases/[id]/relationship/page.tsx`
     - `frontend/src/app/cases/[id]/relationship/RelationshipClient.tsx`
     - `frontend/src/components/relationship/index.ts`
     - `frontend/src/components/relationship/RelationshipFlow.tsx`
     - `frontend/src/components/relationship/PersonNode.tsx`
     - `frontend/src/components/relationship/RelationshipEdge.tsx`
     - `frontend/src/components/relationship/RelationshipLegend.tsx`
   - **Track B 파일 (8개)**:
     - `frontend/src/types/property.ts`
     - `frontend/src/types/__tests__/property.test.ts`
     - `frontend/src/lib/api/properties.ts`
     - `frontend/src/lib/api/__tests__/properties.test.ts`
     - `frontend/src/components/property-division/index.ts`
     - `frontend/src/components/property-division/PropertyDivisionDashboard.tsx`
     - `frontend/src/components/property-division/DivisionGauge.tsx`
     - `frontend/src/components/property-division/EvidenceImpactList.tsx`
   - 커밋 메시지:
     ```
     feat(frontend): implement relationship graph and property division UI

     Track A: Relationship Graph (React Flow)
     - Add relationship type definitions with tests (16 tests)
     - Add relationship API client with tests (7 tests)
     - Add /cases/[id]/relationship route with RelationshipClient
     - Add RelationshipFlow, PersonNode, RelationshipEdge components
     - Add RelationshipLegend with color mappings

     Track B: Property Division Dashboard
     - Add property type definitions with tests (18 tests)
     - Add properties API client with tests (6 tests)
     - Add PropertyDivisionDashboard with DivisionGauge
     - Add EvidenceImpactList component

     Total: 47 tests passing
     ```
   - 테스트: 47개 통과 (Track A: 23개, Track B: 24개)

---

### 이전 작업 (2025-11-28)

## [dev] 작업 보고
- **시간**: 2025-11-28 16:00
- **상태**: ⚠️ S3 버킷 생성 대기
- **작업 내용**: AI Worker Storage 모듈 교체 완료 + Lambda 배포 준비 완료

---

### 🆕 최신 상태 (2025-11-28 16:00)

#### S3 연동 현황
- ✅ S3 다운로드 로직 구현 완료 (`handler.py`)
- ✅ 환경변수 설정 완료 (`S3_BUCKET_NAME=leh-evidence-dev`)
- ❌ **S3 버킷 `leh-evidence-dev` 존재하지 않음**
  - Admin 권한으로 버킷 생성 필요

#### Lambda 배포 준비
- ✅ `Dockerfile.lambda` 작성 완료
- ✅ 모든 모듈 import 테스트 통과
- ⏳ ECR 푸시 및 Lambda 배포 대기 (S3 버킷 생성 후)

---

### 이전 작업 요약 (Storage 마이그레이션)

---

### 1. 완료된 작업

#### 1.1 Storage 모듈 전면 교체

| 기존 (로컬) | 변경 후 (AWS) | 상태 |
|------------|--------------|------|
| SQLite (`metadata.db`) | DynamoDB (`leh_evidence`) | ✅ 완료 |
| ChromaDB (로컬 디렉토리) | Qdrant Cloud | ✅ 완료 |

#### 1.2 수정된 파일

```
ai_worker/src/storage/metadata_store.py  # DynamoDB 기반으로 전면 재작성
ai_worker/src/storage/vector_store.py    # Qdrant 기반으로 전면 재작성
ai_worker/src/utils/embeddings.py        # OpenAI Embedding 유틸리티 (신규)
ai_worker/handler.py                     # 새 Storage 인터페이스 사용
ai_worker/.env                           # DYNAMODB_TABLE 수정 (leh_evidence)
ai_worker/tests/src/test_metadata_store.py  # Mock 기반 유닛 테스트
ai_worker/tests/src/test_vector_store.py    # Mock 기반 유닛 테스트
```

#### 1.3 테스트 결과

```
===== 34 passed =====
- MetadataStore (DynamoDB): 18개 테스트 ✅
- VectorStore (Qdrant): 15개 유닛 테스트 + 1개 통합 테스트 ✅
```

---

### 2. 기술적 세부사항

#### 2.1 DynamoDB 스키마

| 필드 | 설명 |
|------|------|
| `evidence_id` (PK) | 파일: `file_xxx`, 청크: `chunk_xxx` |
| `case_id` (GSI) | 케이스별 조회용 GSI |
| `record_type` | `file` 또는 `chunk` |

#### 2.2 Qdrant 설정

- **URL**: `https://bd8187e3-671e-4da4-b4fd-f8f92637c196.us-west-1-0.aws.cloud.qdrant.io`
- **Collection**: `leh_evidence`
- **Vector Size**: 1536 (OpenAI text-embedding-ada-002)
- **Payload Indexes**: `case_id`, `file_id`, `chunk_id`, `sender`

#### 2.3 권한 이슈 해결

| 작업 | 상태 | 해결 방법 |
|------|------|----------|
| PutItem | ✅ | - |
| GetItem | ✅ | - |
| DeleteItem | ✅ | - |
| Query (GSI) | ✅ | - |
| Scan | ✅ | - |
| BatchWriteItem | ❌ 권한 없음 | 개별 PutItem으로 fallback |
| DescribeTable | ❌ 권한 없음 | 불필요 (테이블 이미 존재) |

---

### 3. 통합 테스트 결과

#### 3.1 Qdrant 통합 테스트
```
✅ 벡터 추가 성공
✅ 유사도 검색 성공
✅ case_id 필터링 성공
✅ 벡터 삭제 성공
```

#### 3.2 DynamoDB 통합 테스트
```
✅ 파일 메타데이터 저장/조회/삭제
✅ 청크 저장/조회/삭제
✅ 케이스별 조회 (GSI Query)
✅ save_chunks (개별 PutItem)
```

---

### 4. 다음 단계

1. **E2E 테스트**: 실제 파일 업로드 → 파싱 → 벡터화 → 저장 전체 플로우
2. **Lambda 배포**: 새 Storage 모듈로 Lambda 함수 업데이트
3. **Backend 연동**: AI Worker와 Backend 간 데이터 동기화 확인

---

### 5. 커밋 메시지 제안

```
feat(ai_worker): replace storage modules with AWS services (DynamoDB, Qdrant)

- Replace SQLite with DynamoDB for metadata storage
- Replace ChromaDB with Qdrant Cloud for vector storage
- Add OpenAI embeddings utility (src/utils/embeddings.py)
- Add payload indexes for Qdrant filtering
- Fix BatchWriteItem limitation with individual PutItem fallback
- Update handler.py to use new storage interfaces
- Rewrite unit tests with mocks (34 tests passing)

BREAKING CHANGE: Local storage no longer supported, requires AWS credentials
```

---

**작업 완료**: AI Worker가 이제 Backend와 동일한 AWS 서비스를 사용
