
### *REST API 명세서 (MVP)*

**버전:** v2.0  
**작성일:** 2025-11-18  
**작성자:** Team H (Backend)  
**관련 문서:** `PRD.md`, `ARCHITECTURE.md`, `BACKEND_DESIGN.md`, `AI_PIPELINE_DESIGN.md`, `FRONTEND_SPEC.md`

---

# 📌 0. 목적 & 범위

이 문서는 **LEH 백엔드 REST API**의 공식 스펙이다.

- 클라이언트(Frontend)와 백엔드 간 통신 규약 정의
- 주요 리소스(Cases, Evidence, Draft)의 요청/응답 형식 정의
- 인증/에러 공통 규칙 정의

> 참고: 기존 Paralegal API 설계의 엔드포인트 구조와 에러 처리 원칙을 계승하되, S3 Presigned URL, 사건별 RAG, Preview-only Draft 등 LEH 아키텍처에 맞게 재구성했다. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

---

# 🧭 1. 공통 규칙

## 1.1 Base

- Base URL (예시): `https://api.leh.app`
- 모든 API는 **JSON** 기반 (파일 업로드는 예외)

## 1.2 인증

- 방식: **JWT (Bearer Token)**
- 헤더:

http
Authorization: Bearer <JWT_TOKEN>
`

- `/auth/login`, `/health` 일부를 제외하면 **모든 엔드포인트에 필수**

## 1.3 공통 응답 형식

### 성공 (예)

json
{
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2025-11-18T10:00:00Z"
  }
}

### 오류 (예)

json
{
  "error": {
    "code": "CASE_NOT_FOUND",
    "message": "존재하지 않거나 접근 권한이 없는 사건입니다."
  }
}

- HTTP Status Code:

  - 200 / 201 / 204: 성공
  - 400: 잘못된 요청 (validation 실패 등)
  - 401: 인증 실패 (토큰 없음/무효)
  - 403: 권한 없음
  - 404: 리소스 없음
  - 409: 충돌 (중복 요청, Draft 생성 중 등)
  - 413: 파일 과대 (Evidence 업로드 관련)
  - 500: 서버 오류

---

# 🔐 2. 인증 / Auth

## 2.1 로그인

### `POST /auth/login`

- 설명: 이메일/비밀번호로 로그인 후 JWT 발급
- 요청 Body:

json
{
  "email": "<user@example.com>",
  "password": "string"
}

- 응답 (200):

json
{
  "data": {
    "access_token": "jwt-token",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "name": "홍길동",
      "role": "LAWYER"
    }
  }
}

- 오류:

  - 401: 잘못된 인증 정보 (메시지는 항상 일반적인 문구로)

## 2.2 토큰 갱신 (옵션)

### `POST /auth/refresh`

- 설명: Refresh Token으로 Access Token 재발급 (도입 시)

---

# 📁 3. 사건(Case) API

## 3.1 사건 목록 조회

### `GET /cases`

- 설명: 로그인한 사용자가 접근 가능한 사건 리스트
- 쿼리 파라미터:

  - `status` (optional): `active` / `closed`
  - `q` (optional): 사건명 검색
- 응답 (200):

json
{
  "data": [
    {
      "id": "case_123",
      "title": "김○○ 이혼 사건",
      "status": "active",
      "updated_at": "2025-11-18T02:10:00Z",
      "evidence_count": 42,
      "draft_status": "ready"
    }
  ]
}

---

## 3.2 사건 생성

### `POST /cases`

- 설명: 새로운 사건 생성
- 요청 Body:

json
{
  "title": "김○○ 이혼 사건",
  "description": "간략 설명 (선택)"
}

- 응답 (201):

json
{
  "data": {
    "id": "case_123",
    "title": "김○○ 이혼 사건",
    "description": "간략 설명",
    "status": "active",
    "created_at": "2025-11-18T01:00:00Z"
  }
}

---

## 3.3 사건 상세 조회

### `GET /cases/{case_id}`

- 설명: 사건 요약 정보 조회
- 응답 (200):

json
{
  "data": {
    "id": "case_123",
    "title": "김○○ 이혼 사건",
    "description": "간략 설명",
    "status": "active",
    "created_at": "2025-11-18T01:00:00Z",
    "evidence_count": 42,
    "draft_status": "ready"
  }
}

---

## 3.4 사건 수정

### `PATCH /cases/{case_id}`

- 설명: 사건 제목/설명 수정
- 요청 Body:

json
{
  "title": "수정된 사건명",
  "description": "수정된 설명"
}

- 응답 (200): 수정된 사건 객체

---

## 3.5 사건 종료(Soft Delete)

### `DELETE /cases/{case_id}`

- 설명:

  - 사건을 “종료” 상태로 전환
  - OpenSearch 사건 인덱스 삭제
  - DynamoDB 메타데이터 soft-delete
  - S3 원본 증거는 유지 (법무법인 책임) — PRD 규칙 따름

- 응답:

  - 204 No Content

---

# 📎 4. 증거(Evidence) API

LEH는 **Presigned URL + S3 직접 업로드**를 사용한다.

## 4.1 업로드용 Presigned URL 발급

### `POST /evidence/presigned-url`

- 설명: 특정 사건에 대한 S3 업로드 URL 발급
- 요청 Body:

json
{
  "case_id": "case_123",
  "filename": "kakao_export.txt",
  "content_type": "text/plain"
}

- 응답 (200):

json
{
  "data": {
    "upload_url": "<https://s3>....",
    "fields": {
      "key": "cases/case_123/raw/uuid_kakao_export.txt",
      "policy": "...",
      "x-amz-algorithm": "...",
      "x-amz-credential": "...",
      "x-amz-date": "...",
      "x-amz-signature": "..."
    },
    "evidence_temp_id": "temp_abc123"
  }
}

---

## 4.2 업로드 완료 알림

### `POST /evidence/upload-complete`

- 설명: 클라이언트가 S3 업로드를 마친 후 백엔드에 알리는 엔드포인트

- 백엔드는 Evidence 레코드 생성 + AI Worker 트리거

- 요청 Body:

json
{
  "case_id": "case_123",
  "evidence_temp_id": "temp_abc123",
  "s3_key": "cases/case_123/raw/uuid_kakao_export.txt",
  "note": "2021년~2023년 카카오톡 내역"
}

- 응답 (201):

json
{
  "data": {
    "id": "ev_001",
    "case_id": "case_123",
    "filename": "kakao_export.txt",
    "file_type": "text/plain",
    "status": "processing",
    "uploaded_at": "2025-11-18T01:20:00Z"
  }
}

---

## 4.3 사건별 증거 목록 조회 (타임라인용)

### `GET /cases/{case_id}/evidence`

- 설명: 타임라인·리스트 표기를 위한 사건별 증거 메타데이터 조회

- 쿼리 파라미터 (optional):

  - `type`: `text|image|audio|video|pdf`
  - `label`: 유책사유 라벨 (예: `학대`, `부정행위`)
  - `from`, `to`: 날짜 범위

- 응답 (200):

json
{
  "data": [
    {
      "id": "ev_001",
      "case_id": "case_123",
      "type": "text",
      "filename": "kakao_export.txt",
      "timestamp": "2021-06-01T10:20:00Z",
      "speaker": "원고",
      "labels": ["계속적 불화"],
      "summary": "6월 1일 새벽 반복적인 언쟁...",
      "status": "done"
    }
  ]
}

---

## 4.4 증거 상세 조회

### `GET /evidence/{evidence_id}`

- 설명: 특정 증거의 상세 정보 + 원본 다운로드 URL

- 응답 (200):

json
{
  "data": {
    "id": "ev_001",
    "case_id": "case_123",
    "type": "audio",
    "filename": "call.m4a",
    "timestamp": "2021-06-01T10:20:00Z",
    "speaker": "피고",
    "labels": ["폭언", "계속적 불화"],
    "summary": "통화 내내 고함 및 모욕적 표현...",
    "content": "STT 전문 (필요 시 일부만)",
    "ocr_text": null,
    "transcript": "Whisper STT 결과...",
    "download_url": "<https://s3-presigned-url>..."
  }
}

- `download_url`은 짧은 유효기간의 Presigned URL (이미지/PDF/오디오 뷰어에 사용)

---

# 🧠 5. Draft(소장 초안) API

LEH는 **“Preview 전용 Draft”**만 제공하며,
실제 제출/최종 편집은 변호사가 Word 등에서 처리한다.

## 5.1 Draft Preview 생성

### `POST /cases/{case_id}/draft-preview`

- 설명:

  - 사건별 RAG + GPT-4o를 이용해 **소장 초안 텍스트 + 인용 증거 목록** 생성
  - 동기 처리(HTTP 응답 내에서 완료)를 기본 가정
  - 향후 비동기 큐 기반 설계로 확장 가능 (기존 Paralegal은 비동기 초안 생성을 제안함)

- 요청 Body (옵션 필드):

json
{
  "sections": ["청구취지", "청구원인"],
  "language": "ko",
  "style": "법원 제출용_표준"
}

- 응답 (200):

json
{
  "data": {
    "case_id": "case_123",
    "draft_text": "1. 당사자 관계...\n2. 혼인 경위...\n...",
    "citations": [
      {
        "evidence_id": "ev_001",
        "snippet": "2021년 6월 1일 피고의 폭언 장면",
        "labels": ["폭언", "계속적 불화"]
      }
    ],
    "generated_at": "2025-11-18T02:00:00Z"
  }
}

- 오류:

  - 400: 증거가 전혀 없는 사건 등
  - 409: Draft 생성이 이미 진행 중인 경우 (비동기 모드 도입 시)

---

## 5.2 Draft Preview 조회 (선택)

### `GET /cases/{case_id}/draft-preview`

- 설명: 최근 생성된 Draft Preview 조회 (캐싱/이력 관리용)
- 응답: 200 / 404 (아직 생성 전)

---

## 5.3 Draft docx 다운로드

### `GET /cases/{case_id}/draft-export`

- 설명:

  - 현재 Draft Preview 내용을 **.docx 파일**로 내려줌
  - 기존 Paralegal 설계에서도 `/cases/{case_id}/draft/export` 형태의 docx 다운로드를 제안함

- 응답:

  - `Content-Disposition: attachment; filename="case_123_draft.docx"`
  - 바디: 바이너리 파일

---

# 🔍 6. RAG / 검색 API [MVP 이후]

> ⚠️ **Note:** 이 섹션의 API는 MVP 이후 구현 예정입니다.

## 6.1 사건 내 RAG 검색

### `GET /cases/{case_id}/search` [미구현]

- 설명: 사건별 증거를 기반으로 한 의미 검색 (OpenSearch + 임베딩)

- 쿼리 파라미터:

  - `q`: 검색 질의 (예: `"폭언이 집중된 시점"`)
  - `label` (옵션): 유책사유 라벨 필터
  - `limit` (옵션): 기본 20

- 응답 (200):

json
{
  "data": [
    {
      "evidence_id": "ev_001",
      "score": 0.91,
      "snippet": "2021년 6월 1일 통화에서 피고가...",
      "labels": ["폭언"]
    }
  ]
}

---

# 🛠 7. 관리/헬스체크 API

## 7.1 Health Check

### `GET /health`

- 설명: 단순 헬스 체크 (모니터링/로드밸런서용)
- 응답 (200):

json
{
  "status": "ok"
}

---

# 🧪 8. 사용 예시 플로우

1. **로그인**

   - `POST /auth/login` → JWT 획득

2. **사건 생성 & 진입**

   - `POST /cases` → 새 사건 ID
   - `GET /cases/{case_id}` → 상세 조회

3. **증거 업로드**

   - `POST /evidence/presigned-url` → S3 업로드 정보
   - 클라이언트가 S3에 직접 업로드
   - `POST /evidence/upload-complete` → Evidence 생성 (status=`processing`)
   - AI Worker 완료 후 `GET /cases/{case_id}/evidence`에서 `status=done` 확인

4. **타임라인/세부 내용 확인**

   - `GET /cases/{case_id}/evidence` → 리스트
   - `GET /evidence/{evidence_id}` → 전문/요약/다운로드 URL

5. **Draft Preview 생성/다운로드**

   - `POST /cases/{case_id}/draft-preview` → 초안 텍스트 + 인용 증거
   - `GET /cases/{case_id}/draft-export` → docx 파일 다운로드

6. **사건 종료**

   - `DELETE /cases/{case_id}` → 사건 상태 종료, RAG index 제거

---

# ✅ 9. 확장 포인트 (v2 이후)

- Draft 버전 관리 및 편집 이력 (`PUT /cases/{id}/draft`)
- Opponent Claim 관리 API (상대방 주장 텍스트 + 증거 링크)
- Webhook 기반 비동기 알림 (증거 분석 완료, Draft 생성 완료 등)
- Admin용 감사 로그 조회 API

---

**END OF API_SPEC.md**
