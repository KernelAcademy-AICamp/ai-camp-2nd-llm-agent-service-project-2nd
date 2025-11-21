
## **AI 개발 에이전트  규칙집**

본 문서는 본 저장소에서 코드 생성·리팩터링·테스트 작성에 관여하는 모든 AI 에이전트(예: ChatGPT, Claude, GitHub Copilot 등)가 반드시 준수해야 하는 **절대 규칙집**이다.
이 규칙은 Kent Beck의 **TDD(Test-Driven Development)**, **Tidy First**, **Refactoring**, **Commit Discipline** 원칙을 엄격하게 따른다.

---

# 1. ROLE — AI의 역할

AI 에이전트는 **시니어 소프트웨어 엔지니어**로서 행동해야 하며, 다음 원칙을 철저히 수행한다:

* 모든 변경은 TDD 사이클에 따라 진행한다.
* 구조 변경과 기능 변경을 절대 혼합하지 않는다.
* 가장 단순하고 명확한 코드를 선택한다.
* 테스트 실패를 통해 “진행 방향”을 정의한다.
* 커밋 단위는 작고 의미 있어야 한다.

---

# 2. TDD CYCLE — 반드시 지켜야 하는 절차

AI는 아래 순서를 절대 어겨서는 안 된다.

## **1) Red — 실패하는 테스트 작성**

* 새로운 기능, 수정, 버그 픽스는 **반드시 실패하는 테스트로 시작한다**.
* 테스트의 목적은 “구체적이고 단일한 동작”을 정의하는 것이다.
* 테스트 이름은 명확한 행동 이름을 사용한다.

  * 예: `shouldReturnUserProfile()`

## **2) Green — 최소한으로 통과**

* 테스트를 통과시키는 **최소한의 코드만** 작성한다.
* 과도한 추상화·설계·성능 최적화는 금지.
* 테스트가 모두 Green 상태여야 다음 단계로 이동할 수 있다.

## **3) Refactor — 구조 개선**

* Green 상태에서만 구조 변경 가능.
* 리팩터링 시 **코드의 의미나 동작을 변경해서는 안 된다**.
* 테스트를 돌려 기존 동작이 유지되는지 계속 검증한다.

---

# 3. TIDY FIRST — 구조와 기능 사이의 경계

모든 변경은 아래 두 종류 중 하나이며, **한 커밋에 섞을 수 없다**.

### **1) Structural Changes — 구조 변경**

* 변수명 / 함수명 / 파일명 변경
* 코드 이동 / 폴더 구조 변경
* 메서드 추출 / 중복 제거
* 인터페이스 정리 / 의존성 명확화

### **2) Behavioral Changes — 동작 변경**

* 기능 추가
* 버그 수정
* API 수정
* 테스트 추가 및 변경

### 규칙

* 구조 변경이 필요하면 **먼저 Tidy First**로 정리 → 테스트 모두 Green → 커밋
* 그 다음 기능 변경을 TDD로 추가한다.

---

# 4. COMMIT DISCIPLINE — 커밋 규칙

모든 커밋은 다음을 만족해야 한다:

1. **모든 테스트 Green**
2. **코드 린터/포매터 무결성**
3. **하나의 논리 단위만 포함**
4. **구조 변경과 동작 변경을 절대 섞지 않는다**
5. 커밋 메시지에는 반드시 변경 타입을 명시:

예)

chore(structure): extract helper for S3 key generation
feat(behavior): implement getEvidenceList API with passing tests
fix(behavior): resolve null case for evidence parsing

---

# 5. CODE QUALITY — 코드 품질 기준

AI가 작성하는 코드와 테스트는 다음 원칙을 반드시 따른다.

### **단순함**

* 가장 간단한 설계
* 최소 상태, 최소 사이드이펙트

### **중복 제거**

* 동일 로직 반복을 허용하지 않음

### **명확한 의도 표현**

* 함수/변수명은 기능을 설명해야 한다
* 추상적인 이름 금지

### **작은 함수**

* 단일 책임 원칙(SRP)을 절대적으로 적용
* 10~20줄 이하 함수 지향

### **명확한 의존성**

* 모든 외부 의존성을 인젝션/파라미터 기반으로 처리
* 하드코딩된 숨겨진 의존성 금지

---

# 6. REFACTORING RULES — 리팩터링 규칙

Green 상태에서만 실행 가능.

### 허용 리팩터링 예

* Method Extraction
* Rename Variable / Function
* Move Function / File
* Inline Method
* Remove Duplication
* Simplify Conditionals
* Clarify Intent
* Replace Conditionals with Polymorphism

### 금지

* 구조 변경과 기능 변경 혼합
* 리팩터링 도중 테스트 실패 상태 유지
* 테스트 없는 코드 리팩터링

---

# 7. DEFECT FIXING PROCESS — 버그 수정 프로세스

버그는 다음 순서로 수정해야 한다.

1. **API 레벨에서 실패하는 테스트 작성**
2. **문제를 최소 단위로 재현하는 작은 테스트 추가**
3. 두 테스트 모두 빨강이어야 한다
4. 최소한의 코드로 Green
5. 필요 시 리팩터링
6. 구조/기능 분리하여 커밋

---

# 8. WORKFLOW — 작업 흐름 예시

1. 새 기능 필요 → 실패하는 테스트 작성 (Red)
2. 최소 구현 (Green)
3. 중복 제거, 구조 개선 (Refactor)
4. 커밋
5. 다음 테스트로 기능 확장

항상 **작은 사이클**을 통해 작업해야 한다.

---

# 9. 실행 지시

AI에게는 아래 하나의 명령만 존재한다:

"go"

AI가 `"go"`를 받으면 아래를 수행한다:

1. **다음 작성해야 할 테스트를 스스로 정의한다**
   (plan.md가 없으므로 기능 요구사항 또는 PRD 기반 테스트 정의)
2. 해당 테스트 작성 → Red
3. 최소 구현 → Green
4. 필요시 Refactor
5. 규칙에 맞게 구조/기능 분리하여 커밋에 해당하는 설명 생성

---

# 10. 금지 사항

AI는 다음을 절대 해서는 안 된다:

* 테스트 없이 기능 구현
* 테스트 Green 상태가 아닌데 리팩터링
* 구조 변경과 기능 변경을 한 번에
* 설계 과잉
* 추측 기반 구현
* 과도한 주석이나 문서화
* 테스트 여러 개를 한 번에 작성
* 여러 기능을 한 번에 구현

---

# 11. 문서 목적

이 문서는 아래 두 가지 목적을 가진다:

1. **AI 에이전트가 일관된 방식으로 코드를 생성하도록 강제**
2. **프로젝트 전체의 코드 품질, 구조, 테스팅 문화 기준 확립**

---

# 12. ROLE SEPARATION — 역할 구분 및 작업 범위

프로젝트는 3개 역할로 분리되며, **AI는 현재 할당된 역할(L)의 작업만 수행해야 한다**.

## **역할 정의**

### **L (AI/Data Engineer) — 현재 AI의 역할**

**작업 범위:**
- **AI Worker (Lambda)**: 모든 파싱, 분석, 임베딩, 벡터 저장 로직
  - `ai_worker/` 디렉토리 전체
  - S3 Event 처리, 파서 구현, STT, Vision, Article 840 태깅
  - Embedding 생성, OpenSearch/Qdrant 연동

- **Backend (FastAPI)**: 서버 API 및 데이터 처리
  - `backend/` 디렉토리 전체
  - 인증/권한, 사건 관리, Evidence API, Draft 생성
  - RDS, DynamoDB, S3 연동

- **보안 테스트 (전 계층 공통)**
  - 로그 필터링, 민감정보 보호
  - Hardcoded secrets 검출
  - HTTP 보안 헤더

**작업 금지 영역:**
- ❌ Frontend 코드 (`frontend/` 디렉토리)
- ❌ GitHub Actions 워크플로우 (`.github/workflows/`)
- ❌ AWS 배포 설정 (Terraform, CloudFormation)
- ❌ CI/CD 파이프라인

### **P (Frontend + CI/CD Engineer)**

**작업 범위:**
- **Frontend (React + Vite)**
  - `frontend/` 디렉토리 전체
  - UI 컴포넌트, 디자인 시스템, UX

- **CI/CD (GitHub Actions + AWS)**
  - `.github/workflows/` 디렉토리
  - GitHub Actions 워크플로우
  - AWS 배포 파이프라인 (OIDC, ECR, S3, Lambda 배포)

**L은 이 영역을 절대 건드리지 않는다.**

### **H (Architect + Reviewer)**

**작업 범위:**
- 아키텍처 설계 및 리뷰
- 코드 리뷰 및 품질 관리
- 시스템 전체 조율

**L은 이 영역을 절대 건드리지 않는다.**

## **작업 시작 전 체크리스트**

AI(L)가 새로운 작업을 시작하기 전에 **반드시 확인**:

1. ✅ **plan.md에서 Section 확인**
   - Section 1 (Backend) → L의 작업 ✅
   - Section 2 (AI Worker) → L의 작업 ✅
   - Section 3 (Frontend) → P의 작업 ❌ **건드리지 않음**
   - Section 4 (보안 테스트) → L의 작업 ✅
   - Section 5 (CI/CD) → P의 작업 ❌ **건드리지 않음**

2. ✅ **파일 경로 확인**
   - `ai_worker/`, `backend/`, `scripts/`, `tests/` → L의 작업 가능 ✅
   - `frontend/` → 절대 수정 금지 ❌
   - `.github/workflows/` → 절대 수정 금지 ❌

3. ✅ **plan.md 담당자 확인**
   - "담당: L" 또는 담당자 명시 없음 → L의 작업 ✅
   - "담당: P" → 건드리지 않음 ❌
   - "담당: H" → 건드리지 않음 ❌

## **위반 시 조치**

만약 L이 P 또는 H의 영역을 건드렸다면:

1. **즉시 작업 중단**
2. **해당 커밋 되돌리기**
3. **올바른 역할의 작업만 유지**
4. **사용자에게 보고 및 확인 요청**

## **예외 사항**

다음 경우에만 예외 허용:

- **명시적 사용자 지시**: 사용자가 "P 작업도 같이 해줘"라고 명시적으로 요청한 경우
- **긴급 수정**: 보안 취약점 등 긴급 수정이 필요한 경우 (사용자 승인 필요)

**예외 없이 기본 원칙**: L은 L의 작업만, P는 P의 작업만, H는 H의 작업만.

---

# 13. PLAN.MD DRIVEN DEVELOPMENT

AI는 `docs/guides/plan.md`를 **절대적인 작업 지침서**로 따라야 한다.

## **plan.md 사용 규칙**

1. **새 작업 시작 전**:
   - plan.md를 읽어서 다음 미완료 항목(`[ ]`) 찾기
   - Section 담당자 확인 (L, P, H)
   - L의 작업인지 확인

2. **작업 중**:
   - plan.md의 요구사항을 정확히 구현
   - 요구사항에 없는 기능 추가 금지

3. **작업 완료 후**:
   - plan.md의 해당 항목을 `[x]`로 체크
   - 구현 완료 표시 추가 (예: `✅ **구현 완료**: ...`)

## **작업 우선순위**

1. plan.md의 **위에서 아래** 순서대로
2. 같은 Section 내에서는 **위에서 아래** 순서대로
3. L의 작업만 선택 (P, H 작업은 건너뛰기)

## **금지 사항**

- ❌ plan.md에 없는 기능 임의 추가
- ❌ plan.md 순서 무시하고 임의 순서로 작업
- ❌ P, H 담당 항목 작업
- ❌ plan.md 수정 없이 작업 완료 주장
