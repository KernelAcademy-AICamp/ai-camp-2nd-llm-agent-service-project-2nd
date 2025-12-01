# Project Folder Structure

LEH 프로젝트의 표준 폴더 구조를 정의합니다. 모든 컴포넌트가 이 구조를 따릅니다.

---

## Backend (`/backend`)

```
backend/
├── app/
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── core/
│   │   ├── config.py        # 환경변수, 설정
│   │   ├── security.py      # JWT, 패스워드 해싱
│   │   ├── dependencies.py  # FastAPI 의존성 주입
│   │   └── logging.py       # 구조화 로그 설정
│   ├── db/
│   │   ├── session.py       # DB 연결 (RDS)
│   │   ├── models.py        # SQLAlchemy 모델
│   │   └── schemas.py       # Pydantic 스키마 (DTO)
│   ├── api/
│   │   ├── auth.py          # 로그인/회원 API
│   │   ├── cases.py         # 사건 CRUD
│   │   ├── evidence.py      # Presigned URL / 조회
│   │   └── draft.py         # Draft Preview API
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── case_service.py
│   │   ├── evidence_service.py
│   │   └── draft_service.py
│   ├── repositories/
│   │   ├── case_repository.py
│   │   ├── user_repository.py
│   │   └── evidence_repository.py
│   ├── utils/
│   │   ├── s3.py            # S3 Adapter
│   │   ├── dynamo.py        # DynamoDB Adapter
│   │   ├── qdrant.py    # Qdrant Adapter
│   │   └── openai_client.py # OpenAI Adapter
│   └── middleware/
│       ├── auth_middleware.py
│       ├── audit.py
│       └── error_handler.py
├── tests/
│   ├── test_api/
│   ├── test_services/
│   └── conftest.py
├── alembic/                  # DB 마이그레이션
└── requirements.txt
```

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `api/` | HTTP 요청/응답 처리 | DTO만 사용, 비즈니스 로직 금지 |
| `services/` | 비즈니스 로직 | Repository/Utils 호출 |
| `repositories/` | 데이터 접근 | DB 쿼리만, 비즈니스 로직 금지 |
| `utils/` | 외부 서비스 연동 | AWS SDK 등 캡슐화 |

---

## AI Worker (`/ai_worker`)

```
ai_worker/
├── handler.py               # Lambda 엔트리포인트 (S3 이벤트)
├── src/
│   ├── parsers/             # 파일 타입별 파서 (Strategy Pattern)
│   │   ├── base.py          # BaseParser 추상 클래스
│   │   ├── text.py          # 텍스트/채팅 파서
│   │   ├── image_ocr.py     # OCR 파서
│   │   ├── image_vision.py  # Vision 분석
│   │   ├── audio_parser.py  # STT 파서
│   │   ├── video_parser.py  # 비디오 처리
│   │   └── pdf_parser.py    # PDF 추출
│   ├── analysis/            # 분석 엔진
│   │   ├── summarizer.py    # 요약 생성
│   │   ├── article_840_tagger.py  # 유책사유 라벨링
│   │   ├── evidence_scorer.py     # 증거력 점수
│   │   └── risk_analyzer.py       # 위험 분석
│   ├── service_rag/         # 법률 지식 RAG
│   │   ├── legal_parser.py
│   │   ├── legal_vectorizer.py
│   │   └── legal_search.py
│   ├── user_rag/            # 사건별 RAG
│   │   └── hybrid_search.py
│   └── storage/             # 저장소 연동
│       ├── metadata_store.py  # DynamoDB
│       └── vector_store.py    # Qdrant
├── tests/
│   ├── test_parsers/
│   └── conftest.py
└── requirements.txt
```

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `handler.py` | 오케스트레이션 | 파서 선택, 워크플로우 조정 |
| `parsers/` | 파일 파싱 | AI API 호출 (OCR, STT, Vision) |
| `analysis/` | 분석 실행 | LLM 호출, 라벨링 |
| `storage/` | 저장소 연동 | DynamoDB, Qdrant |

---

## Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── (auth)/          # 인증 관련 페이지
│   │   ├── cases/           # 사건 관련 페이지
│   │   └── layout.tsx       # 루트 레이아웃
│   ├── components/          # 재사용 컴포넌트
│   │   ├── ui/              # 기본 UI 컴포넌트
│   │   ├── cases/           # 사건 관련 컴포넌트
│   │   ├── evidence/        # 증거 관련 컴포넌트
│   │   └── auth/            # 인증 관련 컴포넌트
│   ├── hooks/               # 커스텀 훅
│   │   ├── useAuth.ts
│   │   ├── useCase.ts
│   │   └── useEvidence.ts
│   ├── lib/                 # 유틸리티
│   │   ├── api/             # API 클라이언트
│   │   └── utils.ts
│   ├── types/               # TypeScript 타입
│   └── styles/              # 글로벌 스타일
├── public/                  # 정적 파일
├── tests/
└── package.json
```

### 레이어 책임

| 레이어 | 책임 | 규칙 |
|--------|------|------|
| `app/` | 페이지 라우팅 | Next.js App Router |
| `components/` | UI 렌더링 | 작고 독립적, 재사용 가능 |
| `hooks/` | 상태 로직 | React Query 활용 |
| `lib/api/` | API 호출 | Backend 연동 |

---

## 공통 규칙

### 금지 사항
- ❌ 레이어 역참조 (api/ → services/ 가능, services/ → api/ 금지)
- ❌ utils/에 비즈니스 로직 넣기
- ❌ 전역 변수 사용

### 파일 크기
- 함수: 10-30줄
- 파일: 300줄 이하 권장

---

## 관련 문서
- [CLEAN_ARCHITECTURE_GUIDE.md](CLEAN_ARCHITECTURE_GUIDE.md) - 아키텍처 원칙
- [BACKEND_SERVICE_REPOSITORY_GUIDE.md](BACKEND_SERVICE_REPOSITORY_GUIDE.md) - 백엔드 상세
- [FRONTEND_CLEAN_CODE.md](FRONTEND_CLEAN_CODE.md) - 프론트엔드 상세
