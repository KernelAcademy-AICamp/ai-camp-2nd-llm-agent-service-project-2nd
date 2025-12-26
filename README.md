# Team H·P·L - Legal Evidence Hub (LEH)

[![CI](https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/actions/workflows/ci.yml/badge.svg)](https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/actions/workflows/ci.yml)
[![Deploy](https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/actions/workflows/deploy_paralegal.yml/badge.svg)](https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/actions/workflows/deploy_paralegal.yml)

**Test Coverage:** Backend 81% | AI Worker 78% | Frontend ~30%

> "변호사는 사건만 생성하고 증거를 S3에 올린다.
> AI는 AWS 안에서 증거를 정리·분석해 '소장 초안 후보'를 보여준다.
> 최종 문서는 언제나 변호사가 직접 결정한다."

LEH는 **이혼 사건 전용 AI 파라리걸 & 증거 허브** 플랫폼입니다.

---

## 1. 팀 구성 & 역할

| 코드 | 역할 | 주요 책임 |
|:-----|:-----|:----------|
| H | **Backend / Infra** | FastAPI, RDS, S3, 인증·권한, 증거 무결성, 배포 파이프라인 |
| L | **AI / Data** | AI Worker, STT/OCR, 파서, 요약·라벨링, 임베딩·RAG |
| P | **Frontend / PM** | Next.js 대시보드, UX, GitHub 운영, 문서 관리, PR 승인 |

---

## 2. 프로젝트 개요

### 2.1 한 줄 요약

> **"AWS 안에서 끝나는 이혼 사건 전용 AI 파라리걸 & 증거 허브"**

- 증거는 **변호사 소유 AWS S3**에만 저장
- AI는 증거를 **정리·요약·라벨링·임베딩**
- 변호사에게는 **"소장/준비서면 초안 후보(Preview)"**만 제안

### 2.2 해결하는 문제

| 기존 문제 | LEH 솔루션 |
|-----------|-----------|
| 카톡/이메일/USB로 중구난방 도착 | S3 Presigned URL 업로드 |
| 수작업 정리 1~2주 소요 | AI 자동 분석 파이프라인 |
| 중요 증거 누락·오용 리스크 | 구조화된 타임라인 & 필터 |
| 증거 무결성(해시, Chain of Custody) 부담 | SHA-256 + Audit Log |

---

## 3. 기술 스택

| 영역 | 기술 | 설명 |
|:-----|:-----|:-----|
| Frontend | **Next.js 14, TypeScript, Tailwind** | 변호사/스태프용 대시보드 |
| Backend | **FastAPI, Python** | 인증, 사건/증거/Draft API |
| RDB | **PostgreSQL (RDS) / SQLite** | 사용자, 사건, 권한, 감사 로그 |
| Evidence Storage | **AWS S3** | 원본 증거 저장소 |
| Metadata | **AWS DynamoDB** | 증거 분석 결과 JSON |
| RAG | **Qdrant** | 사건별 임베딩 인덱스 |
| AI | **OpenAI (GPT-4o, Whisper, Vision)** | OCR/STT/요약/라벨링/초안 생성 |
| CDN | **CloudFront** | Frontend 배포 |

> Google Drive는 사용하지 않으며, 모든 데이터는 **단일 AWS 계정 내부**에서만 저장·처리됩니다.

---

## 4. 시작하기 (Getting Started)

### 4.1 Quick Start (원클릭 설정)

```bash
# 1. 레포 클론
git clone https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd.git
cd ai-camp-2nd-llm-agent-service-project-2nd

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 필수 값 입력

# 3. 전체 설정 (Makefile 사용)
make setup

# 4. 개발 서버 실행 (각각 별도 터미널)
make dev-backend   # http://localhost:8000
make dev-frontend  # http://localhost:3000
```

> **Makefile 명령어 전체 보기**: `make help`

### 4.2 사전 요구사항

- Python 3.12+
- Node.js 18+
- AWS 계정 + IAM (S3, DynamoDB 등)
- OpenAI API 키

### 4.3 환경 변수 설정

LEH는 **통합 `.env` 파일**을 사용합니다:

```bash
# 템플릿 복사
cp .env.example .env

# 필수 값 편집
# - OPENAI_API_KEY
# - AWS_REGION, S3_EVIDENCE_BUCKET
# - DATABASE_URL
# - JWT_SECRET
```

> `.env`는 절대 Git에 커밋하지 않습니다.

### 4.4 백엔드 실행 (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
```

### 4.5 프론트엔드 실행 (Next.js)

```bash
cd frontend
npm install
npm run dev
# http://localhost:3000
```

### 4.6 AI Worker 실행 (로컬 테스트)

```bash
cd ai_worker
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m handler
```

---

## 5. 레포 구조

```
/
├── .env                  # 통합 환경 변수 (Git 제외)
├── .env.example          # 환경 변수 템플릿
│
├── backend/              # FastAPI 백엔드 (H)
│   ├── app/
│   │   ├── api/          # 라우터 (auth, cases, evidence, admin)
│   │   ├── core/         # 설정, 보안, 의존성
│   │   ├── db/           # DB 연결, 세션
│   │   ├── middleware/   # 보안, 로깅, 에러 핸들링
│   │   ├── models/       # SQLAlchemy 모델
│   │   ├── schemas/      # Pydantic 스키마
│   │   ├── services/     # 비즈니스 로직
│   │   ├── repositories/ # 데이터 접근
│   │   └── utils/        # AWS 어댑터 (S3, DynamoDB, Qdrant)
│   └── tests/
│
├── ai_worker/            # AI Lambda 워커 (L)
│   ├── handler.py        # Lambda 엔트리포인트
│   └── src/
│       ├── parsers/      # 파일 타입별 파서 (PDF, 이미지, 오디오, 카카오톡)
│       ├── analysis/     # 분석 엔진 (요약, 점수, 840조 태깅)
│       ├── storage/      # DynamoDB, Qdrant 저장소
│       ├── service_rag/  # 법률 지식 RAG
│       ├── user_rag/     # 사건별 증거 RAG
│       └── utils/        # 임베딩, 로깅 유틸
│
├── frontend/             # Next.js 대시보드 (P)
│   └── src/
│       ├── app/          # Next.js App Router
│       ├── components/   # React 컴포넌트
│       ├── hooks/        # 커스텀 React Hooks
│       ├── lib/          # API 클라이언트
│       ├── services/     # 비즈니스 로직
│       └── types/        # TypeScript 타입
│
├── docs/                 # 설계 문서
│   ├── specs/            # PRD, Architecture, API Spec
│   ├── guides/           # 개발 가이드
│   └── business/         # 비즈니스 문서
│
├── CLAUDE.md             # AI 에이전트 규칙
├── Makefile              # 개발 자동화 스크립트
└── README.md             # 이 파일
```

---

## 6. 협업 방식

> 상세 규칙은 **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** 참고

### 6.1 브랜치 전략

```
main  ←  dev  ←  feat/*
```

- **main**: 배포 가능한 상태, PR로만 변경
- **dev**: 통합 개발 브랜치, 자유롭게 push
- **feat/***: 작업용 브랜치

### 6.2 PR 규칙

- 방향: **항상 `dev → main`**
- 최소 1명 리뷰 필수
- 문서만 수정하는 경우 main 직접 push 허용

---

## 7. 최근 업데이트 (2025-12-12)

- **URL 기반 모달/폼 UX**: Billing·Calendar 페이지가 `useModalState`로 전환되어 뒤로가기와 딥링크가 모두 작동합니다. InvoiceForm/EventForm에는 `useBeforeUnload`가 적용돼 입력값 유실을 방지합니다.
- **Landing/Login 네비게이션 통합**: `LandingNav`를 로그인 화면에서도 재사용하고 인증 상태를 주입해 로그인 사용자는 즉시 로그아웃할 수 있습니다.
- **문서 동기화**: `docs/IMPLEMENTATION_STATUS.md`와 본 README에 현행 스프린트 정보가 정리돼 있습니다.

---

## 8. 문서 허브

| 카테고리 | 문서 |
|----------|------|
| **제품 요구사항** | [docs/specs/PRD.md](docs/specs/PRD.md) |
| **시스템 아키텍처** | [docs/specs/ARCHITECTURE.md](docs/specs/ARCHITECTURE.md) |
| **API 명세** | [docs/specs/API_SPEC.md](docs/specs/API_SPEC.md) |
| **환경 설정** | [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) |
| **협업 규칙** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| **유지보수 가이드** | [docs/guides/MAINTENANCE_GUIDE.md](docs/guides/MAINTENANCE_GUIDE.md) |
| **문서 인덱스** | [docs/INDEX.md](docs/INDEX.md) |

---

## 9. 최종 산출물

1. **운영 가능한 변호사 대시보드**
   - 사건 생성, 증거 업로드, 타임라인, 필터, Draft Preview

2. **AI 기반 증거 분석 파이프라인**
   - S3 Event → AI Worker → DynamoDB/Qdrant → API

3. **법적·보안 기준을 충족하는 설계**
   - 사건별 RAG 격리, Audit Log, PIPA/변호사법 대응

4. **정리된 설계 문서 & 협업 규칙**
   - PRD/Architecture/Design 문서 + GitHub CI/CD
