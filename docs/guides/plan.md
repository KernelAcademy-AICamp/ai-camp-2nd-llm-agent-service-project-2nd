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

## 1. Backend (FastAPI, RDS, S3, DynamoDB, OpenSearch)

### 1.1 인증 / 권한

- [ ] `POST /auth/login` 성공 시 JWT 발급 및 만료 시간 필드 포함
- [ ] 잘못된 자격증명으로 로그인 시 401, 에러 메시지는 “일반적인 문구”여야 한다 (민감 정보 노출 금지)
- [ ] 사건 상세 API 호출 시, JWT의 `sub` 와 `case_members` 권한을 검사하지 않으면 403을 반환해야 한다.

### 1.2 사건 관리 (Cases)

- [ ] `POST /cases` 호출 시 사건이 RDS `cases` 테이블에 저장되고, 응답 JSON의 `id`, `title`, `status` 가 DB 값과 일치해야 한다.
- [ ] `GET /cases` 는 현재 사용자에게 접근 권한이 있는 사건만 반환해야 한다 (`case_members` 기반).
- [ ] `DELETE /cases/{case_id}` 호출 시:
  - 사건 상태가 `closed` 로 변경되어야 하고,
  - 해당 사건의 OpenSearch 인덱스(`case_rag_{case_id}`) 삭제 요청이 서비스 레이어에서 호출되어야 한다 (통합 테스트에서는 mock으로 검증).

### 1.3 Evidence Upload (Presigned URL, S3)

- [ ] `POST /evidence/presigned-url` 은 유효한 `case_id`, `filename`, `content_type` 를 받으면:
  - `upload_url` 과 `fields` 를 포함한 구조를 반환해야 한다.
  - `fields.key` 는 `cases/{case_id}/raw/` 접두어로 시작해야 한다.
- [ ] 존재하지 않거나 권한 없는 `case_id` 로 Presigned URL을 요청하면 404를 반환해야 한다.
- [ ] Presigned URL의 만료 시간이 **5분 이내**인지 확인하는 유닛 테스트가 있어야 한다 (실제 AWS 호출 대신 서명 파라미터 검사).

### 1.4 Evidence 메타 조회 (DynamoDB)

- [ ] `GET /cases/{case_id}/evidence` 호출 시:
  - DynamoDB에서 `case_id` 로 조회된 evidence 목록을 `timestamp` 기준으로 정렬해 반환해야 한다.
  - 삭제 플래그(`deleted = true`) 가 있는 항목은 리스트에서 제외해야 한다.
- [ ] `GET /evidence/{evidence_id}` 는:
  - `summary`, `labels`, `timestamp`, `download_url` 을 포함해야 하고
  - `download_url` 은 짧은 유효기간의 S3 Presigned URL 이어야 한다 (형태만 테스트).

### 1.5 Draft Preview (RAG + GPT-4o)

- [ ] `POST /cases/{case_id}/draft-preview` 호출 시:
  - 사건에 증거가 하나도 없으면 400을 반환해야 한다.
  - 최소 1개 이상의 evidence가 있을 경우, `draft_text` 와 `citations` 배열이 포함된 JSON을 반환해야 한다.
- [ ] Draft 생성 시 사용되는 Prompt 문자열에는:
  - **RAG 기반 사실 인용 지시**,
  - **Hallucination 금지 규칙**,
  - **“최종 결정은 변호사가 한다”** 류의 책임 한계 문구가 포함되어야 한다 (문자열 포함 여부 테스트).

---

## 2. AI Worker (L, S3 Event → DynamoDB / OpenSearch)

### 2.1 Event 파싱

- [ ] S3 Event JSON 을 입력으로 받았을 때:
  - 첫 번째 `Records[0]` 에서 `bucket.name` 과 `object.key` 를 정확히 추출해야 한다.
- [ ] 지원하지 않는 파일 확장자(예: `.exe`)일 경우:
  - Worker는 해당 이벤트를 “unsupported” 상태로 로깅하고,
  - DLQ(SQS) 로 전송하는 헬퍼를 호출해야 한다 (테스트에서는 호출 횟수로 검증).

### 2.2 파일 타입별 처리

- [ ] `.txt` 파일은 text parser 로 라우팅되어야 하고, 결과 JSON에 `content` 필드가 포함돼야 한다.
- [ ] 이미지(`.jpg`, `.png`) 업로드 시:
  - Vision/OCR 모듈에서 반환한 텍스트를 `content` 에 저장해야 한다.
- [ ] PDF 파일은:
  - 먼저 텍스트 추출 시도 후 실패하면 OCR fallback 로직을 호출해야 한다 (두 경로 모두 유닛 테스트).

### 2.3 카톡/메신저 파싱

- [ ] 카카오톡 내보내기 형식 텍스트에서:
  - 날짜, 화자, 메시지를 파싱해 `[ { speaker, timestamp, message } ]` 구조를 생성해야 한다.
- [ ] 날짜 포맷이 인식되지 않으면 `timestamp = "unknown"` 으로 저장해야 한다.

### 2.4 STT 처리 (Whisper)

- [ ] 오디오 파일 처리 시:
  - STT 결과 텍스트가 비어 있지 않은 상태로 `content` 에 저장되어야 한다.
- [ ] 화자 분리(diarization)가 실패할 경우:
  - Worker는 경고 로그만 남기고, transcript 자체는 그대로 저장해야 한다.

### 2.5 의미 분석 & 라벨링 (민법 840)

- [ ] 분석 결과 JSON에서 `labels` 필드는:
  - 항상 **배열(Array)** 이어야 한다.
  - 0개~N개의 유책사유 라벨을 포함하되, `null` 이나 단일 문자열이 되면 안 된다.
- [ ] 라벨 값은 사전에 정의된 유효 값 목록(예: `"부정행위"`, `"학대"`) 중 하나여야 한다.

### 2.6 Embedding + OpenSearch index

- [ ] Embedding 생성 모듈은:
  - 일정 길이 이상의 벡터(예: 1536 길이)를 반환해야 한다 (길이만 테스트).
- [ ] 동일 `evidence_id` 재처리 시:
  - OpenSearch 문서는 **덮어쓰기** 되어야 하고,
  - DynamoDB의 해당 항목도 최신 값으로 업데이트돼야 한다.

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

- [ ] 타임라인 아이템은:
  - 날짜, 요약 텍스트, 관련 evidence 링크를 포함한 세로형 구조여야 한다.
- [ ] 타임라인에서 evidence 링크를 누르면:
  - 별도 전체 페이지로 이동하지 않고, **모달 또는 사이드 패널**로 상세 내용을 보여야 한다 (flow 보호).

### 3.6 Draft 탭 (AI 초안)

- [ ] Draft 탭 상단에는:
  - “이 문서는 AI가 생성한 초안이며, 최종 책임은 변호사에게 있습니다.” 와 같은 **명시적 Disclaimer 텍스트**가 항상 표시되어야 한다.
- [ ] 리치 텍스트 에디터는:
  - 기본적으로 **문서 본문만 보여주는 Zen 모드**에 가깝게, 불필요한 패널을 최소화해야 한다.
- [ ] “초안 생성/재생성” 버튼은 항상 Primary 스타일이어야 하며, 클릭 후 로딩 상태를 명확히 보여줘야 한다.

### 3.7 의뢰인 증거 제출 포털

- [ ] 포털 화면에는:
  - 로펌/서비스 로고, 간단한 안내 문구, 단일 업로드 영역, 업로드 완료/실패 피드백만 있어야 한다.
- [ ] 업로드 완료 시:
  - “파일 N개가 안전하게 전송되었습니다.” 라는 성공 메시지가 `Success Green` 색상으로 표시돼야 한다.

---

## 4. 보안 관련 테스트 (전 계층 공통)

- [ ] HTTP 응답 헤더에는:
  - 최소한 `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` 가 설정되어야 한다 (백엔드 유닛/통합 테스트).
- [ ] 로그 기록 시:
  - JWT 토큰, 비밀번호, 주민등록번호 등 민감정보가 로그에 포함되지 않는지 검증하는 테스트가 있어야 한다 (샘플 로그 캡처 후 assert).
- [ ] GitHub 레포 코드/설정에서:
  - `OPENAI_API_KEY`, DB 비밀번호 등 비밀값이 **하드코딩**되어 있지 않은지 검사하는 정적 체크 스크립트 테스트를 추가해야 한다.

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

## 6. 메타 규칙

- 이 문서의 테스트 항목 외에는 **AI가 임의로 테스트를 추가하지 않는다.**
- `"go"` 입력 시:
  1. 아직 체크되지 않은 항목 중 **제일 위**의 항목을 선택
  2. 해당 항목에 대응하는 **테스트 1개** 작성
  3. 테스트를 통과시키는 최소한의 코드만 구현
  4. 필요하면 리팩터링 (구조 변경만)
- 모든 새로운 기능/수정은:
  - **테스트 → 구현 → 리팩터링** 순서를 따른다.
