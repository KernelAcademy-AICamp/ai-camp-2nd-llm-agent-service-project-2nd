# AI Worker 작업 리포트

## 최신 상태 (2025-12-01)

### E2E 통합 구현 완료

#### 구현된 기능

1. **S3 Key에서 evidence_id 추출** (`handler.py`)
   - Backend 형식 지원: `cases/{case_id}/raw/{evidence_id}_{filename}`
   - `_extract_evidence_id_from_s3_key()` 함수 추가
   - `_extract_case_id()` 함수 Backend 형식 지원 추가

2. **Backend 레코드 UPDATE 로직** (`metadata_store.py`)
   - `update_evidence_status()` 메서드 추가
   - 필드: `status`, `processed_at`, `ai_summary`, `article_840_tags`, `qdrant_id`

3. **route_and_process() 수정** (`handler.py`)
   - Backend evidence_id 추출 시: UPDATE 로직 실행
   - evidence_id 없을 시: fallback으로 새 레코드 생성

#### 테스트 결과

| 테스트 클래스 | 테스트 수 | 통과 |
|--------------|----------|------|
| TestE2EIntegration | 7 | 7 ✅ |

```
tests/test_handler.py::TestE2EIntegration::test_extract_case_id_from_backend_format PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_case_id_from_legacy_format PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_case_id_fallback PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_evidence_id_from_backend_format PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_evidence_id_with_underscore_in_filename PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_evidence_id_returns_none_for_legacy_format PASSED
tests/test_handler.py::TestE2EIntegration::test_extract_evidence_id_returns_none_for_non_ev_prefix PASSED
```

---

## 변경된 파일

| 파일 | 변경 내용 |
|------|----------|
| `ai_worker/handler.py` | evidence_id 추출 함수 및 UPDATE 로직 추가 |
| `ai_worker/src/storage/metadata_store.py` | `update_evidence_status()` 메서드 추가 |
| `ai_worker/tests/test_handler.py` | E2E 통합 테스트 7개 추가 |
| `docs/guides/plan.md` | 2.8 E2E 통합 섹션 추가 |
| `docs/guides/E2E_INTEGRATION_PLAN.md` | 상세 통합 계획 문서 |

---

## 데이터 흐름 (수정 후)

```
Frontend → Backend: presigned URL 요청
         ↓
Backend: evidence 레코드 생성 (status=pending, evidence_id=ev_xxx)
         ↓
Frontend → S3: 파일 업로드 (cases/{case_id}/raw/{ev_xxx}_{filename})
         ↓
S3 Event → Lambda (AI Worker)
         ↓
AI Worker:
  1. S3 key에서 evidence_id 추출 (ev_xxx)
  2. 파일 파싱 및 분석
  3. DynamoDB UPDATE (status=processed, ai_summary, tags)
  4. Qdrant에 벡터 저장
         ↓
Backend: GET /evidence/{id} → status=processed 확인
```

---

## AWS 연결 테스트 결과 (2025-12-01)

### IAM 권한 (`leh-dev-l` 사용자)

| 서비스 | 작업 | 상태 |
|--------|------|------|
| S3 | `leh-evidence-prod` 접근 | ✅ |
| DynamoDB | `leh_evidence` PutItem | ✅ |
| DynamoDB | `leh_evidence` GetItem | ✅ |
| DynamoDB | `leh_evidence` UpdateItem | ✅ |
| DynamoDB | `leh_case_summary` 접근 | ✅ |
| Lambda | 배포/호출 | ✅ (완료) |

### 환경변수 설정

- `S3_EVIDENCE_BUCKET=leh-evidence-prod`
- `DYNAMODB_TABLE=leh_evidence`
- `DYNAMODB_TABLE_CASE_SUMMARY=leh_case_summary`

---

## 다음 작업

- [x] S3 버킷 권한 확인 ✅
- [x] DynamoDB 연결 테스트 ✅
- [x] Lambda 배포 완료 ✅ (2025-12-01)
- [x] Full E2E 테스트 (실제 파일 업로드 → Lambda → Backend) ✅

---

## 배포 완료 현황 (2025-12-01)

### Backend (Lambda + API Gateway)
| 항목 | 값 |
|------|-----|
| Lambda 함수 | `leh-backend` |
| API Endpoint | `https://zhfiuntwj0.execute-api.ap-northeast-2.amazonaws.com` |
| Architecture | arm64, 512MB, 30s timeout |
| IAM Role | `leh-backend-role` |

### AI Worker (Lambda)
| 항목 | 값 |
|------|-----|
| Lambda 함수 | `leh-ai-worker` |
| ECR 이미지 | `540261961975.dkr.ecr.ap-northeast-2.amazonaws.com/leh-ai-worker` |
| Architecture | arm64, 1024MB, 300s timeout |
| S3 트리거 | `leh-evidence-prod/cases/*` |

### Frontend (S3 + CloudFront)
| 항목 | 값 |
|------|-----|
| S3 버킷 | `leh-frontend-kbp9r` |
| CloudFront URL | `https://dpbf86zqulqfy.cloudfront.net` |
| API 연동 | `NEXT_PUBLIC_API_BASE_URL` 설정됨 |

### GitHub Actions 설정
- ✅ 11개 Secrets 설정 (AWS, DB, JWT, OpenAI, Qdrant 등)
- ✅ 27개 Variables 설정 (비민감 환경변수)
- ✅ 배포 워크플로우 Access Key 인증으로 구성

---

*작성일: 2025-12-01*
*최종 업데이트: 2025-12-01*
*작성자: AI Worker 담당 (L), 배포 담당 (H)*
