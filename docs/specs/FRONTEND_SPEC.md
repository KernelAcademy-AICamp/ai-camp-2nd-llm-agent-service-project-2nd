
### *변호사용 웹 대시보드 프론트엔드 상세 설계서*

**버전:** v2.1
**작성일:** 2025-11-18
**작성자:** Team P
**관련 문서:**

* `PRD.md`
* `ARCHITECTURE.md`
* `BACKEND_DESIGN.md`
* `AI_PIPELINE_DESIGN.md`
* `.github` 템플릿

---

# 📌 **0. 문서 목적**

본 문서는 LEH(Legal Evidence Hub)의 **프론트엔드(웹 대시보드)** 전체 구조와 화면 설계를 정의한다.
이 문서는 다음을 목표로 한다:

* 개발자(P/H/L)가 동일한 UI/UX 기준을 이해하도록 한다.
* 화면·컴포넌트·라우팅·상태관리 규칙을 명확히 한다.
* 백엔드/AI와의 데이터 연동 인터페이스를 통일한다.
* 보안·프라이버시 기준을 준수한 운영이 가능하게 한다.

이 문서는 **프론트엔드 구현의 Single Source of Truth**이다.

---

# 🧭 **1. 기술 스택 및 기본 정책**

## 1.1 기술 스택

| 구분          | 기술                                            |
| ----------- | --------------------------------------------- |
| Framework   | **React + Next.js**                           |
| 언어          | **TypeScript**                                |
| 스타일         | **Tailwind CSS**                              |
| 상태 관리       | **React Query(Server State)** + Context/Hooks |
| 라우팅         | Next.js File Routing                          |
| HTTP Client | axios 또는 fetch wrapper                        |
| 빌드·배포       | S3 + CloudFront                               |

---

## 1.2 FE 운영 원칙

1. **Preview-Only**

   * AI가 생성한 초안은 자동 제출 X
   * 변호사가 편집·확정해야 법적 효력
2. **타임라인 중심 UX**

   * 시간순 정렬된 증거 흐름을 중심 화면으로 구성
3. **브라우저 저장 제한**

   * 증거 전문·요약·민감정보는 LocalStorage/IndexedDB에 저장 금지
4. **반응형 + 접근성 우선**

   * 인증·필터·Draft 등은 모바일/노트북 모두 지원
5. **모든 API는 JWT 기반**

   * 인증 없으면 요청 차단, FE에서 글로벌 에러 처리

---

# 🗂 **2. 디렉토리 구조 (통일된 LEH 표준)**

문서 전체를 통일한 구조:

frontend/
├── src/
│   ├── pages/                # Next.js page routing
│   │   ├── index.tsx
│   │   ├── cases/index.tsx
│   │   ├── cases/[id]/index.tsx
│   │   └── settings/index.tsx
│   ├── components/
│   │   ├── layout/           # AppLayout / Sidebar
│   │   ├── cases/            # CaseList, CaseHeader
│   │   ├── evidence/         # EvidenceTimeline / Card / Upload
│   │   ├── draft/            # DraftPreview / CitationList
│   │   └── common/
│   ├── hooks/
│   ├── api/
│   ├── types/
│   ├── utils/
│   └── styles/
└── package.json

디렉토리 기능은 **백엔드 문서 구조와 동일한 논리 레이어링**을 따른다.

---

# 📑 **3. 주요 페이지 정의**

## 3.1 로그인 페이지 (`/`)

### 목적

* 변호사/스태프 인증
* JWT 발급 후 사건 리스트로 이동

### UI 요소

* 이메일 / 비밀번호 입력
* 로그인 버튼
* 오류 메시지: “이메일 또는 비밀번호가 올바르지 않습니다.”

---

## 3.2 사건 리스트 페이지 (`/cases`)

### 목적

* 내가 맡은 사건 전체 열람
* 사건 생성/검색/정렬

### 구성

* 상단: 페이지 제목, `+ 사건 생성` 버튼
* 검색바: 사건명 검색
* 필터: 상태(진행/종료)
* 리스트: 사건명 / 담당자 / 상태 / 최근 업데이트

### 동작

* 사건 클릭 → `/cases/{id}` 이동
* 생성 버튼 → 사건 생성 모달

---

## 3.3 사건 상세 페이지 (`/cases/{id}`)

LEH의 핵심 UX.

### 화면 레이아웃

┌───────────────────────────────────────────────┐
│ CaseHeader: 사건 제목 / 상태 / 멤버 / 버튼들 │
├───────────────────────────────────────────────┤
│ 좌측: EvidenceFilterBar                       │
│                                               │
│ 우측: EvidenceTimeline (카드 리스트)          │
├───────────────────────────────────────────────┤
│ DraftPreview (하단 고정 혹은 패널)            │
└───────────────────────────────────────────────┘

### CaseHeader 기능

* 사건명
* 사건 상태(active/closed)
* 멤버 배지
* 버튼:

  * 증거 업로드
  * 사건 종료
  * RAG 검색 열기

---

# 🧩 **4. 컴포넌트 상세 정의**

## 4.1 EvidenceUpload

**기능**

* 파일 Drag & Drop
* Presigned URL 요청 후 S3 업로드
* 업로드 상태: 대기/진행중/분석중/완료 표시
* 오류 발생 시 재시도 버튼

---

## 4.2 EvidenceTimeline

**입력 데이터**
DynamoDB Evidence JSON 리스트

**표시 요소**

* 시간순 정렬
* EvidenceCard 반복 렌더
* 카드 클릭 → EvidenceDetailModal 표시
* 필터(유형/라벨/날짜)에 따라 실시간 갱신

---

## 4.3 EvidenceCard

**요소**

* 유형 아이콘(text/image/audio/pdf)
* 요약
* timestamp
* speaker
* labels(유책사유 Tag)
* 클릭 → 상세 모달

---

## 4.4 EvidenceDetailModal

**표시**

* 원본 (이미지/텍스트/오디오/문서)
* AI 요약
* 라벨(유책사유, 감정)
* 핵심 문장 하이라이트
* 이 증거가 타임라인에서 어느 위치인지 표시

---

## 4.5 DraftPreview

**역할**

* “소장 초안 제안” 패널
* `draft_text` + `citations` 렌더
* Draft 재생성 버튼
* docx 파일 다운로드 버튼

**주의사항 (법적 준수)**

* 자동 제출 금지
* 자동 입력 금지
* FE는 “읽기 + 다운로드”만 제공

---

# 🔌 **5. API 연동 사양 (Front ↔ Back)**

## 5.1 인증

| 동작      | API                | 비고     |
| ------- | ------------------ | ------ |
| 로그인     | `POST /auth/login` | JWT 발급 |
| 토큰 만료 시 | `/auth/refresh`    | 옵션     |

---

## 5.2 사건 관리

| 목적        | API                  |
| --------- | -------------------- |
| 사건 리스트 조회 | `GET /cases`         |
| 사건 상세 조회  | `GET /cases/{id}`    |
| 사건 생성     | `POST /cases`        |
| 사건 종료     | `DELETE /cases/{id}` |

---

## 5.3 증거 관리

### Presigned URL

GET /evidence/presigned-url?case_id=xxx&filename=xxx

### 증거 리스트

GET /cases/{id}/evidence

---

## 5.4 Draft 생성

POST /cases/{id}/draft-preview

응답:

json
{
  "draft_text": "...",
  "citations": [
    { "evidence_id": "ev_123", "quote": "..." }
  ]
}

---

# 🔄 **6. FE 내부 데이터 흐름**

## 6.1 증거 업로드 흐름

[1] 사용자가 파일 선택
[2] FE → BE: Presigned URL 요청
[3] FE → S3: 직접 업로드
[4] S3 Event → AI Worker 자동 실행
[5] Worker → DynamoDB 반영
[6] FE → BE: /cases/{id}/evidence 재조회
[7] 타임라인 실시간 갱신

---

## 6.2 Draft 생성 흐름

[1] FE: DraftPreview에서 “Draft 생성”
[2] FE → BE: draft-preview 요청
[3] BE: 사건 증거 → RAG → GPT-4o → 초안 생성
[4] BE → FE: draft_text + citations 반환
[5] FE: Preview 표시

---

# 🔒 **7. 보안 · 프라이버시 정책 (FE)**

1. **민감 정보 브라우저 저장 금지**

   * LocalStorage에는 JWT/token만 저장
   * 증거 전문/요약/라벨 등은 저장 금지

2. **HTTPS 강제**

3. **오류 로그에는 개인정보 제거**

   * Sentry/Logging에 “증거 내용” 포함되면 안 됨

4. **세션 종료 정책**

   * 장시간 미사용 시 자동 로그아웃(UI 안내 필요)

5. **권한 검사**

   * 사건 접근 권한 없으면 `/cases`로 리다이렉트

---

# 🧪 **8. 테스트 전략**

## 8.1 Unit Test

* 컴포넌트 렌더링 (EvidenceCard, DraftPreview 등)
* 필터 로직
* API hook (useEvidence/useCase)

## 8.2 Integration Test

* Presigned URL 발급 → S3 업로드 → EvidenceTimeline 반영 (Mock)

## 8.3 E2E

* Playwright/Cypress

  * 로그인 → 사건 선택 → 증거 업로드 → Draft 생성

---

# 📦 **9. 개발 체크리스트**

* [ ] JWT 로그인/로그아웃 구현
* [ ] 사건 리스트 / 상세 / 상태관리 구현
* [ ] Presigned URL 기반 증거 업로드
* [ ] EvidenceTimeline + 필터 조합
* [ ] EvidenceDetailModal
* [ ] DraftPreview (생성/갱신/다운로드)
* [ ] 글로벌 에러/로딩/권한 처리
* [ ] 민감 데이터 FE 저장 금지 준수

---

# 🔚 END OF FRONTEND_SPEC.md
