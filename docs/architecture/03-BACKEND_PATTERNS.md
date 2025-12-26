# 03. 백엔드 패턴 (Clean Architecture)

> **목표**: 왜 코드를 Router → Service → Repository로 나누는지, Dependency Injection이 뭔지 이해합니다.

---

## Clean Architecture란?

**Clean Architecture (클린 아키텍처)**는 코드를 역할별로 계층화하여 유지보수성을 높이는 설계 패턴입니다.

### 비유: 회사 조직도

```
┌─────────────────────────────────────────────────────────────┐
│                      고객 (HTTP 요청)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     접수 데스크 (Router)                      │
│                                                              │
│  "무엇을 원하시나요?" → 요청을 받아서 적절한 담당자에게 전달     │
│  HTTP 관련 일만 처리 (상태코드, 쿠키, 헤더)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     담당자 (Service)                          │
│                                                              │
│  실제 업무 처리 (비즈니스 로직)                               │
│  "비밀번호 맞는지 확인하고, 토큰 만들고, 권한 체크하고..."       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     창고 관리자 (Repository)                  │
│                                                              │
│  데이터 보관/조회만 담당                                      │
│  "이 사용자 정보 찾아줘", "이 데이터 저장해줘"                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     창고 (Database)                          │
│                                                              │
│  PostgreSQL, DynamoDB, Qdrant...                            │
└─────────────────────────────────────────────────────────────┘
```

### 왜 나누나요?

**문제 상황**: 모든 코드가 한 파일에 있다면?

```python
# ❌ 나쁜 예: 모든 것이 한 곳에
@router.post("/login")
def login(email: str, password: str):
    # HTTP 처리
    # 비밀번호 검증
    # 토큰 생성
    # DB 조회
    # 쿠키 설정
    # ... 수백 줄의 코드
```

**문제점**:
1. 코드가 너무 길어서 읽기 어려움
2. 테스트하기 어려움 (DB 없이 테스트 불가)
3. 재사용 불가 (다른 곳에서 같은 로직 필요하면 복사?)
4. 수정 시 영향 범위 파악 어려움

**해결**: 역할별로 분리!

---

## LEH의 Clean Architecture

### 계층 구조

```
backend/app/
│
├── api/           ← Layer 1: Router (Presentation)
│                    HTTP 요청/응답만 처리
│
├── services/      ← Layer 2: Service (Business Logic)
│                    비즈니스 규칙 처리
│
├── repositories/  ← Layer 3: Repository (Data Access)
│                    데이터베이스 CRUD만 처리
│
└── db/models/     ← Layer 4: Entity (Domain)
                     데이터 구조 정의
```

### 의존성 방향 (중요!)

```
Router  →  Service  →  Repository  →  Database
  ↓           ↓             ↓
  │           │             │
  │           │             └── SQLAlchemy, boto3
  │           │
  │           └── 비즈니스 로직 (권한 체크, 검증, 변환)
  │
  └── HTTP 관련 (상태코드, 쿠키, 헤더)
```

**규칙**: 화살표 방향으로만 의존!
- Router는 Service를 사용 가능
- Service는 Repository를 사용 가능
- **역방향 금지**: Repository가 Service를 import하면 안 됨

---

## 실제 코드로 보는 예시: 로그인

### 1. Router (api/auth.py)

**역할**: HTTP 요청을 받아서 Service에 전달, 결과를 HTTP 응답으로 변환

```python
# backend/app/api/auth.py

from fastapi import APIRouter, Depends, Response
from app.services.auth_service import AuthService
from app.db.schemas.auth import LoginRequest, TokenResponse
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,      # 입력: 이메일, 비밀번호
    response: Response,             # HTTP 응답 객체
    db: Session = Depends(get_db)   # DB 세션 (의존성 주입)
):
    """
    Router가 하는 일:
    1. HTTP 요청에서 데이터 추출 (자동으로 됨)
    2. Service에게 비즈니스 로직 위임
    3. HTTP 응답 처리 (쿠키 설정 등)
    """
    # Service 생성 (DB 세션 전달)
    auth_service = AuthService(db)

    # Service에게 로그인 처리 위임
    token_response = auth_service.login(
        email=credentials.email,
        password=credentials.password
    )

    # HTTP 응답에 쿠키 설정 (이건 HTTP 관련이라 Router에서 처리)
    response.set_cookie(
        key="access_token",
        value=token_response.access_token,
        httponly=True,  # JavaScript에서 접근 불가 (보안)
        secure=True,    # HTTPS에서만 전송
    )

    return token_response
```

**포인트**:
- HTTP 관련 코드만 있음 (쿠키, 응답)
- 비즈니스 로직은 Service에 위임
- `Depends(get_db)` → 의존성 주입 (아래에서 설명)

---

### 2. Service (services/auth_service.py)

**역할**: 비즈니스 로직 처리 (검증, 변환, 규칙 적용)

```python
# backend/app/services/auth_service.py

from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.db.schemas.auth import TokenResponse

class AuthService:
    def __init__(self, db: Session):
        """
        Service가 Repository를 사용하기 위해 DB 세션을 받음
        """
        self.user_repo = UserRepository(db)

    def login(self, email: str, password: str) -> TokenResponse:
        """
        Service가 하는 일:
        1. 사용자 조회 (Repository 사용)
        2. 비밀번호 검증 (비즈니스 로직)
        3. 토큰 생성 (비즈니스 로직)
        4. 응답 데이터 구성
        """
        # 1. Repository에게 사용자 조회 요청
        user = self.user_repo.get_by_email(email)

        # 2. 사용자 존재 여부 확인 (비즈니스 규칙)
        if not user:
            raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

        # 3. 비밀번호 검증 (비즈니스 로직)
        if not verify_password(password, user.hashed_password):
            raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다")

        # 4. 계정 상태 확인 (비즈니스 규칙)
        if user.status != "active":
            raise ValueError("비활성화된 계정입니다")

        # 5. JWT 토큰 생성 (비즈니스 로직)
        access_token = create_access_token(
            data={"sub": user.id, "role": user.role}
        )

        # 6. 응답 구성
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id
        )
```

**포인트**:
- HTTP 관련 코드 없음 (쿠키, 상태코드 등)
- 비즈니스 규칙만 처리 (검증, 토큰 생성)
- Repository를 통해 DB 접근
- 테스트하기 쉬움 (Repository를 mock 가능)

---

### 3. Repository (repositories/user_repository.py)

**역할**: 데이터베이스 CRUD 작업만 처리

```python
# backend/app/repositories/user_repository.py

from sqlalchemy.orm import Session
from app.db.models.auth import User

class UserRepository:
    def __init__(self, db: Session):
        """
        DB 세션을 받아서 저장
        """
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        """
        Repository가 하는 일:
        이메일로 사용자 조회 (순수 DB 작업)
        """
        return self.db.query(User).filter(
            User.email == email
        ).first()

    def get_by_id(self, user_id: str) -> User | None:
        """
        ID로 사용자 조회
        """
        return self.db.query(User).filter(
            User.id == user_id
        ).first()

    def create(self, email: str, hashed_password: str, role: str) -> User:
        """
        새 사용자 생성
        """
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        self.db.add(user)
        self.db.flush()  # ID 생성을 위해
        return user
```

**포인트**:
- 순수 DB 작업만 (쿼리, 저장, 삭제)
- 비즈니스 로직 없음 (검증, 변환 등)
- SQLAlchemy 쿼리만 사용

---

## Dependency Injection (의존성 주입)

### DI란?

**의존성 주입 (Dependency Injection, DI)**은 필요한 객체를 외부에서 주입받는 방식입니다.

### 비유: 레스토랑

**DI 없이**:
```
셰프가 직접 시장 가서 재료 사 옴 (의존성 직접 생성)
→ 시장이 바뀌면 셰프 코드 수정 필요
```

**DI 사용**:
```
재료 담당자가 셰프에게 재료 전달 (의존성 주입)
→ 시장이 바뀌어도 셰프 코드는 그대로
```

### FastAPI의 Depends

```python
from fastapi import Depends
from app.db.session import get_db

# get_db 함수: DB 세션을 생성하고 반환
def get_db():
    db = SessionLocal()  # 세션 생성
    try:
        yield db          # 세션 제공
        db.commit()       # 성공 시 커밋
    except Exception:
        db.rollback()     # 실패 시 롤백
    finally:
        db.close()        # 항상 세션 닫기

# Router에서 사용
@router.post("/login")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)  # ← DI! DB 세션을 주입받음
):
    # db를 바로 사용 가능
    auth_service = AuthService(db)
    ...
```

**Depends의 동작**:
1. FastAPI가 `get_db` 함수 실행
2. 생성된 DB 세션을 `db` 파라미터에 주입
3. 요청 처리 후 자동으로 정리 (commit/rollback/close)

### 인증 의존성

```python
# backend/app/core/dependencies.py

from fastapi import Depends, Header, Cookie
from app.core.security import decode_access_token

def get_current_user_id(
    authorization: str | None = Header(None),   # Authorization 헤더
    access_token: str | None = Cookie(None)     # 또는 쿠키
) -> str:
    """
    JWT 토큰에서 사용자 ID 추출

    사용 순서:
    1. Authorization 헤더에서 토큰 확인
    2. 없으면 쿠키에서 토큰 확인
    3. 토큰 디코딩해서 user_id 반환
    """
    token = None

    # 헤더에서 토큰 추출
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # 쿠키에서 토큰 추출
    if not token and access_token:
        token = access_token

    if not token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")

    # 토큰 디코딩
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")

    return payload["sub"]  # user_id 반환

# Router에서 사용
@router.get("/me")
def get_current_user(
    user_id: str = Depends(get_current_user_id)  # ← 인증된 사용자 ID
):
    # user_id가 자동으로 주입됨
    # 인증 안 되면 여기까지 오기 전에 401 에러
    ...
```

### 의존성 체이닝

```python
def get_current_user(
    user_id: str = Depends(get_current_user_id),  # 먼저 실행
    db: Session = Depends(get_db)                  # 그 다음 실행
) -> User:
    """
    user_id를 이용해 User 객체 조회
    """
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

# Router에서 User 객체 바로 사용
@router.get("/profile")
def get_profile(
    current_user: User = Depends(get_current_user)  # User 객체 주입
):
    return {"name": current_user.name, "email": current_user.email}
```

---

## 테스트 용이성

### Clean Architecture의 장점: 테스트하기 쉬움

```python
# tests/services/test_auth_service.py

from unittest.mock import Mock
from app.services.auth_service import AuthService

def test_login_success():
    """
    Repository를 Mock으로 대체해서 테스트
    실제 DB 없이 Service 로직만 테스트 가능!
    """
    # Mock Repository 생성
    mock_db = Mock()
    mock_user = Mock(
        id="user_1",
        email="test@test.com",
        hashed_password="$2b$12$...",  # 해시된 비밀번호
        status="active"
    )

    # Repository의 get_by_email이 mock_user를 반환하도록 설정
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Service 테스트
    service = AuthService(mock_db)
    result = service.login("test@test.com", "password123")

    # 검증
    assert result.user_id == "user_1"
    assert result.access_token is not None
```

---

## 정리: 각 계층의 역할

| 계층 | 파일 위치 | 역할 | 포함하면 안 되는 것 |
|------|----------|------|-------------------|
| **Router** | `api/*.py` | HTTP 요청/응답 처리 | 비즈니스 로직, DB 쿼리 |
| **Service** | `services/*.py` | 비즈니스 로직 | HTTP 코드, 직접 DB 접근 |
| **Repository** | `repositories/*.py` | 데이터 CRUD | 비즈니스 로직 |
| **Model** | `db/models/*.py` | 데이터 구조 정의 | 로직 |
| **Schema** | `schemas/*.py` | API 입출력 DTO | DB 쿼리 |

---

## 🛠 유지보수 및 캡슐화 가이드

### 1. 비즈니스 로직의 위치
모든 비즈니스 로직(검증, 외부 API 호출, 복잡한 데이터 변환)은 반드시 **Service 계층**에 위치해야 합니다. Router(api/)에는 최소한의 요청 파싱 및 응답 처리만 남깁니다.

> [!CAUTION]
> **LSSP Pipeline**처럼 Router 내에 직접 비즈니스 로직을 구현하는 것은 기술 부채(Technical Debt)를 유발하며 유지보수를 어렵게 만듭니다.

### 2. 에러 핸들링
- 가급적 `app.middleware.error_handler`에 정의된 `LEHException` 하위 클래스를 사용하세요.
- 예외 발생 시 자동으로 생성되는 `error_id`는 로그 추적의 핵심 키입니다.

### 3. 로깅 전략
- 민감 정보(PII)는 `SensitiveDataFilter`에 의해 자동으로 마스킹됩니다.
- 핵심 비즈니스 흐름 전환점에는 반드시 `logger.info`를 남겨 추적성을 확보하세요.

---

## 새 기능 추가 시 체크리스트

1. **Router 추가** (`api/new_feature.py`)
   - HTTP 엔드포인트 정의
   - 입력 검증 (Pydantic 스키마)
   - Service 호출

2. **Service 추가** (`services/new_feature_service.py`)
   - 비즈니스 로직 구현
   - Repository 사용

3. **Repository 추가** (`repositories/new_feature_repository.py`)
   - DB CRUD 작업

4. **Model/Schema 추가** (필요시)
   - `db/models/` - SQLAlchemy 모델
   - `db/schemas/` - Pydantic 스키마

5. **main.py에 Router 등록**
   ```python
   from app.api.new_feature import router as new_feature_router
   app.include_router(new_feature_router, prefix="/api")
   ```

---

**다음 문서**: [04. 데이터 흐름](04-DATA_FLOW.md) - 증거 업로드부터 초안 생성까지 데이터가 어떻게 흘러가는지 알아봅니다.
