
## LEH Backend Service / Repository 패턴 & 클린코드 가이드

> **대상:** H(Backend 담당), AI 코드 생성기  
> **기술 스택:** FastAPI · SQLAlchemy · Pydantic · AWS Adapter Layer  
> **목표:** 서비스/레포지토리/인프라/도메인을 명확히 분리하여  
> 유지보수성 · 확장성 · 테스트 용이성을 극대화하는 백엔드 아키텍처 확립

---

# 1. 레이어드 구조 (Layered Architecture)

백엔드의 기본 구조는 다음과 같다.

backend/app/
  api/             # FastAPI 라우터 (입출력/HTTP)
  schemas/         # Pydantic DTO
  models/          # SQLAlchemy 모델
  services/        # 비즈니스 로직
  repositories/    # DB 및 외부 리소스 접근
  utils/           # AWS, Qdrant, DynamoDB Adapter

---

# 2. 책임 분리 (Responsibility Separation)

각 계층은 반드시 자신의 책임만 수행해야 한다.

---

## 2.1 api/ — HTTP 엔드포인트 계층

**역할:**

* 라우팅(path, method, status code)
* Request validation (Pydantic)
* Response wrapping
* 서비스(Service) 호출
* 인증/권한 검사

**금지:**

* ❌ 비즈니스 로직 직접 처리
* ❌ SQL 직접 호출
* ❌ AWS SDK 직접 호출

### 예시

 python
@router.post("/cases", response_model=CaseOut)
def create_case(
    payload: CaseCreate,
    svc: CaseService = Depends(...),
    current_user: User = Depends(get_user),
):
    return svc.create_case(payload, current_user)

---

## 2.2 services/ — 비즈니스 로직 계층

**역할:**

* 도메인 중심 로직 수행
* 여러 Repository 조합해서 Use Case 구현
* 예외(도메인 에러) 발생
* 외부 인프라 호출은 Adapter Layer에 위임

### 예시

 python
class CaseService:
    def **init**(
        self,
        case_repo: CaseRepository,
        member_repo: CaseMemberRepository,
        search: SearchClient
    ):
        self.case_repo = case_repo
        self.member_repo = member_repo
        self.search = search

    def create_case(self, payload: CaseCreate, user: User) -> Case:
        case = self.case_repo.create(payload, owner=user)
        self.member_repo.add_member(case.id, user.id, role="owner")
        self.search.init_case_index(case.id)
        return case

**규칙:**

* 서비스 메서드 하나 = 하나의 Use Case
* 서비스 간 의존성은 **생성자 주입(명시적 DI)**

---

## 2.3 repositories/ — 데이터 접근 계층

**역할:**

* DB 접근(SQLAlchemy ORM)
* low-level CRUD
* 트랜잭션을 직접 관리하지 않는다 (FastAPI dependency에서 관리)

### 예시

 python
class CaseRepository:
    def **init**(self, session: Session):
        self.session = session

    def create(self, payload: CaseCreate, owner: User) -> Case:
        case = Case(**payload.dict(), owner_id=owner.id)
        self.session.add(case)
        self.session.flush()
        return case

---

# 3. DTO & 모델 분리 규칙

| 계층         | 목적      | 파일            |
| ---------- | ------- | ------------- |
| `models/`  | DB 스키마  | SQLAlchemy 모델 |
| `schemas/` | API 입출력 | Pydantic DTO  |

### 원칙

* **API 레이어는 반드시 Pydantic schemas 사용**
* **Service/Repository는 SQLAlchemy models 사용**
* models → schemas 변환은 DTO classmethod 이용

---

# 4. 예외 처리 패턴 (Exception Pattern)

## 4.1 도메인 예외 정의

 python
class CaseNotFound(AppError): ...
class AccessDenied(AppError): ...

Service는 이러한 도메인 예외를 발생시키고,
API 레이어가 HTTP 상태로 변환한다.

## 4.2 FastAPI 예외 핸들러

 python
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )

---

# 5. 외부 연동 (S3 / Dynamo / Qdrant)

Backend는 **읽기, 조회 중심** 역할이 많다.

* 모든 외부 연동은 `utils/` 또는 `adapters/` 내에서 캡슐화한다.
* Services → adapters 호출
* adapters → SDK 호출

### 예시

 python
class EvidenceQueryService:
    def **init**(self, dynamo: EvidenceStore, s3: S3Client):
        self.dynamo = dynamo
        self.s3 = s3

    def list_evidence(self, case_id: str) -> list[EvidenceDto]:
        records = self.dynamo.list_by_case(case_id)
        return [EvidenceDto.from_record(r) for r in records]

---

# 6. 트랜잭션 관리

SQLAlchemy 세션은 FastAPI dependency에서 관리한다.

 python
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

**규칙:**

* Repository/Service는 트랜잭션을 직접 건드리지 않는다.
* 한 요청(Request) = 한 트랜잭션(Session)

---

# 7. 테스트 전략 (Backend)

## 7.1 서비스 레벨 테스트

* 테스트 DB 사용 (SQLite memory or test schema)
* Repository는 실제 DB 트랜잭션 기반
* 외부 Adapter는 mock

## 7.2 API 레벨 테스트

FastAPI TestClient 사용:

인증 → 권한 검사 → 서비스 → 레포지토리

엔드투엔드에 가까운 흐름을 테스트한다.

---

# 8. 클린코드 규칙 (Backend 전용)

* 하나의 서비스 메서드는 하나의 Use Case만 담당
* 서비스 간 의존성 = 명시적 생성자 주입
* 비대해진(Fat) 서비스 발견 시 도메인 단위로 분리
* Helper 함수가 너무 많아지면:

  * utils / adapters / repository 분리를 재검토
* Repo는 DB 접근 전용 (로직 넣지 않음)

---

# 9. 예시: 사건 종료 Use Case

 python
class CaseService:
    def close_case(self, case_id: str, user: User) -> Case:
        case = self.case_repo.get(case_id)
        if case is None:
            raise CaseNotFound()

        if not self.member_repo.can_manage_case(case_id, user.id):
            raise AccessDenied()

        case.status = "closed"
        self.case_repo.save(case)

        self.search_client.delete_case_index(case_id)

        return case

### 계층별 동작

* **API:** HTTP 200 + `CaseOut` 반환
* **Service:** 권한 검사 → 상태 변경 → 인덱스 삭제
* **Repository:** DB 저장
* **SearchClient:** Qdrant index 삭제

### 장점

* 권한 정책 변경
* 인덱스 구조 변경
* DB 스키마 변경
  모두 **각 레이어별로 독립적** 리팩터링 가능

---

# 10. 결론

이 가이드는 Backend 개발 시 다음을 보장하기 위한 기준이다.

* 서비스 / 레포지토리 / 인프라 / 도메인의 **명확한 분리**
* 테스트 가능한 구조
* 기능 확장 및 유지보수 용이
* 일관된 패턴을 통한 AI 코드 생성 품질 향상

Backend 코드는 본 문서의 기준을 기반으로 작성되어야 하며,
AI 및 H 담당자는 **서비스/레포지토리 패턴을 반드시 준수**해야 한다.
