# E2E Integration Plan: Backend - AI Worker

## 1. 현재 상황 분석

### 1.1 완료된 작업
| 항목 | 상태 | 설명 |
|------|------|------|
| AI Worker DynamoDB 통합 | ✅ | PR #26 머지됨 |
| AI Worker Qdrant 통합 | ✅ | PR #26 머지됨 |
| Backend Evidence API | ✅ | 업로드, 조회 구현 |
| Terraform S3 Event Trigger | ✅ | S3 → Lambda 설정 완료 |
| Lambda Dockerfile | ✅ | 배포 준비 완료 |

### 1.2 미완료 작업 (핵심 Gap)

#### Gap 1: 스키마 불일치
**Backend가 생성하는 Evidence 레코드:**
```python
{
    "id": "ev_abc123",           # evidence_id
    "case_id": "case_001",
    "type": "image",            # evidence type
    "filename": "photo.jpg",
    "s3_key": "cases/case_001/raw/ev_abc123_photo.jpg",
    "status": "pending",        # 대기 중
    "created_by": "user_001"
}
```

**AI Worker가 생성하는 레코드:**
```python
{
    "evidence_id": "file_xyz789",  # 다른 ID!
    "file_id": "file_xyz789",
    "file_type": "image",
    "status": "done",
    "record_type": "file"
}
```

**문제:** Backend와 AI Worker가 **다른 레코드**를 생성함

#### Gap 2: AI Worker 트리거 미구현
```python
# backend/app/services/evidence_service.py:195-197
# TODO: Trigger AI Worker via SNS or direct Lambda invocation
# This will be implemented when AWS Lambda is fully set up
# For now, evidence will stay in "pending" status until AI Worker picks it up
```

#### Gap 3: 상태 동기화 없음
- AI Worker가 처리 완료해도 Backend 레코드는 `status=pending` 유지
- Frontend에서 처리 완료 여부 확인 불가

---

## 2. 해결 방안

### 2.1 스키마 통일 전략

**선택: AI Worker가 Backend 레코드를 업데이트**

```
[현재 흐름]
Backend: 새 레코드 생성 (status=pending)
AI Worker: 새 레코드 생성 (별개의 evidence_id)
→ 두 개의 레코드 존재!

[수정 후 흐름]
Backend: 새 레코드 생성 (status=pending, evidence_id=ev_xxx)
S3 Event: Lambda 트리거 (s3_key에 evidence_id 포함)
AI Worker: s3_key에서 evidence_id 추출 → 해당 레코드 UPDATE
→ 하나의 레코드만 존재!
```

**구현 내용:**
1. AI Worker의 `handler.py`에서 s3_key 파싱하여 evidence_id 추출
2. `MetadataStore`에 `update_evidence_status()` 메서드 추가
3. 처리 완료 후 status를 "pending" → "processed"로 변경

### 2.2 트리거 방식 결정

**선택: S3 Event Trigger (이미 Terraform에 설정됨)**

```hcl
# infra/terraform/main.tf (라인 127-137)
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.evidence_bucket.id
  lambda_function {
    lambda_function_arn = aws_lambda_function.ai_worker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "cases/"
  }
}
```

**장점:**
- 이미 설정됨, 추가 구현 불필요
- 자동 트리거 (Backend 코드 수정 불필요)
- 비용 효율적 (서버리스)

**흐름:**
```
1. Frontend → Backend: presigned URL 요청
2. Backend: evidence 레코드 생성 (status=pending)
3. Frontend → S3: 파일 업로드
4. S3 Event → Lambda: AI Worker 자동 호출
5. AI Worker: 파일 처리 → evidence 레코드 UPDATE
6. Frontend: GET /evidence/{id} → status=processed 확인
```

---

## 3. 상세 구현 계획

### Phase 1: AI Worker 수정 (예상 2시간)

#### 3.1.1 evidence_id 추출 로직 추가
**파일:** `ai_worker/handler.py`

```python
def extract_evidence_id_from_s3_key(s3_key: str) -> Optional[str]:
    """
    S3 key에서 evidence_id 추출
    형식: cases/{case_id}/raw/{evidence_id}_{filename}
    예: cases/case_001/raw/ev_abc123_photo.jpg → ev_abc123
    """
    filename = s3_key.split("/")[-1]
    if filename.startswith("ev_") and "_" in filename[3:]:
        parts = filename.split("_", 2)
        return f"ev_{parts[1]}"
    return None
```

#### 3.1.2 MetadataStore에 update 메서드 추가
**파일:** `ai_worker/src/storage/metadata_store.py`

```python
def update_evidence_status(
    self,
    evidence_id: str,
    status: str = "processed",
    ai_summary: Optional[str] = None,
    article_840_tags: Optional[dict] = None,
    qdrant_id: Optional[str] = None
) -> None:
    """
    Backend가 생성한 evidence 레코드 상태 업데이트
    """
    update_expression = "SET #status = :status, processed_at = :processed_at"
    expression_values = {
        ":status": {"S": status},
        ":processed_at": {"S": datetime.now(timezone.utc).isoformat()}
    }

    if ai_summary:
        update_expression += ", ai_summary = :summary"
        expression_values[":summary"] = {"S": ai_summary}

    if article_840_tags:
        update_expression += ", article_840_tags = :tags"
        expression_values[":tags"] = {"M": self._serialize_item(article_840_tags)}

    if qdrant_id:
        update_expression += ", qdrant_id = :qdrant_id"
        expression_values[":qdrant_id"] = {"S": qdrant_id}

    self.client.update_item(
        TableName=self.table_name,
        Key={"evidence_id": {"S": evidence_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=expression_values
    )
```

#### 3.1.3 handler.py 수정
**파일:** `ai_worker/handler.py`

```python
def route_and_process(bucket_name: str, object_key: str) -> Dict[str, Any]:
    # 기존 로직...

    # evidence_id 추출 (Backend 레코드 업데이트용)
    evidence_id = extract_evidence_id_from_s3_key(object_key)

    # 파싱 및 분석 수행...

    # Backend 레코드 업데이트 (새 레코드 생성 대신)
    if evidence_id:
        metadata_store.update_evidence_status(
            evidence_id=evidence_id,
            status="processed",
            ai_summary=summary,
            article_840_tags=tags,
            qdrant_id=vector_id
        )
    else:
        # fallback: 새 레코드 생성 (기존 방식)
        metadata_store.save_file(evidence_file)
```

### Phase 2: 테스트 (예상 1시간)

#### 3.2.1 Unit Test 추가
**파일:** `ai_worker/tests/src/test_metadata_store.py`

```python
def test_update_evidence_status():
    """Backend 레코드 업데이트 테스트"""
    # Given: Backend가 생성한 레코드
    evidence_id = "ev_test123"

    # When: AI Worker가 상태 업데이트
    metadata_store.update_evidence_status(
        evidence_id=evidence_id,
        status="processed",
        ai_summary="테스트 요약"
    )

    # Then: 상태가 업데이트됨
    result = metadata_store.get_evidence(evidence_id)
    assert result["status"] == "processed"
    assert result["ai_summary"] == "테스트 요약"
```

#### 3.2.2 Integration Test
```python
def test_e2e_backend_ai_worker_integration():
    """Backend → S3 → AI Worker → Backend 조회 흐름"""
    # 1. Backend가 evidence 생성 시뮬레이션
    # 2. S3 이벤트 시뮬레이션
    # 3. AI Worker 처리
    # 4. Backend에서 조회 확인
```

### Phase 3: 환경변수 통일 (예상 30분)

**확인 필요 항목:**
| 환경변수 | Backend | AI Worker | 상태 |
|---------|---------|-----------|------|
| DDB_EVIDENCE_TABLE | leh_evidence | leh_evidence | ⚠️ Admin 확인 필요 |
| S3_EVIDENCE_BUCKET | (환경변수 필수) | (환경변수 필수) | ⚠️ Admin에게 버킷 이름 확인 |
| AWS_REGION | ap-northeast-2 | ap-northeast-2 | ✅ 동일 |

> **NOTE**: `leh-evidence-dev`는 더 이상 사용하지 않음 (임시 로컬 테스트용이었음)

---

## 4. 데이터 흐름 (수정 후)

```
┌─────────────┐     1. Presigned URL 요청
│  Frontend   │◄──────────────────────────────┐
└─────────────┘                               │
       │                                      │
       │ 2. 파일 업로드                        │
       ▼                                      │
┌─────────────┐                               │
│     S3      │                               │
│  (cases/)   │                               │
└─────────────┘                               │
       │                                      │
       │ 3. S3 Event (ObjectCreated)          │
       ▼                                      │
┌─────────────┐                               │
│   Lambda    │                               │
│ (AI Worker) │                               │
└─────────────┘                               │
       │                                      │
       │ 4. 파싱 & 분석                        │
       ▼                                      │
┌─────────────┐     ┌─────────────┐           │
│  DynamoDB   │     │   Qdrant    │           │
│ (UPDATE)    │     │ (INSERT)    │           │
└─────────────┘     └─────────────┘           │
       │                                      │
       │ 5. status: pending → processed       │
       ▼                                      │
┌─────────────┐     6. GET /evidence/{id}     │
│   Backend   │───────────────────────────────┘
└─────────────┘
```

---

## 5. 작업 체크리스트

### Phase 1: AI Worker 수정
- [ ] `handler.py`: `extract_evidence_id_from_s3_key()` 함수 추가
- [ ] `metadata_store.py`: `update_evidence_status()` 메서드 추가
- [ ] `handler.py`: `route_and_process()` 수정 - UPDATE 로직 추가

### Phase 2: 테스트
- [ ] Unit test: `test_update_evidence_status()`
- [ ] Integration test: E2E 흐름 테스트
- [ ] 기존 테스트 통과 확인

### Phase 3: 문서화
- [ ] 환경변수 확인 및 문서화
- [ ] API 흐름 다이어그램 업데이트

### Phase 4: 배포 준비
- [ ] Lambda 배포 테스트 (로컬 Docker)
- [ ] S3 버킷 권한 확인 (Admin 필요)

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| S3 버킷 권한 없음 | Lambda가 파일 읽기 불가 | Admin에게 권한 요청 |
| DynamoDB 테이블명 불일치 | 레코드 찾기 실패 | 환경변수 통일 |
| evidence_id 파싱 실패 | 새 레코드 생성 (fallback) | 로깅 및 모니터링 |

---

## 7. 예상 소요 시간

| Phase | 작업 | 소요 시간 |
|-------|------|----------|
| 1 | AI Worker 수정 | 2시간 |
| 2 | 테스트 | 1시간 |
| 3 | 환경변수 통일 | 30분 |
| 4 | 배포 준비 | 1시간 |
| **합계** | | **4.5시간** |

---

*작성일: 2025-12-01*
*작성자: AI Worker 담당 (L)*
