# Design Patterns Guide

LEH 프로젝트에서 사용하는 핵심 디자인 패턴을 정의합니다.

**적용 대상:** Backend, AI Worker
**참고:** [CLEAN_ARCHITECTURE_GUIDE.md](CLEAN_ARCHITECTURE_GUIDE.md), [AI_WORKER_PATTERN_GUIDE.md](AI_WORKER_PATTERN_GUIDE.md)

---

## 1. Strategy Pattern (처리 분기)

증거 타입에 따라 다른 처리 로직을 실행해야 할 때 사용합니다.

### 문제
파일 확장자(image, audio, pdf, text)에 따라 다른 처리가 필요하지만, if-else 체인은 유지보수가 어렵습니다.

### 해결
각 파일 타입별 프로세서를 독립적으로 구현하고, handler가 선택만 합니다.

```
ai_worker/src/parsers/
├── base.py           # BaseParser 추상 클래스
├── text.py           # TextParser
├── image_ocr.py      # ImageOCRParser
├── image_vision.py   # ImageVisionParser
├── audio_parser.py   # AudioParser
├── video_parser.py   # VideoParser
└── pdf_parser.py     # PDFParser
```

```python
# handler.py
processor = select_processor(file_extension)
result = processor.parse(file_path)
```

### 장점
- 새 파일 타입 추가 시 기존 코드 수정 없음
- 각 파서를 독립적으로 테스트 가능

---

## 2. Adapter Pattern (외부 서비스 래핑)

AWS SDK 등 외부 의존성을 캡슐화하여 변경 영향을 최소화합니다.

### 문제
AWS SDK 버전 업그레이드나 서비스 변경 시 전체 코드가 영향 받는 문제.

### 해결
**Adapter Layer**를 만들어 외부 연동을 캡슐화합니다.

```
backend/app/utils/
├── s3.py         # S3 Adapter
├── dynamo.py     # DynamoDB Adapter
├── opensearch.py # OpenSearch Adapter
└── openai_client.py  # OpenAI Adapter
```

```python
# utils/s3.py
class S3Adapter:
    def upload_file(self, bucket, key, file): ...
    def generate_presigned_url(self, bucket, key, expires_in): ...
    def download_file(self, bucket, key): ...
```

### 장점
- 서비스/비즈니스 로직이 AWS SDK를 직접 모르는 상태로 운영
- 테스트 시 Adapter만 mock 처리

---

## 3. Factory Pattern (객체 생성)

일관된 형태의 객체 생성을 보장합니다.

### 사용처
- Evidence JSON 생성
- Draft 섹션 생성
- ParsedMessage 객체 생성

### 예시

```python
# evidence_factory.py
def create_evidence_metadata(
    case_id: str,
    evidence_id: str,
    file_type: str,
    content: str,
    speaker: str,
    timestamp: str,
    labels: list[str]
) -> dict:
    return {
        "case_id": case_id,
        "evidence_id": evidence_id,
        "type": file_type,
        "content": content,
        "speaker": speaker,
        "timestamp": timestamp,
        "labels": labels,
        "created_at": datetime.utcnow().isoformat()
    }
```

### 장점
- 필수 필드 누락 방지
- 일관된 데이터 구조 보장

---

## 4. CQRS Pattern (읽기/쓰기 분리)

쓰기와 읽기 데이터소스를 분리하여 각 워크로드에 최적화합니다.

### LEH 적용

| 작업 | 데이터소스 | 이유 |
|------|-----------|------|
| 사건 생성/수정 | RDS PostgreSQL | 트랜잭션, 관계형 데이터 |
| 증거 메타데이터 조회 | DynamoDB | 고속 key-value 조회 |
| 의미 검색 (RAG) | OpenSearch | 벡터 유사도 검색 |
| Draft 생성 | GPT-4o + RAG | AI 생성 |

### 원칙
- 쓰기 API와 읽기 API를 명확히 분리
- 읽기 전용 API는 캐시 적용 가능

---

## 5. Repository Pattern (데이터 접근 추상화)

데이터베이스 접근 로직을 비즈니스 로직에서 분리합니다.

### 구조

```
backend/app/repositories/
├── case_repository.py
├── user_repository.py
└── evidence_repository.py
```

```python
# case_repository.py
class CaseRepository:
    def get_by_id(self, case_id: str) -> Case: ...
    def create(self, case: CaseCreate) -> Case: ...
    def update(self, case_id: str, data: CaseUpdate) -> Case: ...
    def delete(self, case_id: str) -> None: ...
```

### 장점
- Service 레이어가 DB 구현체를 모름
- 테스트 시 Repository만 mock 처리

---

## 패턴 적용 체크리스트

| 상황 | 적용 패턴 |
|------|----------|
| 파일 타입별 다른 처리 | Strategy |
| AWS/외부 서비스 연동 | Adapter |
| 일관된 객체 생성 | Factory |
| 읽기/쓰기 분리 | CQRS |
| DB 접근 추상화 | Repository |

---

## 관련 문서
- [CLEAN_ARCHITECTURE_GUIDE.md](CLEAN_ARCHITECTURE_GUIDE.md) - 전체 아키텍처 원칙
- [BACKEND_SERVICE_REPOSITORY_GUIDE.md](BACKEND_SERVICE_REPOSITORY_GUIDE.md) - 백엔드 상세 패턴
- [AI_WORKER_PATTERN_GUIDE.md](AI_WORKER_PATTERN_GUIDE.md) - AI Worker 상세 패턴
