# LSSP v2.01-v2.15 Integration Plan for LEH

**생성일**: 2025-12-18  
**대상**: 3인 개발팀  
**목표**: 기존 LEH 프로젝트에 LSSP 이혼 모듈 통합

---

## 1. 현재 상태 Gap 분석

### 1.1 Backend Models 비교

| LSSP 개념 | 현재 LEH 상태 | Gap |
|-----------|--------------|-----|
| `draft_templates` (seed) | `document_templates` 존재 | 스키마 차이, 병합 필요 |
| `draft_blocks` (seed) | ❌ 없음 | 신규 추가 |
| `drafts` | `draft_documents` 존재 | 컬럼 추가 (coverage_score, template_id) |
| `draft_block_instances` | ❌ 없음 (monolithic JSON) | 신규 추가, 마이그레이션 |
| `draft_citations` | ❌ 없음 | 신규 추가 |
| `evidence_extracts` | ❌ 없음 | 신규 추가 |
| `keypoints` | ❌ 없음 | 신규 추가 (핵심 기능) |
| `keypoint_*_links` | ❌ 없음 | 신규 추가 |
| `timeline_events` | `procedure_stage_records` (부분적) | 확장/신규 |
| `legal_grounds` (seed) | ❌ 없음 | 신규 추가 |
| `precedents` (seed) | ❌ 없음 | 신규 추가 |
| `process_states` | `procedure_stage_records` (부분적) | 확장 |

### 1.2 서비스 레이어 비교

| LSSP 서비스 | 현재 LEH |
|------------|---------|
| Draft Engine (v2.04/06) | `services/draft/` 존재 (RAG 기반) |
| Keypoint Extractor (v2.10) | `ai_worker/article_840_tagger` (부분적) |
| Recommender (v2.12) | `rag_orchestrator.py` (유사) |
| Process Engine (v2.14) | `procedure_service.py` (단순) |
| Recompute Orchestrator (v2.15) | ❌ 없음 |

---

## 2. 구현 Phase 계획

### Phase 1: 기초 인프라 (Week 1-2)
**목표**: 시드 데이터 + 핵심 스키마

```
작업 목록:
1. Alembic 마이그레이션 생성
   - legal_grounds (v2.01)
   - keypoint_types (v2.03)
   - draft_templates, draft_blocks (v2.04)
   
2. 시드 데이터 임포트 스크립트
   - seeds/legal_grounds.v2_01.json
   - seeds/evidence_checklist.v2_01.json
   - data/keypoint_types.v2_03.json
   - data/draft_templates.v2_04.json
   - data/draft_blocks.v2_04.json

3. Backend 모델 추가
   - app/db/models/lssp/ 네임스페이스 생성
   - legal_ground.py, keypoint.py, draft_block.py
```

### Phase 2: Keypoint 시스템 (Week 3-4)
**목표**: 증거→키포인트 추출 파이프라인

```
작업 목록:
1. DB 스키마
   - evidence_extracts 테이블
   - keypoints 테이블
   - keypoint_extract_links, keypoint_ground_links

2. API 엔드포인트
   - POST /api/cases/{id}/keypoints
   - GET /api/cases/{id}/keypoints
   - PATCH /api/keypoints/{id}
   - POST /api/keypoints/{id}/link-evidence

3. AI Worker 통합
   - keypoint_extractor 서비스 (v2.10 기반)
   - 기존 article_840_tagger 마이그레이션
```

### Phase 3: Draft Engine 업그레이드 (Week 5-6)
**목표**: 블록 기반 초안 생성

```
작업 목록:
1. DB 마이그레이션
   - draft_block_instances 테이블
   - draft_citations 테이블
   - draft_precedent_links 테이블

2. 기존 draft_documents 마이그레이션
   - JSON content → block_instances 분리
   - 역호환 레이어 유지

3. Draft Engine 서비스
   - services/draft/block_renderer.py (신규)
   - services/draft/citation_linker.py (신규)
   - coverage_score 계산 로직

4. Frontend 업데이트
   - DraftEditor 블록 단위 편집
   - Citation 패널 추가
```

### Phase 4: 법률/판례 라이브러리 (Week 7-8)
**목표**: 법률 근거 및 판례 추천

```
작업 목록:
1. DB 스키마 (v2.11, v2.12)
   - law_articles 테이블
   - precedents 테이블
   - ground_to_authorities_map

2. Recommender API
   - GET /api/cases/{id}/recommended-precedents
   - GET /api/legal-grounds/{code}/authorities

3. 시드 데이터
   - law_articles.v2_11.json
   - precedent_index.v2_12.json
   
4. 기존 RAG 오케스트레이터 통합
```

### Phase 5: Timeline & Process (Week 9-10)
**목표**: 통합 타임라인 + 상태 머신

```
작업 목록:
1. DB 확장 (v2.13, v2.14)
   - timeline_events 테이블
   - process_states 테이블
   - keypoint_timeline_links

2. API 엔드포인트
   - GET /api/cases/{id}/timeline (통합)
   - POST /api/cases/{id}/process/transition

3. 기존 procedure_stage_records 마이그레이션
   - timeline_events로 데이터 이전
   - 역호환 뷰 생성

4. Frontend Timeline 컴포넌트
```

### Phase 6: Recompute Pipeline (Week 11-12)
**목표**: 변경 시 자동 재계산

```
작업 목록:
1. DB 스키마 (v2.15)
   - recompute_jobs 테이블
   - recompute_dependencies

2. Orchestrator 서비스
   - services/recompute/orchestrator.py
   - Trigger 룰 구현 (v2.15 그래프 기반)

3. Job Queue 통합
   - 기존 job_service.py 확장
   - coverage_score, timeline, recommendations 재계산
```

---

## 3. 파일 구조 계획

```
backend/app/
├── db/models/
│   ├── lssp/                    # 신규 네임스페이스
│   │   ├── __init__.py
│   │   ├── legal_ground.py      # v2.01
│   │   ├── keypoint.py          # v2.03
│   │   ├── draft_block.py       # v2.04
│   │   ├── evidence_extract.py  # v2.03
│   │   ├── timeline_event.py    # v2.13
│   │   ├── precedent.py         # v2.12
│   │   └── recompute_job.py     # v2.15
│   └── (기존 모델 유지)
├── api/
│   ├── lssp/                    # 신규 라우터
│   │   ├── keypoints.py
│   │   ├── draft_blocks.py
│   │   ├── legal_grounds.py
│   │   ├── precedents.py
│   │   └── timeline.py
│   └── (기존 라우터 유지)
├── services/
│   ├── lssp/                    # 신규 서비스
│   │   ├── keypoint_extractor.py
│   │   ├── draft_block_renderer.py
│   │   ├── recommender.py
│   │   ├── process_engine.py
│   │   └── recompute_orchestrator.py
│   └── (기존 서비스 유지)
└── seeds/                       # 신규
    ├── legal_grounds.json
    ├── keypoint_types.json
    ├── draft_templates.json
    └── draft_blocks.json
```

---

## 4. 마이그레이션 전략

### 4.1 무중단 배포 원칙
- 모든 DDL은 **append-only** (기존 컬럼 삭제 금지)
- 새 테이블 먼저 생성 → 데이터 마이그레이션 → 코드 전환 → 구 코드 제거

### 4.2 기존 데이터 처리

**draft_documents → drafts + draft_block_instances**:
```sql
-- Step 1: 새 테이블에 복사
INSERT INTO drafts (id, case_id, template_id, title, ...)
SELECT id, case_id, 'LEGACY', title, ...
FROM draft_documents;

-- Step 2: content JSON → block_instances 분해
-- (Python 마이그레이션 스크립트로 처리)

-- Step 3: 기존 테이블 deprecated 마킹
ALTER TABLE draft_documents ADD COLUMN deprecated BOOLEAN DEFAULT false;
```

**procedure_stage_records → timeline_events**:
```sql
INSERT INTO timeline_events (case_id, event_date, event_type, title, source)
SELECT case_id, scheduled_date, 'process', stage, 'MIGRATION'
FROM procedure_stage_records
WHERE scheduled_date IS NOT NULL;
```

---

## 5. 테스트 전략

### 5.1 단위 테스트 커버리지
- 각 Phase별 80% 이상 목표
- keypoint 계산 로직 100%
- coverage_score 계산 100%

### 5.2 통합 테스트
- API 엔드포인트별 happy path + edge case
- 마이그레이션 스크립트 롤백 테스트

### 5.3 E2E 테스트
- "증거 업로드 → 키포인트 추출 → 초안 생성" 플로우
- "키포인트 수정 → 초안 자동 업데이트" 플로우

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|-----|------|
| 기존 draft 데이터 손실 | 높음 | 마이그레이션 전 백업, 롤백 스크립트 |
| AI Worker 성능 저하 | 중간 | 배치 처리, 큐 분리 |
| Frontend 호환성 깨짐 | 중간 | API 버저닝 (/api/v2/), 점진적 전환 |
| 시드 데이터 불일치 | 낮음 | 버전 태그, checksum 검증 |

---

## 7. 즉시 실행 항목 (Week 1)

### Day 1-2: 환경 준비
```bash
# 1. LSSP 브랜치 생성
cd /Users/admin/Documents/dev/leh
git checkout -b feature/lssp-integration

# 2. 모델 디렉토리 생성
mkdir -p backend/app/db/models/lssp
mkdir -p backend/app/api/lssp
mkdir -p backend/app/services/lssp
mkdir -p backend/app/seeds

# 3. 첫 Alembic 마이그레이션 (legal_grounds)
cd backend
alembic revision --autogenerate -m "Add LSSP legal_grounds table"
```

### Day 3-4: v2.01 시드 구현
1. `legal_ground.py` 모델 작성
2. `seeds/legal_grounds.json` 복사
3. 시드 임포트 스크립트 작성
4. 테스트

### Day 5: v2.03 Keypoint 모델 시작
1. `keypoint.py` 모델 작성
2. `evidence_extract.py` 모델 작성
3. 마이그레이션 생성

---

## 8. 참조 문서

- LSSP Pack Index: `./LSSP_V2_01_15_PACK_INDEX.md`
- Checksum: `./LSSP_V2_01_15_MANIFEST.sha256.json`
- v2.04 DDL: `./lssp_divorce_module_pack_v2_04/docs/DB_DDL_DRAFTS_v2_04.sql`
- v2.03 Keypoint Schema: `./lssp_divorce_module_pack_v2_03/docs/DB_SCHEMA_APPENDIX_v2_03.md`
