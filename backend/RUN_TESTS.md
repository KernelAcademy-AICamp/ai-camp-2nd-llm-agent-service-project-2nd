# 🧪 테스트 실행 가이드

## 1️⃣ 첫 실행 (패키지 설치)

### 가상환경 생성 및 활성화

```bash
cd backend

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
# venv\Scripts\activate
```

### 의존성 패키지 설치

```bash
# pip 업그레이드
pip install --upgrade pip

# 모든 패키지 설치
pip install -r requirements.txt
```

---

## 2️⃣ 테스트 실행

### 모든 테스트 실행

```bash
pytest
```

**예상 결과:** 67개 테스트 모두 PASS

### 상세 출력으로 실행

```bash
pytest -v
```

### 특정 카테고리만 실행

```bash
# 단위 테스트만
pytest -m unit

# 통합 테스트만
pytest -m integration
```

### 특정 파일만 실행

```bash
# Config 테스트만
pytest tests/unit/test_config.py -v

# Error handler 테스트만
pytest tests/unit/test_error_handler.py -v

# Security 테스트만
pytest tests/unit/test_security.py -v

# Main 통합 테스트만
pytest tests/integration/test_main.py -v
```

---

## 3️⃣ 커버리지 확인 (선택)

```bash
# 커버리지 리포트 생성
pytest --cov=app --cov-report=html

# 브라우저에서 htmlcov/index.html 열기
open htmlcov/index.html
```

---

## 4️⃣ TDD 워크플로우

### 새 기능 개발 시

1. **테스트 먼저 작성** (Red)
   ```bash
   # tests/unit/test_new_feature.py 생성
   ```

2. **테스트 실행 (실패 확인)**
   ```bash
   pytest tests/unit/test_new_feature.py -v
   # FAILED - 아직 구현 안 됨
   ```

3. **최소한의 코드 작성** (Green)
   ```bash
   # app/new_feature.py 구현
   ```

4. **테스트 재실행 (통과 확인)**
   ```bash
   pytest tests/unit/test_new_feature.py -v
   # PASSED
   ```

5. **코드 리팩토링** (Refactor)
   ```bash
   # 코드 개선 후 다시 테스트
   pytest tests/unit/test_new_feature.py -v
   # 여전히 PASSED
   ```

---

## 5️⃣ 문제 해결

### Import 오류 발생 시

```bash
# PYTHONPATH 설정
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"

# 또는 pytest를 모듈로 실행
python -m pytest tests/
```

### 환경변수 오류 시

```bash
# .env 파일 확인
ls -la .env

# 없으면 .env.example 복사
cp ../.env.example .env
```

---

## ✅ 체크리스트

실행 전 확인사항:

- [ ] 가상환경 활성화됨
- [ ] requirements.txt 설치 완료
- [ ] backend 디렉토리에 있음
- [ ] .env 파일 존재 (또는 테스트용 환경변수 설정됨)

---

## 📊 예상 테스트 결과

```
tests/unit/test_config.py::TestSettings ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ (15 passed)
tests/unit/test_error_handler.py::TestCustomExceptions ✓✓✓✓✓✓✓✓✓✓ (10 passed)
tests/unit/test_error_handler.py::TestExceptionHandlers ✓✓✓✓✓✓✓✓✓✓ (10 passed)
tests/unit/test_security.py::TestSecurityHeadersMiddleware ✓✓✓✓✓ (5 passed)
tests/unit/test_security.py::TestHTTPSRedirectMiddleware ✓✓✓✓✓✓✓ (7 passed)
tests/integration/test_main.py ✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓✓ (20 passed)

======================== 67 passed in X.XXs ========================
```

---

## 🚀 다음 단계

테스트가 모두 통과하면:

1. 새로운 기능 개발 시 **반드시 테스트 먼저 작성**
2. PR 생성 전 `pytest` 실행하여 모든 테스트 통과 확인
3. CI/CD 파이프라인에서 자동 테스트 실행 설정
