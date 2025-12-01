# Team H·P·L - Legal Evidence Hub (LEH)

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

### 4.1 사전 요구사항

- Python 3.11+
- Node.js 18+
- AWS 계정 + IAM (S3, DynamoDB 등)
- OpenAI API 키

### 4.2 레포 클론

```bash
git clone https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd.git
cd ai-camp-2nd-llm-agent-service-project-2nd
```

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
│   │   ├── services/     # 비즈니스 로직
│   │   ├── repositories/ # 데이터 접근
│   │   └── utils/        # AWS 어댑터
│   └── tests/
│
├── ai_worker/            # AI Lambda 워커 (L)
│   ├── handler.py        # Lambda 엔트리포인트
│   └── src/
│       ├── parsers/      # 파일 타입별 파서
│       ├── analysis/     # 분석 엔진
│       └── storage/      # DynamoDB, Qdrant
│
├── frontend/             # Next.js 대시보드 (P)
│   └── src/
│       ├── app/          # Next.js App Router
│       ├── components/   # React 컴포넌트
│       └── lib/          # API 클라이언트
│
├── docs/                 # 설계 문서
│   ├── specs/            # PRD, Architecture, API Spec
│   ├── guides/           # 개발 가이드
│   └── business/         # 비즈니스 문서
│
├── CLAUDE.md             # AI 에이전트 규칙
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

## 7. 문서 허브

| 카테고리 | 문서 |
|----------|------|
| **제품 요구사항** | [docs/specs/PRD.md](docs/specs/PRD.md) |
| **시스템 아키텍처** | [docs/specs/ARCHITECTURE.md](docs/specs/ARCHITECTURE.md) |
| **API 명세** | [docs/specs/API_SPEC.md](docs/specs/API_SPEC.md) |
| **환경 설정** | [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) |
| **협업 규칙** | [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) |
| **문서 인덱스** | [docs/INDEX.md](docs/INDEX.md) |

---

## 8. 최종 산출물

1. **운영 가능한 변호사 대시보드**
   - 사건 생성, 증거 업로드, 타임라인, 필터, Draft Preview

2. **AI 기반 증거 분석 파이프라인**
   - S3 Event → AI Worker → DynamoDB/Qdrant → API

3. **법적·보안 기준을 충족하는 설계**
   - 사건별 RAG 격리, Audit Log, PIPA/변호사법 대응

4. **정리된 설계 문서 & 협업 규칙**
   - PRD/Architecture/Design 문서 + GitHub CI/CD
