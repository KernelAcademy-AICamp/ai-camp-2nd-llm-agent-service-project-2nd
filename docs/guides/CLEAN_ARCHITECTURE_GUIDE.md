
### LEH 유지보수성 / 확장성 / 디자인 패턴 / 클린 코드 지침서

**Legal Evidence Hub (LEH) 전 구성요소(Frontend · Backend · AI Worker · CI/CD)를 위한 통합 설계 규칙**

---

# 0. 목적

이 문서는 LEH 프로젝트 전체에 걸쳐 다음을 일관되게 유지하기 위한 **최상위 품질 기준서**다:

* 유지보수성(maintainability)
* 확장성(extensibility)
* 모듈성(modularity)
* 디자인 패턴 적용
* 클린 코드(읽기 쉬움·명확함·일관성)
* 아키텍처 규율(Architecture consistency)
* TDD / Tidy First / Refactor-first 문화

이 문서는 프론트엔드(P), 백엔드(H), AI Worker(L), DevOps(P), AI Agent(Claude/GPT)의 **모든 코드 생성시 참고 기준**이다.

---

# 1. 아키텍처 기본 규칙 (Architecture Principles)

LEH는 다음 구조를 따른다.

Frontend  →  Backend(FastAPI) → S3 / DynamoDB / Qdrant / RDS
                      ↑
               AI Worker(Lambda/ECS)

### 1.1 계층 간 결합도 규칙

| 레이어       | 어떤 것을 참조할 수 있는가?                         |
| --------- | ---------------------------------------- |
| Frontend  | API Spec, DTO, 디자인 토큰                    |
| Backend   | DB, S3, Dynamo, Qdrant 등 “Infra 추상화” |
| AI Worker | AWS SDK, 모델 호출 adapter                   |
| Infra     | 자체 구현 없이 AWS 관리형 서비스                     |

### 🔒 금지 규칙

* ❌ FE가 AWS 리소스 직접 접근
* ❌ BE가 모델 호출 직접 수행(Worker가 담당)
* ❌ Worker가 프론트용 데이터 포맷을 직접 의존
* ❌ 레이어 역참조 (Frontend → Worker 등)

---

# 2. 도메인 구분 원칙 (Domain Separation)

프로젝트의 핵심 도메인은 다음과 같다:

* `CaseDomain`: 사건 생성/수정/권한 관리
* `EvidenceDomain`: 파일 업로드, 증거 메타, 라벨링, 타임스탬프
* `AIPipelineDomain`: OCR, STT, 의미 분석, Embedding
* `DraftDomain`: RAG 검색 + GPT-4o 초안 생성
* `UserDomain`: 인증, 권한, 멤버 관리

각 도메인은 독립적으로 진화해야 한다.

### 2.1 금지

* ❌ Evidence 로직을 Draft 로직에 넣기
* ❌ Draft 로직에서 Case 권한 검사 수행
* ❌ Worker 내부에서 Backend DTO import

---

# 3. Clean Code 원칙

다음은 **LEH 전체 공통 클린코드 표준**이다.

## 3.1 작게, 더 작게

* 함수 길이: 10–30줄
* 파일 길이: 300줄 이하가 바람직
* 함수 하나 = 단일 책임 (SRP)

## 3.2 함수 이름 규칙

* 함수의 이름만 봐도 “무엇을 하는지” 명확해야 한다.
* Backend 예:

  * `generate_presigned_url()`
  * `load_case_evidence_list()`
  * `parse_kakao_chat()`
  * `create_draft_sections()`
* Worker 예:

  * `process_image_ocr()`
  * `process_audio_stt()`
  * `extract_kakao_metadata()`

## 3.3 네이밍 원칙 (강제)

**신뢰·명확성 기반 이름**:

* `content` : 원문 텍스트
* `summary` : AI가 생성한 핵심 요약
* `labels` : 민법 840 라벨
* `speaker` : 대화 화자
* `timestamp` : 정규화된 UTC 시간

### 금지 네이밍

* ❌ tmp, data, foo, bar
* ❌ process1(), handle2()
* ❌ result, final, out 같은 모호한 이름

---

# 4. 폴더 구조 규칙

> **See also:** [FOLDER_STRUCTURE.md](FOLDER_STRUCTURE.md) - 전체 폴더 구조 상세

## 4.1 Backend (FastAPI)

backend/app/
  api/            → 라우팅
  core/           → 설정/보안/로그
  models/         → SQLAlchemy (DB)
  schemas/        → Pydantic (DTO)
  services/       → 비즈니스 로직
  utils/          → 외부 연동(aws, time)

### 규칙

* API는 DTO만 알고 있어야 한다.
* 비즈니스 로직은 service에만 존재.
* utils는 AWS/Qdrant 등 “외부 인프라 연동 전용”.

---

## 4.2 AI Worker

ai_worker/
  handler.py           → 엔트리
  processors/
      text_parser.py
      ocr_processor.py
      stt_processor.py
      embedding.py
  storage/
      dynamo.py
      s3.py
      qdrant.py
  workflows/
      leh_drive_ingestion_mvp.json

### 규칙

* 모든 AI 호출은 `processors/`에서만 실행
* 모든 DB/스토리지 연동은 `storage/`에서만 실행
* handler는 오케스트레이션만 수행한다

---

## 4.3 Frontend (Next.js or Vite + React)

frontend/src/
  pages/
  components/
  hooks/
  api/
  types/
  styles/

### 규칙

* 상태는 가능한 `React Query`로 관리
* 디자인 토큰은 단일 JSON으로 관리
* 컴포넌트는 “작고 독립적” + “논리/표현 분리”

---

# 5. 패턴 적용 지침 (Design Patterns)

> **See also:** [DESIGN_PATTERNS.md](DESIGN_PATTERNS.md) - 디자인 패턴 상세 가이드

Backend와 Worker는 다음 패턴을 강제한다.

---

## 5.1 Adapter Pattern (Infra 추상화)

### 문제

AWS SDK 등 외부 의존성이 변경되면 F/E, B/E, Worker 전체가 깨지는 문제.

### 해결

**Adapter Layer**를 만들어 AWS 연동을 캡슐화한다.

utils/s3.py:
    def upload_file(...)
    def generate_presigned_url(...)

Worker는 S3 SDK를 직접 모르는 상태로 운영한다.

---

## 5.2 Strategy Pattern (처리 분기)

증거 타입에 따라 Worker가 다른 로직을 실행해야 한다.

processors/
  text_parser.py
  ocr_processor.py
  stt_processor.py

`handler.py`는 다음처럼 Strategy를 선택만 한다:

python
processor = select_processor(file_extension)
processor.run(...)

---

## 5.3 Factory Pattern (Evidence / Draft)

* Evidence JSON 생성 시
* Draft 섹션 생성 시

Factory를 통해 일관된 형태를 유지한다.

---

## 5.4 CQRS 접근 (간접 적용)

* Backend는 **쓰기(RDS)** 와 **읽기(Dynamo/Qdrant)** 를 분리한다.

원칙:

* 사건 생성 → RDS
* 사건 증거 조회 → Dynamo
* 검색 → Qdrant
* Draft → GPT + RAG

---

# 6. 확장성 지침 (Scalability & Evolution)

## 6.1 증거 타입 추가

새 파일 타입(예: 동영상) 추가 시:

1. Worker `processors/`에 새로운 처리기 추가
2. handler에서 extension → processor 매핑만 추가
3. DynamoDB와 Qdrant는 동일 구조 사용
4. Backend/Frontend는 기존 API/컴포넌트 재사용

확장 비용이 최소화된다.

---

## 6.2 Draft GPT 모델 변경

GPT 모델 버전 교체 필요 시:

* Worker에는 영향 없음
* Backend `draft_service`에서 모델 provider만 교체
* prompt 템플릿 분리 → Provider DI (Dependency Injection)

---

# 7. 보안 + 코드 품질 준수

## 7.1 보안

* 절대 민감정보를 로그에 남기지 않기
* OpenAI 호출 시 PII 마스킹
* JWT 서명 키는 GitHub Secrets
* FE LocalStorage에 evidence 전문 저장 금지

---

# 8. CI/CD와 Clean Architecture

GitHub Actions + Oracle Cloud DevOps는 다음을 적용:

* Lint → Test → Build → Deploy 순서 고정
* main 배포 전 mandatory approval
* dev 환경은 자동
* CD는 CI 성공을 **강제로 의존(needs)**
* 각 단계는 재실행 가능하게 설계
* 배포 실패 시 자동 롤백 스크립트 준비

---

# 9. 코드 리뷰 규칙 (Pull Request Policy)

모든 PR은 다음을 만족해야 한다:

* 함수/파일이 너무 크면 거절
* 전역 변수 사용 금지
* TDD 기반: 테스트 없이 기능 구현 PR 금지
* "리팩터링"과 "기능 구현" PR은 반드시 분리
* 하나의 PR은 하나의 변경 목적만
* PR 설명에는 반드시 “Before / After / Why” 포함
* Reviewer(P/H/L 중 1명 이상) 승인 필수

---

# 10. 예시: 나쁜 코드 vs 좋은 코드

## ❌ Bad

python
def handle_file(f):
    # 200줄 짜리 복잡한 로직
    ...

## ✅ Good

python
def handle_file(f):
    processor = select_processor(f.ext)
    json = processor.run(f)
    save_to_dynamo(json)

---

# 11. 테스트 우선 원칙과의 정합성

* Clean Architecture는 TDD와 함께 사용할 때 가장 효과적이다.
* 도메인 로직을 테스트로 고정시키고,
* Adapter/Infra는 mock으로 대체하여 안정적으로 리팩터링할 수 있게 한다.

---

# 12. 결론

이 문서는 LEH 프로젝트의 **아키텍처·클린코드·패턴·확장성**의 표준을 제공하며
AI(L/Claude/GPT)와 사람이 함께 일할 때 **일관성 있는 코드 품질**을 유지하는 기반이 된다.
