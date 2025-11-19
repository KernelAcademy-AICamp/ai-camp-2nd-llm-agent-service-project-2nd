# LEH Backend Tests

TDD (Test-Driven Development) 방식으로 작성된 테스트 코드입니다.

## 📁 테스트 구조

```
tests/
├── conftest.py                  # 공통 fixtures (test_env, client, mock 객체들)
├── test_api/                    # API 엔드포인트 테스트
│   └── test_main.py             # main.py 앱 전체 테스트 (20 tests)
├── test_core/                   # Core 모듈 테스트
│   └── test_config.py           # config.py 테스트 (15 tests)
├── test_middleware/             # 미들웨어 테스트
│   ├── test_error_handler.py    # error_handler.py 테스트 (20 tests)
│   └── test_security.py         # security.py 테스트 (12 tests)
├── test_services/               # 서비스 레이어 테스트 (향후 추가)
└── test_repositories/           # 레포지토리 레이어 테스트 (향후 추가)
```

**총 테스트 수:** 67개

> 구조는 BACKEND_SERVICE_REPOSITORY_GUIDE.md에 따라 계층별로 분리되어 있습니다.

---

## 🚀 테스트 실행 방법

### 모든 테스트 실행

```bash
cd backend
pytest
```

### 특정 카테고리만 실행

```bash
# 단위 테스트만
pytest -m unit

# 통합 테스트만
pytest -m integration

# 느린 테스트 제외
pytest -m "not slow"
```

### 특정 디렉토리만 실행

```bash
# API 테스트만
pytest tests/test_api/

# Core 모듈 테스트만
pytest tests/test_core/

# 미들웨어 테스트만
pytest tests/test_middleware/
```

### 특정 파일만 실행

```bash
# config.py 테스트만
pytest tests/test_core/test_config.py

# error_handler.py 테스트만
pytest tests/test_middleware/test_error_handler.py

# main.py 통합 테스트만
pytest tests/test_api/test_main.py
```

### 특정 테스트 함수만 실행

```bash
pytest tests/test_core/test_config.py::TestSettings::test_settings_loads_from_env
```

### 상세 출력 (verbose)

```bash
pytest -v
```

### 실패한 테스트만 재실행

```bash
pytest --lf  # last-failed
```

### 테스트 커버리지 확인

```bash
pytest --cov=app --cov-report=html
# 결과: htmlcov/index.html 생성됨
```

---

## 📋 테스트 마커 (Markers)

pytest.ini에 정의된 마커들:

- `@pytest.mark.unit` - 단위 테스트
- `@pytest.mark.integration` - 통합 테스트
- `@pytest.mark.slow` - 느린 테스트 (skip 가능)
- `@pytest.mark.requires_aws` - AWS 서비스 필요 (미구현)
- `@pytest.mark.requires_db` - DB 연결 필요 (미구현)

---

## 🧪 작성된 테스트 목록

### Unit Tests (47개)

#### test_config.py (15개)
- ✅ Settings 환경변수 로딩
- ✅ 기본값 설정
- ✅ CORS origins 리스트 변환
- ✅ DATABASE_URL 자동 생성
- ✅ S3 Presigned URL 만료 시간 제한
- ✅ Feature flags 기본값
- ✅ AWS/OpenAI 설정 검증

#### test_error_handler.py (20개)
- ✅ 커스텀 예외 클래스 (LEHException, AuthenticationError 등)
- ✅ 에러 핸들러 응답 형식 (JSON, error_id, timestamp)
- ✅ HTTP 예외 처리
- ✅ Validation 에러 처리
- ✅ 일반 예외 처리 (dev vs prod 모드)
- ✅ 에러 핸들러 등록

#### test_security.py (12개)
- ✅ 보안 헤더 추가 (X-Content-Type-Options, X-Frame-Options 등)
- ✅ HSTS 헤더 (프로덕션 전용)
- ✅ CSP, Permissions-Policy
- ✅ HTTPS 리다이렉트 (프로덕션 전용)
- ✅ 경로/쿼리 파라미터 보존
- ✅ 미들웨어 통합

### Integration Tests (20개)

#### test_main.py
- ✅ 앱 시작 성공
- ✅ OpenAPI 스키마 (title, version)
- ✅ 루트 엔드포인트 (/, 서비스 정보)
- ✅ Health check (/health, 200 OK, 응답 속도)
- ✅ 미들웨어 통합 (CORS, 보안 헤더, 에러 핸들러)
- ✅ 잘못된 요청 처리 (404, 405)
- ✅ CORS 설정
- ✅ 동시 요청 처리

---

## 🛠 Fixtures (conftest.py)

### 환경 설정
- `test_env` - 테스트용 환경변수 설정
- `mock_settings` - Mock Settings 객체

### 클라이언트
- `client` - FastAPI TestClient

### Mock 객체
- `mock_db_session` - Mock 데이터베이스 세션
- `mock_s3_client` - Mock boto3 S3 클라이언트
- `mock_dynamodb_client` - Mock DynamoDB 클라이언트
- `mock_opensearch_client` - Mock OpenSearch 클라이언트
- `mock_openai_client` - Mock OpenAI 클라이언트

### 샘플 데이터
- `sample_case_data` - 샘플 사건 데이터
- `sample_evidence_data` - 샘플 증거 데이터
- `sample_user_data` - 샘플 사용자 데이터

---

## ✅ TDD 워크플로우

### 1. Red - 실패하는 테스트 작성

```python
def test_new_feature():
    """Test new feature that doesn't exist yet"""
    result = my_new_function()
    assert result == "expected"
```

### 2. Green - 최소한의 코드로 테스트 통과

```python
def my_new_function():
    return "expected"
```

### 3. Refactor - 코드 개선

```python
def my_new_function():
    # Improved implementation
    return calculate_result()
```

### 4. 테스트 실행 확인

```bash
pytest tests/unit/test_my_module.py -v
```

---

## 📝 테스트 작성 가이드

### 단위 테스트 (Core, Middleware 등)

```python
import pytest
from app.core.module import my_function

@pytest.mark.unit
class TestMyFunction:
    """Test my_function behavior"""

    def test_returns_correct_value(self):
        """Test that function returns expected value"""
        result = my_function(input="test")
        assert result == "expected"

    def test_raises_error_on_invalid_input(self):
        """Test that function raises error for invalid input"""
        with pytest.raises(ValueError):
            my_function(input=None)
```

### 통합 테스트 (API 엔드포인트)

```python
import pytest

@pytest.mark.integration
class TestAPIEndpoint:
    """Test API endpoint integration"""

    def test_endpoint_returns_200(self, client):
        """Test that endpoint returns 200 OK"""
        response = client.get("/api/endpoint")
        assert response.status_code == 200
```

### 서비스 레이어 테스트

```python
import pytest
from app.services.case_service import CaseService

@pytest.mark.unit
class TestCaseService:
    """Test CaseService business logic"""

    def test_create_case_success(self, mock_case_repo):
        """Test case creation with valid data"""
        service = CaseService(case_repo=mock_case_repo)
        case = service.create_case(title="Test Case")
        assert case.title == "Test Case"
```

---

## 🐛 테스트 디버깅

### 테스트 실패 시 디버깅

```bash
# 실패한 테스트에서 즉시 중단
pytest -x

# 마지막 실패 지점에서 디버거 실행
pytest --pdb

# 상세 로그 출력
pytest -v --tb=long

# 특정 테스트만 실행하며 print 출력 표시
pytest tests/test_core/test_config.py::test_name -s
```

---

## 📊 CI/CD 통합

GitHub Actions에서 테스트 실행:

```yaml
- name: Run tests
  run: |
    cd backend
    pytest --cov=app --cov-report=xml
```

---

## 🔜 향후 추가할 테스트

- [ ] JWT 인증 미들웨어 테스트
- [ ] Audit Log 미들웨어 테스트
- [ ] Database 모델 테스트 (SQLAlchemy)
- [ ] API 라우터 테스트 (auth, cases, evidence, draft)
- [ ] S3 서비스 테스트
- [ ] DynamoDB 서비스 테스트
- [ ] OpenSearch 서비스 테스트
- [ ] Draft 생성 서비스 테스트 (GPT-4o 통합)
- [ ] E2E 테스트 (전체 플로우)
