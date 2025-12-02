# Project Folder Structure

LEH 프로젝트의 표준 폴더 구조를 정의합니다. 모든 컴포넌트가 이 구조를 따릅니다.

**Last Updated:** 2025-12-01

---

## Backend (`/backend`)

```
backend/
├── app/
│   ├── main.py              # FastAPI 엔트리포인트 + Mangum (Lambda)
│   ├── core/
│   │   ├── config.py        # 환경변수, 설정
│   │   ├── security.py      # JWT, 패스워드 해싱
│   │   ├── dependencies.py  # FastAPI 의존성 주입
│   │   └── logging_filter.py # 민감정보 필터링 로그
│   ├── db/
│   │   ├── session.py       # DB 연결 (SQLite/PostgreSQL)
│   │   ├── models.py        # SQLAlchemy 모델
│   │   └── schemas.py       # Pydantic 스키마 (DTO)
│   ├── api/
│   │   ├── auth.py          # 로그인/회원 API
│   │   ├── cases.py         # 사건 CRUD + Draft Preview
│   │   ├── evidence.py      # Presigned URL / 조회
│   │   └── admin.py         # 관리자 기능
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── case_service.py
│   │   ├── evidence_service.py
│   │   ├── draft_service.py      # Draft Preview 생성
│   │   ├── audit_log_service.py
│   │   ├── user_management_service.py
│   │   └── role_management_service.py
│   ├── repositories/
│   │   ├── case_repository.py
│   │   ├── user_repository.py
│   │   ├── case_member_repository.py
│   │   ├── audit_log_repository.py
│   │   └── invite_token_repository.py
│   ├── utils/
│   │   ├── s3.py            # S3 Adapter (Presigned URL)
│   │   ├── dynamo.py        # DynamoDB Adapter
│   │   ├── qdrant.py        # Qdrant Adapter (RAG)
│   │   └── openai_client.py # OpenAI Adapter
│   └── middleware/
│       ├── security.py      # HTTP 보안 헤더
│       ├── audit_log.py     # 감사 로그
│       └── error_handler.py # 전역 에러 핸들링
├── tests/
│   ├── test_api/            # API 엔드포인트 테스트
│   ├── test_services/       # 서비스 레이어 테스트
│   ├── test_middleware/     # 미들웨어 테스트
│   ├── test_integration/    # 통합 테스트 (AWS, Qdrant)
│   └── conftest.py          # 테스트 픽스처
├── alembic/                  # DB 마이그레이션
├── Dockerfile.lambda         # Lambda 배포용 Dockerfile
└── requirements.txt
```

### 배포 구성 (Lambda + API Gateway)
| 항목 | 값 |
|------|-----|
| Lambda 함수 | `leh-backend` |
| API Endpoint | `https://zhfiuntwj0.execute-api.ap-northeast-2.amazonaws.com` |
| ECR 이미지 | `540261961975.dkr.ecr.ap-northeast-2.amazonaws.com/leh-backend` |
| Architecture | arm64, 512MB, 30s timeout |

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `api/` | HTTP 요청/응답 처리 | DTO만 사용, 비즈니스 로직 금지 |
| `services/` | 비즈니스 로직 | Repository/Utils 호출 |
| `repositories/` | 데이터 접근 | DB 쿼리만, 비즈니스 로직 금지 |
| `utils/` | 외부 서비스 연동 | AWS SDK 등 캡슐화 |
| `middleware/` | 횡단 관심사 | 보안, 로깅, 에러 처리 |

---

## AI Worker (`/ai_worker`)

```
ai_worker/
├── handler.py               # Lambda 엔트리포인트 (S3 이벤트)
├── conftest.py              # 테스트 공통 설정
├── src/
│   ├── parsers/             # 파일 타입별 파서 (Strategy Pattern)
│   │   ├── base.py          # BaseParser 추상 클래스
│   │   ├── text.py          # 텍스트/채팅 파서 (KakaoTalk 등)
│   │   ├── image_ocr.py     # OCR 파서
│   │   ├── image_vision.py  # GPT-4o Vision 분석
│   │   ├── audio_parser.py  # Whisper STT 파서
│   │   ├── video_parser.py  # 비디오 처리 (오디오 추출)
│   │   └── pdf_parser.py    # PDF 추출
│   ├── analysis/            # 분석 엔진
│   │   ├── summarizer.py    # 요약 생성
│   │   ├── article_840_tagger.py  # 민법 840조 유책사유 라벨링
│   │   ├── evidence_scorer.py     # 증거력 점수
│   │   └── risk_analyzer.py       # 위험 분석
│   ├── service_rag/         # 법률 지식 RAG
│   │   ├── legal_parser.py
│   │   ├── legal_vectorizer.py
│   │   └── legal_search.py
│   ├── user_rag/            # 사건별 RAG
│   │   └── hybrid_search.py
│   ├── storage/             # 저장소 연동
│   │   ├── metadata_store.py  # DynamoDB
│   │   └── vector_store.py    # Qdrant
│   └── search/              # 검색 엔진
└── tests/
    ├── src/                 # 소스 코드 테스트
    │   ├── test_parsers.py
    │   ├── test_summarizer.py
    │   ├── test_article_840_tagger.py
    │   └── ...
    └── test_handler.py      # 핸들러 테스트
```

### 배포 구성 (Lambda + S3 Trigger)
| 항목 | 값 |
|------|-----|
| Lambda 함수 | `leh-ai-worker` |
| ECR 이미지 | `540261961975.dkr.ecr.ap-northeast-2.amazonaws.com/leh-ai-worker` |
| S3 트리거 | `leh-evidence-prod/cases/*` |
| Architecture | arm64, 1024MB, 300s timeout |

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `handler.py` | 오케스트레이션 | 파서 선택, 워크플로우 조정 |
| `parsers/` | 파일 파싱 | AI API 호출 (OCR, STT, Vision) |
| `analysis/` | 분석 실행 | LLM 호출, 라벨링 |
| `storage/` | 저장소 연동 | DynamoDB, Qdrant |
| `*_rag/` | RAG 파이프라인 | 임베딩, 검색 |

---

## Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── layout.tsx       # 루트 레이아웃
│   │   ├── page.tsx         # 랜딩 페이지
│   │   ├── login/           # 로그인 페이지
│   │   ├── signup/          # 회원가입 페이지
│   │   ├── sitemap.ts       # SEO 사이트맵
│   │   └── robots.ts        # SEO 로봇
│   ├── components/          # 재사용 컴포넌트
│   │   ├── ui/              # 기본 UI 컴포넌트
│   │   ├── landing/         # 랜딩 페이지 컴포넌트
│   │   ├── cases/           # 사건 관련 컴포넌트
│   │   ├── evidence/        # 증거 관련 컴포넌트
│   │   ├── draft/           # Draft Preview 컴포넌트
│   │   └── auth/            # 인증 관련 컴포넌트
│   ├── hooks/               # 커스텀 훅
│   │   ├── useAuth.ts
│   │   ├── useCase.ts
│   │   └── useEvidence.ts
│   ├── lib/                 # 유틸리티
│   │   ├── api/             # API 클라이언트
│   │   └── utils.ts
│   ├── types/               # TypeScript 타입
│   │   ├── case.ts
│   │   ├── evidence.ts
│   │   └── draft.ts
│   ├── styles/              # 글로벌 스타일
│   └── tests/               # 테스트 파일
│       ├── components/      # 컴포넌트 테스트
│       ├── pages/           # 페이지 테스트
│       ├── landing/         # 랜딩 페이지 테스트
│       └── accessibility/   # 접근성 테스트
├── public/                  # 정적 파일
└── package.json
```

### 배포 구성 (S3 + CloudFront)
| 항목 | 값 |
|------|-----|
| S3 버킷 | `leh-frontend-kbp9r` |
| CloudFront URL | `https://dpbf86zqulqfy.cloudfront.net` |
| 빌드 방식 | `next export` (정적 빌드) |
| API 연동 | `NEXT_PUBLIC_API_BASE_URL` 환경변수 |

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `app/` (또는 `pages/`) | 페이지 라우팅 | Next.js Pages Router |
| `components/` | UI 렌더링 | 작고 독립적, 재사용 가능 |
| `hooks/` | 상태 로직 | React Query 활용 |
| `lib/api/` | API 호출 | Backend 연동 (JWT 자동 첨부) |
| `types/` | 타입 정의 | 공유 타입 |

---

## Project Root

```
project-root/
├── .env                  # 통합 환경 변수 (Git 제외)
├── .env.example          # 환경 변수 템플릿
├── .gitignore
├── CLAUDE.md             # AI 에이전트 가이드
├── CONTRIBUTING.md       # → docs/CONTRIBUTING.md
├── README.md             # 프로젝트 소개
│
├── backend/              # FastAPI 백엔드
│   └── .env              # → symlink to ../.env
├── ai_worker/            # AI Lambda 워커
│   └── .env              # → symlink to ../.env
├── frontend/             # Next.js 대시보드
│   └── .env              # → symlink to ../.env
│
├── docs/                 # 문서
│   ├── specs/            # 설계 스펙
│   ├── guides/           # 개발 가이드
│   ├── business/         # 비즈니스 문서
│   └── archive/          # 아카이브
│
└── .github/              # GitHub 설정
    ├── workflows/        # CI/CD
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 공통 규칙

### 금지 사항
- 레이어 역참조 (api/ → services/ 가능, services/ → api/ 금지)
- utils/에 비즈니스 로직 넣기
- 전역 변수 사용

### 파일 크기
- 함수: 10-30줄
- 파일: 300줄 이하 권장

### 네이밍 컨벤션
- Python: `snake_case`
- TypeScript: `camelCase` (함수/변수), `PascalCase` (컴포넌트/타입)
- 파일명: 모듈 이름과 일치

---

## 관련 문서
- [CLEAN_ARCHITECTURE_GUIDE.md](CLEAN_ARCHITECTURE_GUIDE.md) - 아키텍처 원칙
- [BACKEND_SERVICE_REPOSITORY_GUIDE.md](BACKEND_SERVICE_REPOSITORY_GUIDE.md) - 백엔드 상세
- [FRONTEND_CLEAN_CODE.md](FRONTEND_CLEAN_CODE.md) - 프론트엔드 상세
- [AI_WORKER_PATTERN_GUIDE.md](AI_WORKER_PATTERN_GUIDE.md) - AI 워커 상세
