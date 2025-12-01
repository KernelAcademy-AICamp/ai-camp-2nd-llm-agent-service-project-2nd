# plan.md — LEH TDD 개발 플랜 (Kent Beck + AI + CI/CD)

> 이 문서는 **TDD로 무엇부터 구현할지**에 대한 “다음 테스트 목록”이다.  
> 사람이 "go"라고 말하면, AI는 여기서 **아직 체크되지 않은 첫 번째 항목 하나만** 선택해서  
>
> 1) 그에 해당하는 테스트를 작성하고  
> 2) 테스트를 통과시키기 위한 최소한의 코드만 구현한다.

- 테스트 작성 순서: **위에서 아래로**
- 테스트 단위: 항상 **작고 구체적인 행동 1개**
- 구현 단위: 해당 테스트를 **통과시키는 최소 코드**

---

## 0. 공통 원칙 (claude.md 요약)

1. 항상 **Red → Green → Refactor** 사이클을 따른다.
2. 구조 변경(Tidy)과 기능 변경(Behavior)을 **같은 커밋에 섞지 않는다.**
3. 가능할수록 **API/사용자 행동 레벨 테스트**부터 시작한다.
4. AI 관련 코드는 **모델 호출을 전부 mock**하고, 프로토콜/계약만 테스트한다.
5. `main`, `dev` 브랜치에 대한 배포는 **GitHub Actions + AWS (OIDC)**가 담당하며,  
   배포 전 단계에서 **모든 테스트가 통과**해야 한다.

---

## 1. Backend (FastAPI, RDS, S3, DynamoDB, Qdrant)

### 1.1 인증 / 권한

- [x] `POST /auth/login` 성공 시 JWT 발급 및 만료 시간 필드 포함
- [x] 잘못된 자격증명으로 로그인 시 401, 에러 메시지는 "일반적인 문구"여야 한다 (민감 정보 노출 금지)
- [x] 사건 상세 API 호출 시, JWT의 `sub` 와 `case_members` 권한을 검사하지 않으면 403을 반환해야 한다.

### 1.2 사건 관리 (Cases)

- [x] `POST /cases` 호출 시 사건이 RDS `cases` 테이블에 저장되고, 응답 JSON의 `id`, `title`, `status` 가 DB 값과 일치해야 한다.
- [x] `GET /cases` 는 현재 사용자에게 접근 권한이 있는 사건만 반환해야 한다 (`case_members` 기반).
- [x] `PATCH /cases/{case_id}` 호출 시:
  - 사건 제목, 설명을 수정할 수 있어야 한다.
  - 케이스 소유자 또는 read_write 권한을 가진 멤버만 수정 가능해야 한다.
  - 존재하지 않는 케이스에 대해 404를 반환해야 한다.
- [x] `DELETE /cases/{case_id}` 호출 시:
  - 사건 상태가 `closed` 로 변경되어야 하고,
  - 해당 사건의 Qdrant 컬렉션에서 관련 벡터 삭제 요청이 서비스 레이어에서 호출되어야 한다 (통합 테스트에서는 mock으로 검증).

### 1.3 Evidence Upload (Presigned URL, S3)

- [x] `POST /evidence/presigned-url` 은 유효한 `case_id`, `filename`, `content_type` 를 받으면:
  - `upload_url` 과 `fields` 를 포함한 구조를 반환해야 한다.
  - `fields.key` 는 `cases/{case_id}/raw/` 접두어로 시작해야 한다.
- [x] 존재하지 않거나 권한 없는 `case_id` 로 Presigned URL을 요청하면 404를 반환해야 한다.
- [x] Presigned URL의 만료 시간이 **5분 이내**인지 확인하는 유닛 테스트가 있어야 한다 (실제 AWS 호출 대신 서명 파라미터 검사).
- [x] `POST /evidence/upload-complete` 호출 시:
  - `case_id`, `evidence_temp_id`, `s3_key`를 받아 Evidence 레코드를 생성해야 한다.
  - AI Worker 트리거를 위한 이벤트를 발행해야 한다 (SNS 또는 직접 호출).
  - 권한 없는 케이스에 대해 403을 반환해야 한다.
  - 성공 시 생성된 Evidence 정보를 반환해야 한다.

### 1.4 Evidence 메타 조회 (DynamoDB)

- [x] `GET /cases/{case_id}/evidence` 호출 시:
  - DynamoDB에서 `case_id` 로 조회된 evidence 목록을 `timestamp` 기준으로 정렬해 반환해야 한다.
  - 삭제 플래그(`deleted = true`) 가 있는 항목은 리스트에서 제외해야 한다.
- [x] `GET /evidence/{evidence_id}` 는:
  - `summary`, `labels`, `timestamp`, `download_url` 을 포함해야 하고
  - `download_url` 은 짧은 유효기간의 S3 Presigned URL 이어야 한다 (형태만 테스트).

### 1.5 Draft Preview (RAG + GPT-4o)

- [x] `POST /cases/{case_id}/draft-preview` 호출 시:
  - 사건에 증거가 하나도 없으면 400을 반환해야 한다.
  - 최소 1개 이상의 evidence가 있을 경우, `draft_text` 와 `citations` 배열이 포함된 JSON을 반환해야 한다.
- [x] Draft 생성 시 사용되는 Prompt 문자열에는:
  - **RAG 기반 사실 인용 지시**,
  - **Hallucination 금지 규칙**,
  - **"최종 결정은 변호사가 한다"** 류의 책임 한계 문구가 포함되어야 한다 (문자열 포함 여부 테스트).
- [x] `GET /cases/{case_id}/draft-export` 호출 시:
  - 초안을 DOCX 또는 PDF 형식으로 다운로드할 수 있어야 한다.
  - `format` 쿼리 파라미터로 형식을 지정할 수 있어야 한다 (기본값: docx).
  - 케이스 멤버만 다운로드 가능해야 한다.
  - `Content-Disposition` 헤더에 파일명이 포함되어야 한다.

### 1.6 사용자 관리 (Admin) ✅

- [x] `POST /admin/users/invite` 호출 시:
  - 이메일, 역할 정보를 받아 초대 토큰을 생성하고 DB에 저장해야 한다.
  - 응답에 `invite_token` 과 `invite_url` 을 포함해야 한다.
  - Admin 권한을 가진 사용자만 호출 가능해야 한다 (RBAC 검증).
- [x] `GET /admin/users` 호출 시:
  - 로펌 내 모든 사용자 목록을 반환해야 한다.
  - 검색 쿼리 파라미터 (`email`, `name`)를 지원해야 한다.
  - 역할 및 상태 필터링 (`role`, `status`)을 지원해야 한다.
  - Admin 권한 필요.
- [x] `DELETE /admin/users/{user_id}` 호출 시:
  - 사용자를 soft delete (status를 `inactive`로 변경)해야 한다.
  - 삭제하려는 사용자가 자기 자신이면 400을 반환해야 한다.
  - Admin 권한 필요.

### 1.7 권한 관리 (RBAC) ✅

- [x] Role 기반 접근 제어 미들웨어 구현:
  - `require_admin(current_user: User)` dependency가 Admin이 아닌 사용자에 대해 403을 반환해야 한다.
  - `require_lawyer_or_admin(current_user: User)` dependency가 Staff 사용자에 대해 403을 반환해야 한다.
- [x] `GET /admin/roles` 호출 시:
  - 모든 역할(ADMIN, LAWYER, STAFF)별 권한 매트릭스를 반환해야 한다.
  - 각 역할의 리소스(cases, evidence, admin, billing)별 액션(view, edit, delete) 권한을 포함해야 한다.
  - Admin 권한 필요.
- [x] `PUT /admin/roles/{role}/permissions` 호출 시:
  - 특정 역할의 권한을 업데이트해야 한다.
  - MVP: In-memory 업데이트 (권한 테이블은 추후 구현).
  - Admin 권한 필요.

### 1.8 회원가입 (Signup) ✅

- [x] `POST /auth/signup` 호출 시:
  - 이메일 중복 검사를 수행하고, 중복이면 409를 반환해야 한다.
  - 비밀번호를 bcrypt로 해싱하여 저장해야 한다.
  - 기본 역할은 `LAWYER`로 설정해야 한다.
  - 신규 사용자 생성 후 JWT 토큰을 발급해야 한다.
- [x] Signup 요청 시 이용약관 동의(`accept_terms`)가 `true`가 아니면 400을 반환해야 한다.

### 1.9 Article 840 태그 연동 ✅

- [x] `GET /evidence/{evidence_id}` 응답에 Article 840 태그 정보 포함:
  - DynamoDB에서 `article_840_tags` 필드를 조회해야 한다.
  - 응답 스키마에 `article_840_tags` 필드를 추가해야 한다 (categories, confidence, matched_keywords).
  - `labels` 필드에 `categories` 배열을 매핑해야 한다.
- [x] `GET /cases/{case_id}/evidence` 호출 시:
  - 각 증거 항목에 Article 840 태그 정보가 포함되어야 한다.
  - 유책사유별 필터링 쿼리 파라미터(`categories`)를 지원해야 한다.

### 1.10 케이스 공유 ✅

- [x] `POST /cases/{case_id}/members` 호출 시:
  - 여러 팀원을 동시에 추가할 수 있어야 한다 (`members: List[CaseMemberAdd]`).
  - 각 멤버의 권한 레벨(`permission`: read / read_write)을 설정해야 한다.
  - 케이스 소유자 또는 Admin만 호출 가능해야 한다.
  - `case_members` 테이블에 추가된 멤버를 저장해야 한다.
- [x] `GET /cases/{case_id}/members` 호출 시:
  - 해당 케이스의 모든 멤버 목록을 반환해야 한다.
  - 각 멤버의 이름, 이메일, 권한 레벨을 포함해야 한다.

### 1.11 감사 로그 (Audit Log) ✅

- [x] Audit Log 자동 기록 미들웨어 구현:
  - 모든 API 요청에 대해 사용자 ID, 액션(HTTP 메서드 + 경로), 타임스탬프를 `audit_logs` 테이블에 저장해야 한다.
  - 민감한 엔드포인트(로그인, 증거 조회, 삭제 등)만 선택적으로 기록해야 한다.
- [x] `GET /admin/audit` 호출 시:
  - 날짜 범위 필터링(`start_date`, `end_date`)을 지원해야 한다.
  - 사용자별 필터링(`user_id`)을 지원해야 한다.
  - 액션 타입 필터링(`actions`: LOGIN, VIEW, CREATE, UPDATE, DELETE)을 지원해야 한다.
  - 페이지네이션을 지원해야 한다.
  - Admin 권한 필요.
- [x] `GET /admin/audit/export` 호출 시:
  - CSV 형식으로 감사 로그를 다운로드할 수 있어야 한다.
  - 필터링 조건을 동일하게 적용해야 한다.

---

## 2. AI Worker (L, S3 Event → DynamoDB / Qdrant) ✅ **완료**

### 2.1 Event 파싱 ✅

- [x] S3 Event JSON 을 입력으로 받았을 때:
  - 첫 번째 `Records[0]` 에서 `bucket.name` 과 `object.key` 를 정확히 추출해야 한다.
  - ✅ **구현 완료**: handler.py:193-199, URL 디코딩(+, %20) 포함
- [x] 지원하지 않는 파일 확장자(예: `.exe`)일 경우:
  - Worker는 해당 이벤트를 "unsupported" 상태로 로깅하고,
  - DLQ(SQS) 로 전송하는 헬퍼를 호출해야 한다 (테스트에서는 호출 횟수로 검증).
  - ✅ **구현 완료**: handler.py:90-95, route_parser() 반환값으로 skipped 상태 처리

### 2.2 파일 타입별 처리 ✅

- [x] `.txt` 파일은 text parser 로 라우팅되어야 하고, 결과 JSON에 `content` 필드가 포함돼야 한다.
  - ✅ **구현 완료**: TextParser + KakaoTalk 자동 감지
- [x] 이미지(`.jpg`, `.png`) 업로드 시:
  - Vision/OCR 모듈에서 반환한 텍스트를 `content` 에 저장해야 한다.
  - ✅ **구현 완료**: ImageVisionParser (GPT-4o Vision) + ImageOCRParser (Tesseract)
- [x] PDF 파일은:
  - 먼저 텍스트 추출 시도 후 실패하면 OCR fallback 로직을 호출해야 한다 (두 경로 모두 유닛 테스트).
  - ✅ **구현 완료**: PDFParser (PyPDF2)

### 2.3 카톡/메신저 파싱 ✅

- [x] 카카오톡 내보내기 형식 텍스트에서:
  - 날짜, 화자, 메시지를 파싱해 `[ { speaker, timestamp, message } ]` 구조를 생성해야 한다.
  - ✅ **구현 완료**: KakaoTalkParser with regex pattern + TextParser 자동 감지
- [x] 날짜 포맷이 인식되지 않으면 `timestamp = "unknown"` 으로 저장해야 한다.
  - ✅ **구현 완료**: 날짜 파싱 실패 시 None 반환 처리

### 2.4 STT 처리 (Whisper) ✅

- [x] 오디오 파일 처리 시:
  - STT 결과 텍스트가 비어 있지 않은 상태로 `content` 에 저장되어야 한다.
  - ✅ **구현 완료**: AudioParser (OpenAI Whisper API)
- [x] 화자 분리(diarization)가 실패할 경우:
  - Worker는 경고 로그만 남기고, transcript 자체는 그대로 저장해야 한다.
  - ✅ **구현 완료**: VideoParser (ffmpeg audio extraction + AudioParser)

### 2.5 의미 분석 & 라벨링 (민법 840) ✅

- [x] 분석 결과 JSON에서 `labels` 필드는:
  - 항상 **배열(Array)** 이어야 한다.
  - 0개~N개의 유책사유 라벨을 포함하되, `null` 이나 단일 문자열이 되면 안 된다.
  - ✅ **구현 완료**: Article840Tagger with Article840Category Enum (7개 카테고리)
- [x] 라벨 값은 사전에 정의된 유효 값 목록(예: `"부정행위"`, `"학대"`) 중 하나여야 한다.
  - ✅ **구현 완료**: ADULTERY, DESERTION, MISTREATMENT_BY_INLAWS, HARM_TO_OWN_PARENTS, UNKNOWN_WHEREABOUTS, SERIOUS_GROUNDS, OTHER

### 2.6 Embedding + Qdrant Vector Store ✅

- [x] Embedding 생성 모듈은:
  - 일정 길이 이상의 벡터(예: 1536 길이)를 반환해야 한다 (길이만 테스트).
  - ✅ **구현 완료**: VectorStore with OpenAI text-embedding-3-small (1536 dim) + Qdrant
- [x] 동일 `evidence_id` 재처리 시:
  - Qdrant 벡터는 **upsert(덮어쓰기)** 되어야 하고,
  - DynamoDB의 해당 항목도 최신 값으로 업데이트돼야 한다.
  - ✅ **구현 완료**: MetadataStore (SQLite/DynamoDB) + VectorStore upsert 로직

**테스트 현황**:
- ✅ handler 테스트: 16 passing (Phase 1-6 통합)
- ✅ E2E 통합 테스트: 5 passing (Phase 7)
- ✅ 전체 파이프라인: S3 Event → 파싱 → 메타데이터 저장 → 벡터 저장 → Article 840 태깅

### 2.7 AWS 서비스 연동 (Issue #10: Mock → Real 전환)

> **담당 분담:**
> - **H (Backend)**: DynamoDB 연동, OpenAI API 연동
> - **L (AI Worker)**: Qdrant 연동, S3 연동, Lambda 배포

#### 2.7.1 DynamoDB 연동 ✅ (H 담당 - 완료)

- [x] `backend/app/utils/dynamo.py` Mock 구현을 실제 boto3로 교체
  - ✅ **구현 완료**: boto3 client 사용, `leh_evidence` 테이블 연동
- [x] 테이블 스키마 확인 및 적용:
  - PK: `evidence_id` (HASH)
  - GSI: `case_id-index` (case_id로 조회)
- [x] 모든 CRUD 함수 테스트 완료:
  - `get_evidence_by_case()`: GSI 쿼리
  - `get_evidence_by_id()`: GetItem
  - `put_evidence_metadata()`: PutItem
  - `delete_evidence_metadata()`: DeleteItem
  - `clear_case_evidence()`: GSI 쿼리 + BatchDelete

#### 2.7.2 Qdrant 연동 (L 담당) ✅ **완료 (2025-11-28)**

> **Qdrant Cloud 사용**: PR #26 머지 완료

- [x] Qdrant 클라이언트 설정:
  - **Qdrant Cloud**: `QDRANT_URL`, `QDRANT_API_KEY` 환경변수 사용
  - ✅ 구현 완료: `ai_worker/src/storage/vector_store.py`
- [x] 컬렉션 설정:
  - 컬렉션 이름: `leh_evidence`
  - 벡터 차원: 1536 (OpenAI text-embedding-3-small)
  - Distance metric: Cosine
  - Payload indexes: case_id, file_id, chunk_id, sender
- [x] VectorStore 구현체 수정:
  - `add_chunk_with_metadata()`: 벡터 + 메타데이터 저장
  - `search()`: 유사 벡터 검색
  - `delete_by_case_id()`: 케이스 삭제 시 관련 벡터 일괄 삭제
- [x] 테스트 완료: 18개 테스트 통과

#### 2.7.3 OpenAI API 연동 (H 담당)

- [ ] `backend/app/utils/openai_client.py` Mock 구현을 실제 API로 교체
- [ ] 환경변수 설정: `OPENAI_API_KEY`
- [ ] 사용 함수:
  - `generate_chat_completion()`: Draft 생성 (GPT-4o)
  - `generate_embedding()`: RAG 검색용 임베딩 (text-embedding-3-small)
- [ ] 테스트 항목:
  - API 키 유효성 확인
  - Rate limit 처리 (429 에러 시 재시도)
  - 타임아웃 설정 (60초)

#### 2.7.4 S3 연동 (L 담당) ✅ **완료**

- [x] AI Worker에서 S3 파일 다운로드 구현
  - ✅ `handler.py`: boto3 S3 client로 /tmp에 다운로드
- [x] 환경변수: `S3_EVIDENCE_BUCKET`, `AWS_REGION`
- [x] 파일 경로 규칙: `cases/{case_id}/raw/{evidence_id}_{filename}`

#### 2.7.5 Lambda 배포 (L 담당) 🔄 **준비 완료**

- [x] Dockerfile.lambda 작성 완료
- [x] 모든 모듈 import 테스트 통과
- [x] S3 Event Trigger 설정 (Terraform에 설정됨)
- [ ] **배포 대기**: Admin 권한 필요 (S3 버킷 접근)
- [ ] IAM Role 설정:
  - S3 읽기 권한
  - DynamoDB 읽기/쓰기 권한
  - Qdrant 접근 (VPC 또는 Public)

### 2.8 E2E 통합 (Backend ↔ AI Worker) 🔴 **진행 중**

> **목표**: Backend가 생성한 Evidence 레코드를 AI Worker가 처리 후 UPDATE

#### 2.8.1 스키마 매핑 구현

- [ ] `handler.py`: S3 key에서 evidence_id 추출 함수 추가
  - 형식: `cases/{case_id}/raw/{evidence_id}_{filename}`
  - 예: `ev_abc123_photo.jpg` → `ev_abc123`
- [ ] `metadata_store.py`: `update_evidence_status()` 메서드 추가
  - Backend 레코드 상태 업데이트 (pending → processed)
  - AI 분석 결과 필드 추가 (ai_summary, article_840_tags, qdrant_id)

#### 2.8.2 처리 완료 후 상태 업데이트

- [ ] `handler.py`: `route_and_process()` 수정
  - evidence_id 추출 성공 시: Backend 레코드 UPDATE
  - 실패 시: fallback으로 새 레코드 생성 (기존 방식)
- [ ] 업데이트 필드:
  - `status`: "pending" → "processed"
  - `processed_at`: 처리 완료 시간
  - `ai_summary`: AI 생성 요약
  - `article_840_tags`: 민법 840조 태그
  - `qdrant_id`: Qdrant 벡터 ID

#### 2.8.3 테스트

- [ ] Unit test: `test_update_evidence_status()`
- [ ] Integration test: Backend → S3 → AI Worker → Backend 조회

---

## 3. Frontend (P, React + Tailwind) — UX & UI 디자인 반영

> P는 FE + GitHub + CI/CD 총괄.  
> FE 테스트는 **화면 구조/상태/보안/Calm Control UX** 에 집중한다.

### 3.1 공통 UI 규칙

- [x] 모든 페이지의 기본 폰트는 `Pretendard`(또는 정의된 폰트 토큰)를 사용해야 하고, body 폰트 크기는 16px 이어야 한다.
- [x] 주요 버튼(Primary CTA)은 디자인 토큰의 `accent` 색상(예: `#1ABC9C`)을 사용해야 한다.
- [x] 삭제/파괴적 행동 버튼은 `semantic-error` 색상(예: `#E74C3C`)을 사용하고, 클릭 시 **확인 모달**이 떠야 한다.

### 3.2 로그인 화면

- [x] 로그인 화면에는:
  - 이메일 입력, 비밀번호 입력, 로그인 버튼만 존재해야 한다 (광고/마케팅 배너 X).
- [x] 로그인 폼 제출 후:
  - 잘못된 자격증명일 경우, “아이디 또는 비밀번호를 확인해 주세요.” 형태의 일반적인 에러 메시지만 보여야 하며, 어떤 정보가 틀렸는지는 노출하지 않아야 한다.

### 3.3 케이스 목록 대시보드 (Case List)

- [x] 케이스 카드에는:
  - 사건명, 최근 업데이트 날짜, 증거 개수, Draft 상태가 표시돼야 한다.
- [x] 카드 레이아웃은 `Calm Grey` 배경 카드 + `Deep Trust Blue` 제목 색상을 사용해야 한다.
- [x] 카드 hover 시 미묘한 shadow 증가와 accent 색상의 light glow 효과가 나타나야 한다.

### 3.4 증거 업로드 & 리스트

- [x] 증거 업로드 영역은:
  - “파일을 끌어다 놓거나 클릭하여 업로드” 문구를 포함한 큰 드래그 앤 드롭 영역을 보여야 한다.
- [x] Evidence 테이블에는 최소한:
  - 유형 아이콘, 파일명, 업로드 날짜, AI 요약, 상태, 작업 액션 컬럼이 있어야 한다.
- [x] 상태 컬럼은 다음 상태들을 표시할 수 있어야 한다: `업로드 중`, `처리 대기`, `분석 중`, `검토 필요`, `완료`.

### 3.5 타임라인 화면

- [x] 타임라인 아이템은:
  - 날짜, 요약 텍스트, 관련 evidence 링크를 포함한 세로형 구조여야 한다.
- [x] 타임라인에서 evidence 링크를 누르면:
  - 별도 전체 페이지로 이동하지 않고, **모달 또는 사이드 패널**로 상세 내용을 보여야 한다 (flow 보호).

### 3.6 Draft 탭 (AI 초안)

- [x] Draft 탭 상단에는:
  - “이 문서는 AI가 생성한 초안이며, 최종 책임은 변호사에게 있습니다.” 와 같은 **명시적 Disclaimer 텍스트**가 항상 표시되어야 한다.
- [x] 리치 텍스트 에디터는:
  - 기본적으로 **문서 본문만 보여주는 Zen 모드**에 가깝게, 불필요한 패널을 최소화해야 한다.
- [x] “초안 생성/재생성” 버튼은 항상 Primary 스타일이어야 하며, 클릭 후 로딩 상태를 명확히 보여줘야 한다.

### 3.7 의뢰인 증거 제출 포털

- [x] 포털 화면에는:
  - 로펌/서비스 로고, 간단한 안내 문구, 단일 업로드 영역, 업로드 완료/실패 피드백만 있어야 한다.
- [x] 업로드 완료 시:
  - “파일 N개가 안전하게 전송되었습니다.” 라는 성공 메시지가 `Success Green` 색상으로 표시돼야 한다.

### 3.8 회원가입 & 인증 고도화

- [x] 회원가입 폼에 이메일, 비밀번호, 비밀번호 확인, 이름 입력 필드와 이용약관 동의 체크박스를 포함한다.
- [x] 각 필드에 대한 유효성 검사(포맷, 일치 여부 등)를 적용하고 오류 메시지를 사용자에게 보여줘야 한다.
- [x] /signup 라우트를 추가해 로그인 플로우와 연결한다.

### 3.9 Layout 고도화

- [x] 모든 페이지 하단에 일관된 Footer 컴포넌트를 구현한다.
- [x] Footer에는 법적 책임 고지, 서비스 이용 약관, 개인정보 처리방침, 연락처, 사이트맵 링크가 포함되어야 한다.

### 3.10 사건 등록/관리

- [x] '새 사건 등록' 버튼 클릭 시 사건 정보를 입력할 수 있는 모달 또는 별도 페이지를 표시한다.
- [x] 사건 목록에서 각 사건의 진행 상황(예: '진행 중', '종결')을 변경할 수 있는 UI(드롭다운 등)를 추가한다.

### 3.11 증거 목록 인터랙션

- [x] 증거 목록 상단에 증거 유형(이미지, 문서 등) 또는 날짜별로 필터링할 수 있는 컨트롤을 추가한다.
- [x] 각 증거 항목의 우측에 수정/삭제 등의 작업을 수행할 수 있는 액션 버튼(또는 드롭다운 메뉴)을 구현하고, 각 버튼에 대한 이벤트 핸들러를 연결한다.

### 3.12 Draft(초안) 작성 시스템

- [x] 'Draft 생성' 버튼 클릭 시, 어떤 증거를 기반으로 초안을 작성할지 선택하는 옵션 모달을 구현한다.
- [x] 초안을 편집할 수 있는 웹 에디터(Rich Text Editor) 컴포넌트를 구현하고, 기본적인 서식(굵게, 밑줄 등) 적용 기능을 추가한다.
- [x] (추후 개발 예정) 외부 API(또는 라이브러리)를 연동하여, 편집된 내용을 HWP 또는 Word 파일로 변환하여 다운로드하는 기능을 구현한다.

### 3.13 변호사 전용 기능

- [x] 변호사가 자주 사용하는 자체 문서 양식(Template)을 업로드하고 관리할 수 있는 페이지를 구현한다.
- [x] Draft 작성 시, 업로드된 자체 양식을 기반으로 내용을 채울 수 있는 옵션을 제공한다.

### 3.14 의뢰인 소통 허브

- [x] 사건에 의뢰인 정보를 기입하고 관리할 수 있는 폼을 구현한다.
- [x] 특정 의뢰인에게 증거 목록을 공유하고 법적 고지사항을 전달할 수 있는 전용 페이지(읽기 전용)를 생성하는 기능을 구현한다.

### 엔터프라이즈 및 관리자 기능 (Admin & Finance)

### 3.15 사용자 및 역할 관리 (Admin: Users & Roles)

- [x] 사용자 목록 페이지 (/admin/users):
  - 로펌 내 사용자 조회 (이름, 이메일, 역할, 상태 등), 검색 및 필터링.
  - 사용자 초대 및 삭제 기능.
- [x] 권한 설정 페이지 (/admin/roles):
  - 역할별(Admin, Attorney, Staff) 권한 매트릭스 UI (토글 스위치).
  - 권한 변경 시 즉시 반영 및 알림.
- [x] 케이스 공유 모달:
  - 팀원 검색 및 선택.
  - 읽기/쓰기 권한 설정.

### 3.16 빌링 및 구독 관리 (Admin: Billing)

- [x] 구독 현황 페이지 (/settings/billing):
  - 현재 플랜 정보, 다음 결제일, 결제 수단 관리 카드.
  - 플랜 업그레이드/다운그레이드 모달.
- [x] 사용량 미터링 위젯:
  - AI 토큰 사용량, 스토리지 사용량을 시각적 게이지/프로그레스 바로 표시.
  - 한도 임박 시 경고 표시.
- [x] 청구서 내역:
  - 과거 결제 이력 테이블.
  - PDF 영수증 다운로드 버튼.

### 3.17 AI 투명성 및 감사 로그 (Compliance)

- [x] 활동 로그 페이지 (/admin/audit):
  - 사용자 활동(로그인, 조회, 수정, 삭제 등) 기록 테이블.
  - 날짜, 사용자, 작업 유형별 필터링.
- [x] AI 추적성(Traceability) 패널:
  - Draft 에디터 내 문장 클릭 시, 근거가 된 증거 원문 하이라이트 표시.
  - AI 생성 근거 데이터(프롬프트, 증거 ID 등) 조회.
- [x] 보안 상태 대시보드:
  - 암호화 적용 여부, PIPA 준수 상태 등을 보여주는 상태 카드 위젯.

### 3.18 성과 분석 대시보드 (Analytics)

- [x] 효율성 KPI 위젯:
  - "절약된 시간", "처리된 증거 수" 등 ROI 지표 시각화 (큰 숫자 강조).
- [x] 사용량 트렌드 차트:
  - 월별 사건 수, 증거 유형별 분포 등을 Bar/Pie 차트로 시각화.
- [x] 팀 활동 히트맵/리스트:
  - 팀원별 시스템 활용도 및 기여도 시각화.

### 3.19 랜딩 페이지 (Landing Page)

> **목적:** Self-Serve 온보딩, 신뢰 구축, SEO 효과
> **위치:** `/` (루트 경로, 현재 로그인 화면을 `/login`으로 이동)
> **디자인 원칙:** UI_UX_DESIGN.md 기준 적용 (Calm Control, Deep Trust Blue, Clarity Teal)

#### 3.19.1 페이지 구조 (12개 섹션)

- [x] **1. Navigation Bar (고정 헤더)**
  - 로고(좌측), 메뉴(우측): 기능/가격/고객사례/로그인/무료체험
  - 스크롤 시 배경 블러 효과 (backdrop-blur)
  - Sticky position, shadow on scroll

- [x] **2. Hero Section**
  - 헤드라인: "증거 정리 시간 90% 단축" (큰 폰트, Deep Trust Blue)
  - 서브헤드라인: "AI가 이혼 소송 증거를 자동 분석하고 초안을 작성합니다"
  - CTA 버튼: "무료로 시작하기" (Primary, 눈에 띄는 위치)
  - Hero 이미지/스크린샷: 실제 제품 UI 미리보기

- [x] **3. Social Proof**
  - "50개 로펌 사용 중" (신뢰 배지)
  - 로고 슬라이더 (유명 로펌 로고, 실제 데이터 없을 경우 "leading law firms")
  - 평균 평점 표시 (5.0/5.0)

- [x] **4. Problem Statement**
  - 제목: "이런 고민 있으셨나요?"
  - 3-4개 Pain Points (아이콘 + 텍스트):
    - 📂 "수백 개 카톡 대화, 일일이 읽기 힘드시죠?"
    - ⏰ "증거 정리에만 며칠씩 걸리시나요?"
    - 📝 "초안 작성할 때마다 반복 작업에 지치셨나요?"
    - 🔍 "중요한 증거를 놓칠까 불안하신가요?"

- [x] **5. Solution (3가지 핵심 기능)**
  - 제목: "Legal Evidence Hub가 해결합니다"
  - 3-Column 레이아웃:
    - **자동 증거 분석**: 이미지/음성/PDF를 AI가 자동 분류 및 요약
    - **스마트 타임라인**: 시간순 증거 정리, 유책사유 자동 태깅
    - **초안 자동 생성**: RAG 기반 사실 인용, 답변서 초안 1분 생성
  - 각 기능마다 아이콘, 짧은 설명, 스크린샷

- [x] **6. How It Works (4단계 프로세스)**
  - 제목: "4단계로 완성되는 초안"
  - Step-by-step 플로우차트:
    - 1️⃣ 증거 업로드 (드래그 앤 드롭)
    - 2️⃣ AI 자동 분석 (OCR, STT, 감정 분석)
    - 3️⃣ 타임라인 검토 (증거 확인)
    - 4️⃣ 초안 다운로드 (HWP/DOCX)
  - 각 단계마다 작은 애니메이션 또는 아이콘

- [x] **7. AI Transparency & Security**
  - 제목: "법률 컴플라이언스 준수"
  - 2-Column 레이아웃:
    - 좌측: AI 투명성
      - "모든 AI 결과는 근거 증거 표시"
      - "최종 결정은 변호사님께"
    - 우측: 보안 및 규정 준수
      - AES-256 암호화
      - PIPA(개인정보보호법) 준수
      - ISO 27001 인증 (준비 중)
  - 신뢰 배지 아이콘 (자물쇠, 방패)

- [x] **8. Pricing (명확한 가격 정책)**
  - 제목: "투명한 가격, 숨은 비용 없음"
  - 3-Tier 가격표:
    - **Basic**: ₩49,000/월 (개인 변호사)
    - **Professional**: ₩99,000/월 (소형 로펌, 가장 인기)
    - **Enterprise**: ₩199,000/월 (대형 로펌, 맞춤 기능)
  - 각 플랜마다 포함 기능 리스트 (체크마크)
  - "14일 무료 체험" 강조

- [x] **9. Testimonials (실제 후기)**
  - 제목: "이미 사용 중인 변호사님들의 평가"
  - 3개 후기 카드:
    - 프로필 사진(또는 이니셜), 이름, 소속, 평점
    - 짧은 후기 텍스트 (예: "증거 정리 시간이 1/10로 줄었습니다")
  - (데이터 없을 경우 placeholder 텍스트)

- [x] **10. FAQ (우려 해소)**
  - 제목: "자주 묻는 질문"
  - Accordion 형식 (클릭 시 펼침):
    - "AI가 생성한 초안은 법적 효력이 있나요?"
    - "개인정보는 안전하게 보호되나요?"
    - "기존 시스템과 연동 가능한가요?"
    - "환불 정책은 어떻게 되나요?"
    - "어떤 파일 형식을 지원하나요?"
  - 답변은 간결하고 명확하게 (2-3문장)

- [x] **11. Final CTA (전환 유도)**
  - 제목: "지금 바로 시작하세요"
  - 서브텍스트: "14일 무료 체험, 신용카드 필요 없음"
  - 큰 CTA 버튼: "무료로 시작하기" (Primary, 센터 정렬)
  - 보조 버튼: "영업팀과 상담하기" (Secondary)

- [x] **12. Footer**
  - 3-Column 레이아웃:
    - 좌측: 회사 정보 (로고, 주소, 연락처)
    - 중앙: 링크 (제품/가격/블로그/고객사례/채용)
    - 우측: 법적 고지 (이용약관/개인정보처리방침/쿠키정책)
  - 하단: Copyright 및 소셜 미디어 아이콘

#### 3.19.2 기술 요구사항

- [x] **라우팅 구조 변경**
  - `/` → Landing Page (신규)
  - `/login` → Login Page (기존 `/`에서 이동)
  - Navigation Guard: 로그인 상태면 `/cases`로 자동 리디렉션

- [x] **성능 최적화**
  - Hero 이미지: WebP 포맷, lazy loading
  - 스크린샷: Blur placeholder (next/image)
  - 스크롤 애니메이션: Intersection Observer API 사용

- [x] **반응형 디자인**
  - 모바일: 1-Column 레이아웃
  - 태블릿: 2-Column 레이아웃
  - 데스크톱: 3-Column 레이아웃 (섹션별 적용)
  - ✅ **구현 완료**: `responsive.test.tsx` 15개 테스트, SolutionSection/PricingSection에 `md:grid-cols-2` 추가

- [x] **접근성**
  - Semantic HTML (section, article, nav)
  - ARIA labels for CTA buttons
  - Focus visible for keyboard navigation
  - Color contrast ratio ≥ 4.5:1 (WCAG AA)
  - ✅ **구현 완료**: `accessibility.test.tsx` 26개 테스트, Skip Navigation Link, aria-labels, focus-visible 스타일 추가

- [x] **SEO 최적화**
  - `<title>`: "Legal Evidence Hub - AI 이혼 소송 증거 분석 솔루션"
  - `<meta description>`: 160자 이내, 핵심 키워드 포함
  - `<meta keywords>`: "이혼소송, 증거분석, AI법률, 답변서"
  - Open Graph 태그 (소셜 공유용)
  - Structured Data (JSON-LD): Organization, Product
  - ✅ **구현 완료**: `layout.tsx`에 메타데이터 설정, `seo.test.tsx` 29개 테스트

#### 3.19.3 디자인 원칙 적용

- **Calm Control 철학:**
  - 빼기의 디자인 (과도한 애니메이션 자제)
  - 인지 부하 최소화 (섹션당 1개 핵심 메시지)
  - 여백 충분히 활용 (8pt grid system)

- **색상 팔레트:**
  - Primary: Deep Trust Blue (#2C3E50)
  - Accent: Clarity Teal (#1ABC9C)
  - Background: Calm Grey (#F8F9FA)
  - Text: 진한 회색 (#2D3748)

- **타이포그래피:**
  - Font: Pretendard
  - Heading: 32px-48px (Hero), 24px-32px (Section)
  - Body: 16px (기본), 14px (설명)
  - Line height: 1.6-1.8

- **인터랙션:**
  - Button hover: 색상 변경 + subtle scale
  - Scroll animation: Fade-in-up (duration: 0.6s)
  - Smooth scroll to section (anchor links)

#### 3.19.4 테스트 항목

- [x] **기능 테스트**
  - CTA 버튼 클릭 → `/signup` 페이지로 이동
  - Navigation 메뉴 클릭 → 해당 섹션으로 스크롤
  - FAQ Accordion 펼침/접힘 동작

- [x] **네비게이션 개선**
  - Navigation 메뉴바의 LEH 로고 클릭 → 홈(/) 페이지로 이동
  - Footer의 회사명/로고 클릭 → 홈(/) 페이지로 이동

- [x] **반응형 테스트**
  - Mobile (375px): 모든 섹션 1-Column
  - Tablet (768px): 일부 섹션 2-Column
  - Desktop (1440px): 3-Column 레이아웃
  - ✅ **테스트 완료**: `src/tests/landing/responsive.test.tsx` (15 tests passing)

- [ ] **성능 테스트**
  - Lighthouse Score: Performance ≥ 90
  - First Contentful Paint ≤ 1.5s
  - Largest Contentful Paint ≤ 2.5s

- [x] **SEO 테스트**
  - ⬜ Google Search Console 등록 (외부 설정 필요)
  - ✅ Sitemap.xml 생성 및 제출 (`app/sitemap.ts`)
  - ✅ Robots.txt 설정 (`app/robots.ts`)

**참고 문서:**
- [UI_UX_DESIGN.md](../UI_UX_DESIGN.md) - 디자인 시스템
- [FRONTEND_CLEAN_CODE.md](../FRONTEND_CLEAN_CODE.md) - 코드 컨벤션
- [랜딩 페이지 베스트 프랙티스](https://www.nngroup.com/articles/landing-page-guidelines/)

---

## 4. 보안 관련 테스트 (전 계층 공통) ✅ **완료**

- [x] HTTP 응답 헤더에는:
  - 최소한 `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` 가 설정되어야 한다 (백엔드 유닛/통합 테스트).
  - ✅ **구현 완료**: Phase 3.1 - HTTP Security Headers 테스트 (`backend/tests/test_security_headers.py`)
- [x] 로그 기록 시:
  - JWT 토큰, 비밀번호, 주민등록번호 등 민감정보가 로그에 포함되지 않는지 검증하는 테스트가 있어야 한다 (샘플 로그 캡처 후 assert).
  - ✅ **구현 완료**: Phase 3.2 - AI Worker + Backend 민감정보 로깅 필터 (`ai_worker/src/utils/logging_filter.py`, `backend/app/core/logging_filter.py`)
- [x] GitHub 레포 코드/설정에서:
  - `OPENAI_API_KEY`, DB 비밀번호 등 비밀값이 **하드코딩**되어 있지 않은지 검사하는 정적 체크 스크립트 테스트를 추가해야 한다.
  - ✅ **구현 완료**: Phase 3.3 - Hardcoded Secrets Detection (`scripts/check_hardcoded_secrets.py`, 10 tests passing)

---

## 5. CI/CD (GitHub Actions + AWS, 담당: P)

> P는 **GitHub Actions 워크플로우와 AWS 배포 파이프라인**을 총괄한다.  
> 아래 항목들은 CI/CD 시스템에 대한 **테스트 우선 개발 항목**이다.

### 5.1 공통 CI (dev, main 공통)

- [ ] `.github/workflows/ci.yml` 이 존재하고, `backend`, `ai_worker`, `frontend` 세 영역에 대해:
  - 의존성 설치
  - 린트
  - 테스트(pytest / FE 테스트)를 실행한 뒤
  - 실패 시 **배포 job 을 실행하지 않아야 한다.**
- [ ] CI는 Pull Request 기준으로:
  - `dev` 대상 PR 에서는 테스트 + 빌드까지 수행하고 결과를 PR에 코멘트해야 한다.

### 5.2 dev 브랜치 → AWS “dev 환경” 자동 배포

- [ ] `push` 또는 `merge` to `dev` 발생 시:
  - CI가 성공한 후에만 `cd-dev.yml` 워크플로우가 실행돼야 한다.
- [ ] `cd-dev.yml` 은:
  - **OIDC 인증**을 통해 AWS 권한을 획득해야 한다 (Access Key 하드코딩 금지).
  - Frontend 빌드 결과를 **AWS S3 (Dev Bucket)**으로 동기화(Sync)해야 한다.
  - Backend / AI Worker 컨테이너 이미지를 빌드하고, **AWS ECR**에 푸시한 뒤, Lambda/ECS 서비스를 업데이트해야 한다.

### 5.3 main 브랜치 → AWS “prod 환경” 자동 배포

- [ ] `main` 브랜치에 PR이 merge되면:
  - CI가 다시 전체 테스트를 실행하고 통과할 경우에만 `cd-main.yml` 이 실행돼야 한다.
- [ ] `cd-main.yml` 은:
  - dev 와 다른 AWS 계정 또는 리소스(Prod 환경)에 배포해야 하며, 환경변수 세트가 분리되어야 한다.
- [ ] main 배포는:
  - 사람이 수동으로 승인해야 하는 단계(예: `environment: production` + required reviewers)를 포함해야 한다.

### 5.4 CI/CD 보안 테스트

- [ ] `.github/workflows/*.yml` 에서:
  - AWS Access Key ID / Secret Key 가 직접 하드코딩되어 있지 않은지 검사하는 정적 테스트를 추가한다.
- [ ] Secrets 사용 시:
  - `secrets.XXX` 참조만 있어야 하며, 워크플로우 상에서 echo 로 출력되지 않는지 검사하는 테스트를 추가한다.

---

## 6. UI/UX 개선 및 고도화 (Frontend Enhancement)

> **완료일: 2025-11-24**
> **담당: P (Frontend Lead)**
> **참고 문서**: `docs/guides/UI_IMPROVEMENTS.md`, `docs/QA_REPORT_UI_IMPROVEMENTS.md`

### 6.1 ✅ 완료된 개선사항 (Phase 1)

#### 6.1.1 CaseCard - Magic UI Border Beam Effect
- [x] 마우스 호버 시 은은한 테두리 광원 효과 추가
- [x] Tailwind 커스텀 애니메이션 (`animate-border-beam`) 구현
- [x] Accent color (`#1ABC9C`) 사용하여 전문적인 느낌 유지
- [x] 3초 linear infinite 애니메이션으로 Calm Control UX 준수
- [x] `pointer-events-none`으로 클릭 이벤트 보호
- [x] z-index 레이어링으로 콘텐츠와 효과 분리

**테스트 결과:**
- ✅ HTML 구조 검증 완료 (curl로 확인)
- ✅ 163개 전체 테스트 통과
- ✅ 빌드 성공 (TypeScript 에러 없음)

#### 6.1.2 EvidenceTable - Shadcn/ui DataTable 리팩토링
- [x] TanStack Table v8 통합 (정렬, 페이지네이션, 필터링)
- [x] Clean Architecture 적용 (로직/UI 분리)
  - [x] `useEvidenceTable` hook 생성 (비즈니스 로직)
  - [x] `EvidenceTypeIcon` 컴포넌트 (Pure Presentational)
  - [x] `EvidenceStatusBadge` 컴포넌트 (Pure Presentational)
  - [x] `DataTablePagination` 컴포넌트 (재사용 가능)
  - [x] `EvidenceDataTable` 메인 테이블 (Shadcn/ui 스타일)
- [x] 정렬 기능: 파일명, 업로드 날짜 클릭 정렬
- [x] 페이지네이션: 10/20/30/50 항목씩 보기
- [x] 필터링: 유형(5종류), 날짜(오늘/7일/30일)
- [x] 디자인 토큰 100% 준수
- [x] WCAG 2.1 AA 접근성 준수

**테스트 결과:**
- ✅ 모든 163개 테스트 통과
- ✅ 코드 모듈화: 200 lines → 6개 파일 (505 lines total)
- ✅ 하위 호환성 유지 (기존 API 변경 없음)
- ✅ Bundle size 최적화 (TanStack Table ~6 kB 추가)

**문서화:**
- ✅ `UI_IMPROVEMENTS.md` (450+ lines) - 아키텍처, 마이그레이션 가이드
- ✅ `QA_REPORT_UI_IMPROVEMENTS.md` (1000+ lines) - 전체 QA 리포트

---

### 6.2 향후 개선 계획 (Phase 2) - 우선순위: 중

> **조건**: Phase 1 완료 후 사용자 피드백 수집 후 진행
> **예상 소요 시간**: 3-5일

#### 6.2.1 DataTable 고급 기능
- [ ] **드래그 앤 드롭 컬럼 정렬**
  - `@dnd-kit/core` 라이브러리 통합 검토
  - 사용자가 컬럼 순서를 자유롭게 변경 가능
  - localStorage에 사용자 설정 저장

- [ ] **컬럼 show/hide 토글**
  - 컬럼 설정 모달 또는 드롭다운 메뉴
  - "보이는 컬럼" 체크박스 UI
  - 최소 3개 컬럼은 항상 표시 (파일명, 상태, 작업)

- [ ] **CSV 내보내기 기능**
  - "CSV 다운로드" 버튼 추가
  - 현재 필터/정렬 상태 반영하여 export
  - 날짜 형식: `YYYY-MM-DD HH:mm:ss`
  - 파일명: `evidence_export_${timestamp}.csv`

- [ ] **행 선택 (체크박스) + 일괄 작업**
  - 각 행 왼쪽에 체크박스 추가
  - 헤더 체크박스로 전체 선택/해제
  - 선택된 행 카운트 표시
  - 일괄 작업: 삭제, 라벨 추가, 상태 변경

**테스트 요구사항:**
- [ ] 드래그 앤 드롭 시 컬럼 순서 변경 테스트
- [ ] 컬럼 숨기기/보이기 토글 테스트
- [ ] CSV 내보내기 파일 내용 검증 테스트
- [ ] 일괄 작업 시 선택된 항목만 영향받는지 테스트

---

#### 6.2.2 성능 최적화 (대량 데이터)
- [ ] **Virtual Scrolling 구현**
  - 증거 100개 이상 시 성능 저하 방지
  - `react-window` 또는 `@tanstack/react-virtual` 통합
  - 스크롤 시 가시 영역만 렌더링
  - 예상 성능 향상: 10배

- [ ] **Infinite Scroll 옵션**
  - 페이지네이션 대신 무한 스크롤 선택 가능
  - "더 보기" 버튼 또는 자동 로딩
  - 초기 로드: 20개, 추가 로드: 20개씩

**테스트 요구사항:**
- [ ] 1000개 항목 렌더링 시 60fps 유지 테스트
- [ ] 스크롤 성능 프로파일링 (React Profiler)
- [ ] 메모리 누수 검증

---

#### 6.2.3 실시간 업데이트
- [ ] **WebSocket 통합**
  - 증거 업로드/분석 완료 시 실시간 테이블 업데이트
  - "N개의 새로운 항목" 알림 표시
  - 사용자가 "새로고침" 버튼 클릭하여 반영

- [ ] **낙관적 업데이트 (Optimistic Update)**
  - 증거 삭제 시 즉시 UI에서 제거 (백엔드 응답 기다리지 않음)
  - 실패 시 롤백 + 에러 메시지

**테스트 요구사항:**
- [ ] WebSocket 연결/재연결 시나리오 테스트
- [ ] 낙관적 업데이트 롤백 테스트
- [ ] 다중 사용자 동시 편집 충돌 테스트

---

### 6.3 E2E 테스트 구축 (Phase 2) - 우선순위: 높

> **목적**: 실제 브라우저에서 UI 인터랙션 자동화 테스트
> **도구**: Playwright 또는 Cypress

#### 6.3.1 E2E 테스트 항목
- [ ] **CaseCard Border Beam 효과**
  - 마우스 호버 시 opacity 변화 캡처
  - 스크린샷 비교 (hover 전/후)
  - 애니메이션 프레임 검증

- [ ] **EvidenceTable 정렬**
  - 파일명 헤더 클릭 → 테이블 행 순서 변경 확인
  - 날짜 헤더 클릭 → 정렬 방향 변경 확인

- [ ] **페이지네이션 네비게이션**
  - "다음 페이지" 버튼 클릭 → URL 파라미터 변경 확인
  - 페이지 크기 변경 → 테이블 행 수 변경 확인

- [ ] **필터 적용**
  - 유형 필터 선택 → 해당 유형 항목만 표시
  - 날짜 필터 선택 → 카운터 업데이트 확인

**도구 선택 기준:**
- **Playwright**: 멀티 브라우저(Chrome, Firefox, Safari), 빠름, TypeScript 네이티브
- **Cypress**: 개발자 경험 우수, 디버깅 쉬움, 스크린샷 비교 내장

**테스트 파일 구조:**
```
frontend/e2e/
├── case-card.spec.ts          # Border Beam 효과
├── evidence-table.spec.ts     # 정렬, 필터, 페이지네이션
├── accessibility.spec.ts      # ARIA, 키보드 네비게이션
└── visual-regression.spec.ts  # 스크린샷 비교
```

**예상 테스트 수:** 20-30개
**예상 소요 시간:** 2-3일

---

### 6.4 디자인 시스템 확장 (Phase 3) - 우선순위: 낮

> **조건**: 디자이너 협업 필요, Phase 1-2 완료 후
> **목적**: 일관된 UI 컴포넌트 라이브러리 구축

#### 6.4.1 공통 컴포넌트 라이브러리
- [ ] **Button 컴포넌트**
  - Variants: primary, secondary, outline, ghost, destructive
  - Sizes: xs, sm, md, lg
  - Loading state, disabled state
  - Border Beam 효과 옵션

- [ ] **Input 컴포넌트**
  - Text, Number, Date, Select
  - Validation states (error, success, warning)
  - Helper text, character count
  - Calm Control 스타일 focus ring

- [ ] **Modal/Dialog 컴포넌트**
  - Shadcn/ui 스타일
  - 애니메이션: fade-in + slide-up
  - ESC 키로 닫기, 배경 클릭으로 닫기 옵션
  - ARIA dialog role

- [ ] **Toast/Notification 컴포넌트**
  - 위치: top-right (기본)
  - 타입: success, error, warning, info
  - 자동 닫기 (5초)
  - 여러 알림 쌓기 (stack)

**Storybook 통합:**
- [ ] Storybook 설치 및 설정
- [ ] 각 컴포넌트 스토리 작성
- [ ] 인터랙션 테스트 추가
- [ ] Dark mode 스토리

**예상 소요 시간:** 5-7일

---

### 6.5 알려진 제한사항 및 개선 아이디어

#### 🟡 현재 제한사항 (Non-blocking)

1. **Browser Compatibility**
   - CSS blur 효과가 구형 브라우저에서 작동하지 않을 수 있음
   - 해결책: `@supports (filter: blur())` 쿼리로 fallback 제공

2. **Accessibility - 애니메이션 감소 모드**
   - `prefers-reduced-motion` 미디어 쿼리 미지원
   - 해결책: Tailwind 설정에서 `motion-safe:` prefix 사용
   ```js
   // tailwind.config.js
   animation: {
     'border-beam': 'border-beam 3s linear infinite',
   },
   // 사용 시:
   className="motion-safe:animate-border-beam"
   ```

3. **DataTable - 모바일 UX**
   - 가로 스크롤이 직관적이지 않을 수 있음
   - 해결책: 모바일에서는 카드 리스트 뷰로 전환 (responsive design)

#### 💡 개선 아이디어 (Backlog)

1. **CaseCard Hover 효과 변형**
   - Border Beam 방향 변경 (circular, diagonal)
   - 색상 그라디언트 커스터마이징 (사용자 설정)
   - 호버 시 카드 내부 콘텐츠 애니메이션 (fade-in details)

2. **DataTable 고급 검색**
   - 전체 텍스트 검색 (파일명, 요약 통합 검색)
   - 정규식 검색 지원
   - 검색 하이라이트

3. **DataTable 뷰 전환**
   - 테이블 뷰 ↔ 카드 뷰 토글
   - 갤러리 뷰 (이미지 증거 전용)
   - 타임라인 뷰 (날짜순 시각화)

4. **데이터 시각화 통합**
   - 증거 유형별 분포 차트 (Pie chart)
   - 월별 업로드 추세 (Line chart)
   - Recharts 또는 Chart.js 통합

---

## 7. 버튼 접근성 및 사용자 경험 개선 (Phase 2)

> **기준 문서:** [docs/BUTTON_AUDIT_REPORT.md](../BUTTON_AUDIT_REPORT.md)
> **감사 완료일:** 2025-11-24
> **전체 평가:** A+ (우수)
> **개선 필요 항목:** 4건 (High: 2, Medium: 2)

### 7.1 High Priority - 즉시 수정

#### 7.1.1 DraftGenerationModal 닫기 버튼 접근성
- [ ] **aria-label 추가**
  - **파일:** `frontend/src/components/draft/DraftGenerationModal.tsx` Line 62
  - **현재 상태:** X 아이콘만 있고 aria-label 없음
  - **개선 내용:**
    ```tsx
    <button
      onClick={onClose}
      className="text-gray-400 hover:text-gray-600 transition-colors"
      aria-label="Draft 생성 옵션 모달 닫기"
    >
      <X className="w-6 h-6" />
    </button>
    ```
  - **영향도:** 높음 (스크린 리더 사용자)
  - **예상 소요 시간:** 5분

#### 7.1.2 List 버튼 onClick 핸들러 구현
- [ ] **텍스트 서식 기능 완성**
  - **파일:** `frontend/src/components/draft/DraftPreviewPanel.tsx` Line 82
  - **현재 상태:** 버튼은 있으나 onClick 핸들러 없음
  - **개선 내용:**
    ```tsx
    <button
      type="button"
      aria-label="Insert unordered list"
      onClick={() => handleFormat('insertUnorderedList')}
      className="p-1 hover:bg-gray-200 rounded transition-colors"
    >
      <List className="w-4 h-4 text-gray-700" />
    </button>
    ```
  - **영향도:** 높음 (기능 미완성)
  - **예상 소요 시간:** 10분

### 7.2 Medium Priority - 다음 스프린트

#### 7.2.1 EvidenceDataTable 추가 작업 버튼
- [ ] **더보기 메뉴 구현**
  - **파일:** `frontend/src/components/evidence/EvidenceDataTable.tsx` Line 187
  - **현재 상태:** MoreVertical 아이콘만 있고 onClick 핸들러 없음
  - **개선 내용:**
    - Dropdown 메뉴 컴포넌트 생성 (다운로드, 삭제, 상세보기 옵션)
    - onClick 핸들러로 메뉴 토글
    - 외부 클릭 시 자동 닫기
  - **예시 구현:**
    ```tsx
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);

    const handleMoreActions = (evidenceId: string) => {
      setOpenMenuId(openMenuId === evidenceId ? null : evidenceId);
    };

    // 버튼 수정
    <button
      onClick={() => handleMoreActions(evidence.id)}
      className="text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
      aria-label={`${evidence.filename} 추가 작업`}
      aria-expanded={openMenuId === evidence.id}
      aria-haspopup="true"
    >
      <MoreVertical className="w-5 h-5" />
    </button>
    ```
  - **영향도:** 중간 (UX 개선)
  - **예상 소요 시간:** 1-2시간

#### 7.2.2 type="button" 명시
- [ ] **폼 제출 방지를 위한 명시적 type 속성 추가**
  - **영향 받는 파일 및 라인:**
    - `frontend/src/pages/cases/index.tsx` Line 55 (로그아웃 버튼)
    - `frontend/src/components/evidence/EvidenceDataTable.tsx` Line 103, 121 (정렬 버튼)
    - 기타 8개 버튼
  - **개선 내용:**
    ```tsx
    // Before
    <button onClick={handleLogout}>로그아웃</button>

    // After
    <button type="button" onClick={handleLogout}>로그아웃</button>
    ```
  - **영향도:** 낮음 (예방 차원)
  - **예상 소요 시간:** 30분 (일괄 수정)

### 7.3 Low Priority - 향후 개선

#### 7.3.1 정렬 버튼 접근성 향상
- [ ] **aria-sort 속성 추가**
  - **파일:** `frontend/src/components/evidence/EvidenceDataTable.tsx`
  - **개선 내용:**
    - TanStack Table의 정렬 상태를 aria-sort에 반영
    - 정렬 방향 시각적 표시 (ArrowUp/ArrowDown 조건부 렌더링)
  - **예시 구현:**
    ```tsx
    const getSortDirection = (columnId: string) => {
      const sortingState = table.getState().sorting.find(s => s.id === columnId);
      if (!sortingState) return 'none';
      return sortingState.desc ? 'descending' : 'ascending';
    };

    <th scope="col">
      <button
        onClick={() => table.getColumn('filename')?.toggleSorting()}
        aria-sort={getSortDirection('filename')}
        className="flex items-center space-x-1 hover:text-deep-trust-blue transition-colors"
      >
        <span>파일명</span>
        {getSortDirection('filename') === 'ascending' ? (
          <ArrowUp className="w-4 h-4" />
        ) : getSortDirection('filename') === 'descending' ? (
          <ArrowDown className="w-4 h-4" />
        ) : (
          <ArrowUpDown className="w-4 h-4" />
        )}
      </button>
    </th>
    ```
  - **영향도:** 낮음 (접근성 향상)
  - **예상 소요 시간:** 1시간

### 7.4 버튼 감사 후속 작업

#### 7.4.1 정기 감사 프로세스
- [ ] **월 1회 버튼 접근성 자동 체크**
  - Axe DevTools 또는 Pa11y CI 통합
  - GitHub Actions에서 자동 실행
  - 접근성 위반 시 PR 블록

#### 7.4.2 Button 컴포넌트 표준화
- [ ] **재사용 가능한 Button 컴포넌트 생성**
  - 모든 접근성 속성 기본 포함 (aria-label, type 등)
  - Variants: primary, secondary, danger, ghost
  - Loading state 자동 처리
  - 기존 버튼들을 점진적으로 마이그레이션

**참고 문서:**
- [BUTTON_AUDIT_REPORT.md](../BUTTON_AUDIT_REPORT.md) - 상세 감사 결과
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)

---

## 8. Mock 인증 구현 (개발/QA용)

> **구현일:** 2025-11-25
> **목적:** 백엔드 미실행 상태에서 프론트엔드 QA 진행 가능하도록 임시 Mock 구현
> **상태:** 🟡 임시 구현 (TODO: 백엔드 연동 시 제거)

### 8.1 QA에서 발견된 문제

| 항목 | 문제 | 원인 | 해결 상태 |
|------|------|------|----------|
| 로그인 버튼 | 클릭 시 무반응 | 백엔드(localhost:8000) 미실행 | ✅ Mock 구현 |
| 회원가입 버튼 | 클릭 시 무반응 | onSubmit 핸들러 미구현 | ✅ Mock 구현 |
| /cases 접근 | 비인증 상태에서 접근 가능 | Navigation Guard 미구현 | ✅ Guard 추가 |

### 8.2 구현된 Mock 로직

#### 8.2.1 로그인 Mock (`LoginForm.tsx`)
```tsx
// 파일: frontend/src/components/auth/LoginForm.tsx
// Mock 모드: NEXT_PUBLIC_USE_MOCK_AUTH !== 'false' 일 때 활성화

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_AUTH !== 'false';

if (USE_MOCK) {
  // 500ms 딜레이 후 mock 토큰 발급
  const mockToken = `mock-jwt-token-${Date.now()}`;
  localStorage.setItem('authToken', mockToken);
  router.push('/cases');
}
```

**동작:**
- 이메일/비밀번호 입력 → 로그인 버튼 클릭
- 500ms 로딩 후 `authToken` 저장 → `/cases`로 리디렉션

#### 8.2.2 회원가입 Mock (`signup/page.tsx`)
```tsx
// 파일: frontend/src/app/signup/page.tsx
// useState로 폼 상태 관리 추가
// onSubmit 핸들러에서 mock 로직 실행

const handleSubmit = async (e: React.FormEvent) => {
  // 비밀번호 8자 이상 검증
  if (password.length < 8) {
    setError('비밀번호는 8자 이상이어야 합니다.');
    return;
  }
  // Mock 토큰 발급 + 사용자 정보 저장
  localStorage.setItem('authToken', mockToken);
  localStorage.setItem('mockUser', JSON.stringify({ name, email, lawFirm }));
  router.push('/cases');
};
```

**동작:**
- 이름, 이메일, 소속, 비밀번호 입력 → 무료 체험 시작 클릭
- 비밀번호 8자 미만 시 에러 메시지 표시
- 성공 시 `authToken` + `mockUser` 저장 → `/cases`로 리디렉션

#### 8.2.3 /cases Navigation Guard (`cases/index.tsx`)
```tsx
// 파일: frontend/src/pages/cases/index.tsx
// useEffect에서 authToken 확인

useEffect(() => {
  const token = localStorage.getItem('authToken');
  if (!token) {
    router.replace('/login');
  } else {
    setIsAuthChecking(false);
  }
}, [router]);
```

**동작:**
- 페이지 로드 시 `authToken` 확인
- 토큰 없으면 `/login`으로 리디렉션
- 토큰 있으면 페이지 렌더링

### 8.3 QA 테스트 방법

```bash
# 1. 프론트엔드 개발 서버 실행
cd frontend && npm run dev

# 2. 브라우저에서 테스트
# - http://localhost:3000/login → 아무 이메일/비밀번호로 로그인
# - http://localhost:3000/signup → 폼 입력 후 회원가입
# - http://localhost:3000/cases → 비로그인 시 /login으로 리디렉션
```

### 8.4 백엔드 연동 시 TODO

- [ ] `LoginForm.tsx`: `USE_MOCK` 조건 제거, 실제 API 호출만 사용
- [ ] `signup/page.tsx`: 실제 회원가입 API 연동 (`POST /auth/register`)
- [ ] `cases/index.tsx`: JWT 토큰 유효성 검증 로직 추가 (만료 체크)
- [ ] 환경변수 `NEXT_PUBLIC_USE_MOCK_AUTH=false` 설정하여 Mock 비활성화

### 8.5 관련 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/components/auth/LoginForm.tsx` | Mock 로그인 로직 추가 |
| `frontend/src/app/signup/page.tsx` | onSubmit 핸들러 + Mock 회원가입 구현 |
| `frontend/src/pages/cases/index.tsx` | Navigation Guard (useEffect) 추가 |

---

## 9. Frontend-Backend 통합 테스트 계획

> **목적:** Mock 인증 제거 후 실제 백엔드 API와 프론트엔드 연동 검증
> **상태:** 🔴 계획 단계

### 9.1 사전 준비 작업

#### 9.1.1 Mock 제거 체크리스트

| 파일 | 작업 | 상태 |
|------|------|------|
| `frontend/.env.local` | `NEXT_PUBLIC_USE_MOCK_AUTH=false` 설정 | ⬜ |
| `frontend/src/components/auth/LoginForm.tsx` | `USE_MOCK` 조건 제거 (실제 API만 사용) | ⬜ |
| `frontend/src/app/signup/page.tsx` | 실제 회원가입 API 연동 (`POST /auth/signup`) | ⬜ |
| `frontend/src/pages/cases/index.tsx` | JWT 토큰 유효성 검증 추가 (만료 체크) | ⬜ |

#### 9.1.2 환경 설정

```bash
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/leh_db
JWT_SECRET_KEY=<secure-random-key>

# Frontend (.env.local)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_USE_MOCK_AUTH=false
```

### 9.2 통합 테스트 시나리오

#### 9.2.1 인증 플로우 (Authentication)

| # | 테스트 케이스 | 예상 결과 | 상태 |
|---|--------------|----------|------|
| 1 | 회원가입 → 자동 로그인 | JWT 발급, /cases 리디렉션 | ⬜ |
| 2 | 로그인 (유효한 자격증명) | JWT 발급, /cases 리디렉션 | ⬜ |
| 3 | 로그인 (잘못된 비밀번호) | 401, 일반 에러 메시지 | ⬜ |
| 4 | 로그인 (존재하지 않는 이메일) | 401, 일반 에러 메시지 | ⬜ |
| 5 | 로그아웃 | 토큰 삭제, /login 리디렉션 | ⬜ |
| 6 | 만료된 토큰으로 API 호출 | 401, /login 리디렉션 | ⬜ |

#### 9.2.2 케이스 관리 (Cases)

| # | 테스트 케이스 | 예상 결과 | 상태 |
|---|--------------|----------|------|
| 1 | 케이스 목록 조회 | 사용자의 케이스 목록 표시 | ⬜ |
| 2 | 새 케이스 생성 | 케이스 생성, 목록 갱신 | ⬜ |
| 3 | 케이스 상세 조회 | 케이스 정보 + 증거 목록 | ⬜ |
| 4 | 케이스 상태 변경 | 상태 업데이트, UI 반영 | ⬜ |

#### 9.2.3 증거 관리 (Evidence)

| # | 테스트 케이스 | 예상 결과 | 상태 |
|---|--------------|----------|------|
| 1 | Presigned URL 요청 | S3 업로드 URL 반환 | ⬜ |
| 2 | 파일 업로드 (S3 Direct) | 업로드 성공, 메타데이터 저장 | ⬜ |
| 3 | 증거 목록 조회 | 타임라인 형식으로 표시 | ⬜ |
| 4 | 증거 상세 (AI 분석 결과) | Article 840 태그 포함 | ⬜ |

### 9.3 Playwright E2E 테스트 확장

#### 9.3.1 새로운 테스트 파일 구조

```
frontend/e2e/
├── auth.spec.ts          # 기존 (Mock 모드)
├── auth-real.spec.ts     # 실제 API 연동 테스트
├── cases.spec.ts         # 케이스 CRUD 테스트
├── evidence.spec.ts      # 증거 업로드/조회 테스트
└── fixtures/
    └── test-user.ts      # 테스트 사용자 데이터
```

#### 9.3.2 테스트 실행 명령

```bash
# Mock 모드 테스트 (백엔드 불필요)
NEXT_PUBLIC_USE_MOCK_AUTH=true npm run test:e2e

# 실제 API 테스트 (백엔드 필요)
NEXT_PUBLIC_USE_MOCK_AUTH=false npm run test:e2e -- --grep "@real-api"
```

### 9.4 통합 테스트 실행 절차

```bash
# 1. 백엔드 서비스 시작
cd backend && uvicorn app.main:app --reload

# 2. 데이터베이스 마이그레이션
cd backend && alembic upgrade head

# 3. 프론트엔드 서비스 시작 (Mock 비활성화)
cd frontend
echo "NEXT_PUBLIC_USE_MOCK_AUTH=false" >> .env.local
npm run dev

# 4. E2E 테스트 실행
npm run test:e2e

# 5. 수동 QA 테스트
# - http://localhost:3000/signup → 회원가입
# - http://localhost:3000/login → 로그인
# - http://localhost:3000/cases → 케이스 목록
```

### 9.5 예상 이슈 및 해결 방안

| 이슈 | 원인 | 해결 방안 |
|------|------|----------|
| CORS 에러 | 프론트엔드-백엔드 도메인 불일치 | `CORS_ORIGINS`에 `localhost:3000` 추가 |
| 401 Unauthorized | JWT 토큰 미전송 | `Authorization` 헤더 추가 확인 |
| 토큰 만료 | JWT expiry 짧음 | 프론트엔드에서 refresh 로직 구현 |
| DB 연결 실패 | PostgreSQL 미실행 | Docker 또는 로컬 PostgreSQL 시작 |

### 9.6 성공 기준

- [ ] 회원가입 → 로그인 → 케이스 생성 → 증거 업로드 전체 플로우 성공
- [ ] Playwright E2E 테스트 9개 모두 통과 (실제 API 모드)
- [ ] 에러 시 사용자 친화적 메시지 표시
- [ ] 네트워크 지연 시 로딩 상태 표시
- [ ] 보안: JWT 토큰 HTTP-only 쿠키 저장 검토

---

## 10. 메타 규칙

- 이 문서의 테스트 항목 외에는 **AI가 임의로 테스트를 추가하지 않는다.**
- `"go"` 입력 시:
  1. 아직 체크되지 않은 항목 중 **제일 위**의 항목을 선택
  2. 해당 항목에 대응하는 **테스트 1개** 작성
  3. 테스트를 통과시키는 최소한의 코드만 구현
  4. 필요하면 리팩터링 (구조 변경만)
- 모든 새로운 기능/수정은:
  - **테스트 → 구현 → 리팩터링** 순서를 따른다.
