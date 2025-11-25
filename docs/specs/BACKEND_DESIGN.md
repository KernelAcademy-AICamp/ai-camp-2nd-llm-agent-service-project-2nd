
### *FastAPI 기반 Backend 아키텍처 & 내부 구조 설계서*

**버전:** v2.0
**작성일:** 2025-11-18
**작성자:** Team H(H)
**참고 문서:**

* `PRD.md`
* `ARCHITECTURE.md`
* `AI_PIPELINE_DESIGN.md`

---

# 📌 0. 문서 목적

이 문서는 **LEH Backend(FastAPI)**의 전체적인 기술 구조, API 설계 원칙, DB 스키마, 서비스 레이어, 인증 방식, S3 Presigned URL 정책, AI Worker 연동 방식을 기술한다.

Backend 개발자(H)가 **전체 서버를 구현할 때 절대적인 기준(Single Source of Truth)**이 된다.

---

# 🧭 1. Backend 전체 구조

LEH 백엔드는 **FastAPI 기반의 Stateless API 서버**로 구성되며, 주요 책임은 다음 5가지다:

1. **인증/인가 (JWT)**
2. **사건/유저/멤버십 관리 (RDS PostgreSQL)**
3. **증거 업로드 관리 (S3 Presigned URL)**
4. **증거 분석 결과 조회 (DynamoDB / OpenSearch 조합)**
5. **Draft Preview 생성 API (GPT-4o + 사건별 RAG)**

---

# 🗂 2. 디렉토리 구조

PDF 기반 초기 설계를 최신 구조로 재정리하였다.

backend/
├── app/
│   ├── main.py                  # FastAPI 엔트리포인트
│   ├── core/
│   │   ├── config.py            # 환경변수, 설정
│   │   ├── security.py          # JWT, 패스워드 해싱
│   │   └── logging.py           # 구조화 로그 설정
│   ├── db/
│   │   ├── session.py           # DB 연결(RDS)
│   │   ├── models.py            # SQLAlchemy 모델
│   │   └── schemas.py           # Pydantic 스키마
│   ├── api/
│   │   ├── auth.py              # 로그인/회원 API
│   │   ├── cases.py             # 사건 CRUD
│   │   ├── evidence.py          # Presigned URL / 조회
│   │   ├── draft.py             # Draft Preview API
│   │   └── search.py            # 사건 RAG 검색 API [미구현]
│   ├── services/
│   │   ├── case_service.py      # 사건 관련 비즈니스 로직
│   │   ├── evidence_service.py  # S3 연동 및 Dynamo 조회
│   │   ├── draft_service.py     # Draft 생성(LLM 호출)
│   │   └── search_service.py    # OpenSearch 쿼리 [미구현]
│   ├── utils/
│   │   ├── s3.py                # Presigned URL 생성기
│   │   ├── dynamo.py            # DynamoDB Helper
│   │   ├── opensearch.py        # OS Helper
│   │   └── time.py              # 공통 시간/타임존 처리
│   └── middleware/
│       ├── auth_middleware.py   # JWT 인증 미들웨어
│       ├── audit.py             # 감사 로그 기록기
│       └── error_handler.py     # 공통 에러 핸들러
└── requirements.txt

---

# 🔐 3. 인증/보안 설계 (JWT)

## 3.1 JWT 구조

json
{
  "sub": "<user_id>",
  "role": "lawyer | staff | admin",
  "exp": "<만료시간>",
  "case_access": ["case_123", "case_456"]
}

* Access Token TTL: 24h
* Refresh Token TTL: 7 days
* Role + 사건별 접근권한(case_members)에 따라 접근 제한

## 3.2 Password Hashing

* bcrypt + salt
* PDF 설계가 권장한 방식과 동일 (FastAPI 표준 방식)
* 비밀번호는 절대 복호화 불가

## 3.3 API 보호 정책

* 모든 API는 **HTTPS + Bearer JWT** 필수
* 내부 worker와의 통신은 API를 통하지 않음 (Dynamo 직접 업데이트)

---

# 🧱 4. 데이터베이스 설계 (RDS PostgreSQL)

백엔드는 정형 데이터만 저장한다.

## 4.1 테이블 구조

### `users`

| column          | type      | note               |
| --------------- | --------- | ------------------ |
| id              | uuid      | PK                 |
| email           | text      | unique             |
| hashed_password | text      |                    |
| name            | text      |                    |
| role            | enum      | lawyer/staff/admin |
| created_at      | timestamp |                    |

---

### `cases`

| column      | type      | note          |
| ----------- | --------- | ------------- |
| id          | uuid      | PK            |
| title       | text      | 사건명           |
| description | text      |               |
| status      | enum      | active/closed |
| created_by  | uuid      | FK users.id   |
| created_at  | timestamp |               |

---

### `case_members`

| column  | type | note                |
| ------- | ---- | ------------------- |
| case_id | uuid | FK                  |
| user_id | uuid | FK                  |
| role    | enum | owner/member/viewer |

> 사건 접근 제어 권한의 근거 테이블.

---

### `audit_logs`

| column    | type      | note                                 |
| --------- | --------- | ------------------------------------ |
| id        | uuid      |                                      |
| user_id   | uuid      |                                      |
| action    | text      | e.g., “VIEW_EVIDENCE”, “CREATE_CASE” |
| object_id | text      | evidence_id or case_id               |
| timestamp | timestamp |                                      |

---

# 🗄 5. 비정형 데이터 저장 — DynamoDB 설계

> Paralegal PDF 설계에서 “증거 메타데이터 분리”가 제안된 내용을 LEH에서 DynamoDB로 확장했다.

### DynamoDB 구조

* **PK**: `case_id`
* **SK**: `evidence_id`
* JSON payload 전체 저장

### Evidence JSON 예시

json
{
  "case_id": "case_123",
  "evidence_id": "ev_001",
  "type": "image",
  "timestamp": "2024-12-25T10:20:00Z",
  "speaker": "피고",
  "labels": ["폭언"],
  "ai_summary": "피고가 고성을 지르는 장면.",
  "insights": ["감정적 폭발"],
  "content": "...OCR/STT 전문...",
  "s3_key": "cases/123/raw/img01.jpg",
  "opensearch_id": "case_123_ev_1"
}

---

# 🔍 6. OpenSearch 스키마

각 사건별 index 생성:

case_rag_{case_id}

문서 구조:

json
{
  "id": "case_123_ev_1",
  "content": "OCR/STT/텍스트 전문",
  "labels": ["폭언"],
  "timestamp": "2024-12-25T10:20:00Z",
  "speaker": "피고",
  "vector": [ ...embedding_vector ]
}

---

# 📡 7. 증거 업로드 프로세스 (Presigned URL)

> 기존 Paralegal 시스템은 “API 서버로 파일 전달 → S3 저장” 구조였으나, LEH에서는 성능·비용을 위해 Presigned URL 방식으로 전환한다.

## 7.1 요청 Flow

1. FE → BE: 파일 메타정보 전달
2. BE → FE: S3 Presigned URL 발급
3. FE → S3: 파일 업로드
4. S3 Event 발생
5. AI Worker가 처리 시작

## 7.2 Presigned URL API Spec

GET /evidence/presigned-url?case_id=xxx&filename=xxx

응답 예시:

json
{
  "upload_url": "https://s3...signed_url",
  "file_key": "cases/<case_id>/raw/<uuid>_<filename>"
}

---

# 🤖 8. Evidence 조회 프로세스

백엔드는 직접 파일을 분석하지 않고, **AI Worker가 업데이트한 결과(Dynamo + OpenSearch)**를 조회하여 FE에 전달한다.

## 8.1 Evidence List API

GET /cases/{id}/evidence

서버 동작:

* DynamoDB에서 `case_id`로 모든 evidence 조회
* timestamp 기준 정렬
* summary, labels, speaker, type 등 FE에 전달

---

# 📄 9. Draft Preview API 설계

PDF Paralegal 문서의 Draft 생성 기능을 **사건별 RAG 기반**으로 고도화했다.

## 9.1 API

POST /cases/{id}/draft-preview

요청:

json
{
  "sections": ["청구취지", "청구원인"]
}

응답:

json
{
  "draft_text": "...GPT가 생성한 초안...",
  "citations": [
    {
      "evidence_id": "ev_001",
      "quote": "..."
    }
  ]
}

## 9.2 Draft 생성 Flow

1. BE: 사건 정보 조회
2. BE: DynamoDB에서 증거 목록 Fetch
3. BE: 증거 요약/내용 기반으로 OpenSearch 쿼리 → 관련 문장 검색
4. BE → GPT-4o: 생성 요청 (증거 인용 포함)
5. GPT 응답 → FE에 전달
6. FE는 Preview만 제공 (자동 입력 없음)

---

# 🧩 10. 서비스 레이어 상세

## 10.1 `case_service.py`

* 사건 CRUD
* 멤버 추가/제거
* 사건 상태 변경(active → closed)
* 사건 삭제 시:

  * OpenSearch index 삭제
  * DynamoDB soft-delete

---

## 10.2 `evidence_service.py`

* Presigned URL 생성
* DynamoDB 조회
* S3 key 관리
* 사건별 증거 통계 집계(필터링)

---

## 10.3 `draft_service.py`

* RAG 검색 (OpenSearch)
* GPT-4o Prompt 생성
* 증거 인용문 구조화
* Draft 텍스트 생성
* (선택) docx 변환 모듈 호출

---

## 10.4 `search_service.py`

* OpenSearch query builder
* 라벨/날짜/화자 기반 필터 적용
* 사건 단위 Top-K 검색

---

# 🧱 11. 미들웨어

## 11.1 JWT 인증 미들웨어

* Authorization Header 검증
* Token decode → User Context 주입
* 권한 체크(사건 접근 여부)

## 11.2 Audit Log 미들웨어

* 요청 시: user_id, endpoint, method 기록
* 응답 시: status_code 기록
* DB에 비동기 저장

## 11.3 에러 핸들러

* ValidationError → 422
* AuthenticationError → 401
* PermissionError → 403
* 내부 오류 → 500 + unique error_id 반환

---

# 📦 12. 배포·환경 변수

## 12.1 환경 변수(.env)

DB_URL=postgres://...
AWS_REGION=ap-northeast-2
S3_BUCKET=leh-evidence
DYNAMODB_TABLE=evidence_table
OPENSEARCH_ENDPOINT=...
OPENAI_API_KEY=...
JWT_SECRET=...

## 12.2 런타임

* FastAPI + Uvicorn
* AWS Lambda or ECS/Fargate
* DB 연결 풀링 주의
* cold start 대비 → Lambda use-case 시 별도 최적화

---

# 🧪 13. 테스트 전략

* pytest 기반 단위 테스트
* mock S3/DynamoDB(OpenSearch는 로컬 테스트)
* integration test: Presigned URL → S3 → Worker → Evidence 조회 흐름

---

# 🔚 END OF BACKEND_DESIGN.md
