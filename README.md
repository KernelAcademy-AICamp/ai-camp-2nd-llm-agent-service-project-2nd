# Team H·P·L 🤖 Legal Evidence Hub (LEH) – AI 파라리걸 & 증거 허브

> “변호사는 사건만 생성하고 증거를 S3에 올린다.  
> AI는 AWS 안에서 증거를 정리·분석해 ‘소장 초안 후보’를 보여준다.  
> 최종 문서는 언제나 변호사가 직접 결정한다.”

LEH 레포지토리는 위 비전을 **AWS 단일 인프라** 위에서 구현하기 위한  
PRD, 아키텍처, 설계 문서, 코드, 그리고 협업 규칙을 한 번에 담고 있다.

---

## 1. 👥 팀 구성 & 역할

### 1.1 팀원 역할

| 코드 | 역할 | 주요 책임 |
| :--- | :--- | :--- |
| H | **Backend / Infra** | FastAPI, RDS, S3, 인증·권한, 증거 무결성, 배포 파이프라인 |
| L | **AI / Data** | AI Worker, STT/OCR, 파서, 요약·라벨링, 임베딩·RAG |
| P | **Frontend / PM** | React 대시보드, UX, GitHub 운영, 문서 관리, PR 승인 |

---

## 2. 🎯 프로젝트 개요

### 2.1 한 줄 요약

> **“AWS 안에서 끝나는 이혼 사건 전용 AI 파라리걸 & 증거 허브”**

- 증거는 **변호사 소유 AWS S3**에만 저장
- AI는 증거를 **정리·요약·라벨링·임베딩**하고
- 변호사에게는 **“소장/준비서면 초안 후보(Preview)”**만 제안

### 2.2 해결하는 문제

기존 로펌/법무법인의 증거 처리 현실:

- 카톡 캡처, 녹취, 사진, PDF가 **카톡/이메일/USB**로 중구난방 도착
- **수작업 정리 1~2주**, 중요한 증거 누락·오용 리스크
- 개인정보보호법·AI 규제·증거 무결성(해시, Chain of Custody) 부담

**LEH가 제공하는 것**

1. **증거 적재**
   - 웹 대시보드에서 사건 생성 → **S3 Presigned URL**로 증거 업로드
   - 모든 원본은 지정된 **S3 Evidence Bucket**에만 저장

2. **AI 분석 (L)**
   - S3 Event → AI Worker 자동 실행
   - 텍스트·이미지·오디오·영상·PDF를 타입별 파서로 처리
   - **DynamoDB / OpenSearch / RDS**에 구조화 + 임베딩 저장

3. **대시보드 (P)**
   - 사건별 **증거 타임라인**
   - 유책사유·유형·날짜 필터
   - **소장 초안 Preview**(증거 인용 포함) 제공  
   - 자동 제출/자동 입력은 **금지** (법률사무대리 방지)

4. **백엔드 (H)**
   - 인증/인가, 증거 업로드 URL 발급, 메타 조회 API
   - 사건별 RAG 검색 API, Draft Preview API
   - SHA-256, Audit Log 등 **법적 무결성 기반** 구현

---

## 3. 🛠 기술 스택

| 영역 | 기술 | 설명 |
| :--- | :--- | :--- |
| Frontend | **React (Next/Vite), TypeScript, Tailwind** | 변호사/스태프용 대시보드 |
| Backend | **FastAPI, Python** | 인증, 사건/증거/Draft API, Presigned URL, RAG |
| RDB | **PostgreSQL (RDS)** | 사용자, 사건, 권한, 감사 로그 |
| Evidence Storage | **AWS S3** | 원본 증거 저장소 |
| Metadata | **AWS DynamoDB** | 증거 분석 결과 JSON, 타임라인 메타 |
| RAG | **Amazon OpenSearch** | 사건별 임베딩 인덱스(`case_rag_{case_id}`) |
| Queue | **S3 Event / (옵션 SQS)** | AI Worker 트리거 |
| AI | **OpenAI (GPT-4o, Whisper, Vision, Embedding)** | OCR/STT/요약/라벨링/초안 생성 |
| Observability | **CloudWatch, (옵션 Sentry)** | 로그·모니터링 |

> Google Drive는 사용하지 않으며, 모든 데이터는 **단일 AWS 계정 내부**에서만 저장·처리된다.

---

## 3. 🛠 기술 스택

### 4.1 사전 요구사항

- Python 3.11+
- Node.js 20+
- AWS 계정 + IAM (S3, DynamoDB, OpenSearch, RDS 등)
- OpenAI API 키
- PostgreSQL 인스턴스 (RDS 또는 로컬)

### 4.2 레포 클론

bash
git clone `https://github.com/ORG/REPO.git`
cd REPO
`

### 4.3 환경 변수 설정

1. 템플릿 복사

bash
cp .env.example .env


2. 필수 값 설정 (예시)

- `S3_EVIDENCE_BUCKET`
- `DDB_EVIDENCE_TABLE`
- `OPENSEARCH_HOST`
- `DATABASE_URL` (또는 POSTGRES_* 세트)
- `OPENAI_API_KEY`
- 기타 AWS 자격 증명 또는 IAM Role 사용 방식

`.env`는 절대 Git에 커밋하지 않는다.

---

### 4.4 백엔드 실행 (FastAPI)

bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# (선택) DB 마이그레이션
# alembic upgrade head

uvicorn backend.main:app --reload
# 기본: `http://localhost:8000`


---

### 4.5 AI 워커 실행 (AI Worker)

bash
cd ai_worker  # 실제 디렉토리명에 맞춰 수정

# 같은 venv를 사용한다고 가정
python -m worker.main  # 또는
python worker/main.py


- S3 Event / SQS 메시지를 받아:

  - S3에서 파일 다운로드
  - 타입별 파서 실행 (텍스트/이미지/오디오/영상/PDF)
  - 요약/라벨링/임베딩 생성
  - DynamoDB + OpenSearch에 결과 반영

---

### 4.6 프론트엔드 실행 (React)

bash
cd frontend
npm install
npm run dev   # 기본: `http://localhost:5173`


- `.env` 내 `VITE_API_BASE_URL`(또는 NEXT_PUBLIC_API_BASE_URL)이 FastAPI 주소와 일치해야 한다.
| 영역 | 기술 | 설명 |
| :--- | :--- | :--- |
| Frontend | **React (Next/Vite), TypeScript, Tailwind** | 변호사/스태프용 대시보드 |
| Backend | **FastAPI, Python** | 인증, 사건/증거/Draft API, Presigned URL, RAG |
| RDB | **PostgreSQL (RDS)** | 사용자, 사건, 권한, 감사 로그 |
| Evidence Storage | **AWS S3** | 원본 증거 저장소 |
| Metadata | **AWS DynamoDB** | 증거 분석 결과 JSON, 타임라인 메타 |
| RAG | **Amazon OpenSearch** | 사건별 임베딩 인덱스(`case_rag_{case_id}`) |
| Queue | **S3 Event / (옵션 SQS)** | AI Worker 트리거 |
| AI | **OpenAI (GPT-4o, Whisper, Vision, Embedding)** | OCR/STT/요약/라벨링/초안 생성 |
| Observability | **CloudWatch, (옵션 Sentry)** | 로그·모니터링 |

> Google Drive는 사용하지 않으며, 모든 데이터는 **단일 AWS 계정 내부**에서만 저장·처리된다.

---

## 4. 🚀 시작하기 (Getting Started)

### 4.1 사전 요구사항

- Python 3.11+
- Node.js 20+
- AWS 계정 + IAM (S3, DynamoDB, OpenSearch, RDS 등)
- OpenAI API 키
- PostgreSQL 인스턴스 (RDS 또는 로컬)

### 4.2 레포 클론

```bash
git clone `https://github.com/ORG/REPO.git`
cd REPO
````

### 4.3 환경 변수 설정

1. 템플릿 복사

```bash
cp .env.example .env
```

2. 필수 값 설정 (예시)

- `S3_EVIDENCE_BUCKET`
- `DDB_EVIDENCE_TABLE`
- `OPENSEARCH_HOST`
- `DATABASE_URL` (또는 POSTGRES_* 세트)
- `OPENAI_API_KEY`
- 기타 AWS 자격 증명 또는 IAM Role 사용 방식

`.env`는 절대 Git에 커밋하지 않는다.

---

### 4.4 백엔드 실행 (FastAPI)

```bash
cd backend

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# (선택) DB 마이그레이션
# alembic upgrade head

uvicorn backend.main:app --reload
# 기본: http://localhost:8000
```

---

### 4.5 AI 워커 실행 (AI Worker)

```bash
cd ai_worker  # 실제 디렉토리명에 맞춰 수정

# 같은 venv를 사용한다고 가정
python -m worker.main  # 또는
python worker/main.py
```

- S3 Event / SQS 메시지를 받아:

  - S3에서 파일 다운로드
  - 타입별 파서 실행 (텍스트/이미지/오디오/영상/PDF)
  - 요약/라벨링/임베딩 생성
  - DynamoDB + OpenSearch에 결과 반영

---

## 5. 📁 레포 구조 (요약)

bash
/
├── backend/                 # FastAPI 백엔드 (H 리드)
│   ├── main.py
│   ├── api/                # cases, evidence, auth, draft, search 등
│   ├── models/             # SQLAlchemy 모델
│   ├── schemas/            # Pydantic 스키마
│   ├── services/           # S3/DynamoDB/OpenSearch/Auth 등
│   └── core/               # 설정, 로깅, 보안
│
├── ai_worker/               # AI 파이프라인 워커 (L 리드)
│   ├── handler.py          # Lambda 엔트리포인트
│   ├── processor/          # router, text_parser, ocr, stt, semantic, embed 등
│   └── utils/              # s3, dynamo, opensearch 유틸
│
├── frontend/                # React/Next 대시보드 (P 리드)
│   └── src/
│       ├── pages/          # index, cases, cases/[id], settings
│       ├── components/     # layout, evidence, cases, draft, common
│       ├── hooks/          # useAuth, useCase, useEvidence, useDraft
│       ├── api/            # client, cases, evidence, draft
│       └── types/          # case, evidence, draft
│
├── infra/                   # IaC (CDK/Terraform) – 선택
├── docs/                    # 설계 문서
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── BACKEND_DESIGN.md
│   ├── AI_PIPELINE_DESIGN.md
│   ├── FRONTEND_SPEC.md
│   ├── API_SPEC.md
│   └── SECURITY_COMPLIANCE.md
│
├── .github/
│   ├── ISSUE_TEMPLATE/      # 버그/기능/태스크 템플릿
│   ├── pull_request_template.md
│   └── workflows/           # CI 설정
│
├── .env.example
├── CONTRIBUTING.md          # GitHub 협업 규칙 (필독)
├── requirements.txt
└── README.md                # 본 문서


---

### 4.6 프론트엔드 실행 (React)

```bash
cd frontend
npm install
npm run dev   # 기본: http://localhost:5173
```

- `.env` 내 `VITE_API_BASE_URL`(또는 NEXT_PUBLIC_API_BASE_URL)이 FastAPI 주소와 일치해야 한다.

---

## 5. 📁 레포 구조 (요약)

```bash
/
├── backend/                 # FastAPI 백엔드 (H 리드)
│   ├── main.py
│   ├── api/                # cases, evidence, auth, draft, search 등
│   ├── models/             # SQLAlchemy 모델
│   ├── schemas/            # Pydantic 스키마
│   ├── services/           # S3/DynamoDB/OpenSearch/Auth 등
│   └── core/               # 설정, 로깅, 보안
│
├── ai_worker/               # AI 파이프라인 워커 (L 리드)
│   ├── handler.py          # Lambda 엔트리포인트
│   ├── processor/          # router, text_parser, ocr, stt, semantic, embed 등
│   └── utils/              # s3, dynamo, opensearch 유틸
│
├── frontend/                # React/Next 대시보드 (P 리드)
│   └── src/
│       ├── pages/          # index, cases, cases/[id], settings
│       ├── components/     # layout, evidence, cases, draft, common
│       ├── hooks/          # useAuth, useCase, useEvidence, useDraft
│       ├── api/            # client, cases, evidence, draft
│       └── types/          # case, evidence, draft
│
├── infra/                   # IaC (CDK/Terraform) – 선택
├── docs/                    # 설계 문서
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── BACKEND_DESIGN.md
│   ├── AI_PIPELINE_DESIGN.md
│   ├── FRONTEND_SPEC.md
│   ├── API_SPEC.md
│   └── SECURITY_COMPLIANCE.md
│
├── .github/
│   ├── ISSUE_TEMPLATE/      # 버그/기능/태스크 템플릿
│   ├── pull_request_template.md
│   └── workflows/           # CI 설정
│
├── .env.example
├── CONTRIBUTING.md          # GitHub 협업 규칙 (필독)
├── requirements.txt
└── README.md                # 본 문서
```

---

## 6. 🔁 협업 방식 (요약)

> 상세 규칙은 **`CONTRIBUTING.md`** 참고. 아래는 핵심 요약만 적는다.

### 6.1 브랜치 전략

text
main  ←  dev  ←  feat/*


- **main**

  - 항상 배포 가능한 상태
  - 직접 push 금지
  - **오직 PR(dev → main)**로만 변경

- **dev**

  - 통합 개발 브랜치
  - H/L/P 모두 자유롭게 push 가능 (테스트 통과를 전제)
  - 대규모 리팩토링/AI Vibe Coding 등도 dev에서 진행

- **feat/***

  - 필요할 때만 사용하는 작업용 브랜치
  - 예: `feat/parser-unify`, `feat/ai-routing-v2`
  - 작업 완료 후 dev에 merge, 브랜치 삭제 가능

- **문서-only 예외**

  - `docs/*.md`, `CONTRIBUTING.md`, `README.md` 등 **문서만 수정**하는 경우
    → main에 직접 push 허용 (코드 변경 포함 시 반드시 PR)

### 6.2 PR 규칙 (요약)

- 방향: **항상 `dev → main`**
- 최소 1명 리뷰 (기본 승인자: P 또는 지정된 Owner)
- PR 템플릿 필수 사용:

  - Summary / Changed Files / Impact / Testing 간단히 기입

---

## 7. 📚 문서 허브

- **제품 요구사항** → `docs/specs/PRD.md`
- **시스템 아키텍처** → `docs/specs/ARCHITECTURE.md`
- **기술 설계 (BE/FE/AI)** → `docs/specs/*_DESIGN.md`
- **운영/비즈니스 (New)** → `docs/business/`, `infra/docs/RUNBOOK.md`
- **법적 고지 (New)** → `docs/legal/TERMS_AND_PRIVACY.md`
- **Git 협업 규칙** → `docs/guides/CONTRIBUTING.md`

---

## 8. 🏁 최종 산출물

1. **운영 가능한 변호사 대시보드**

   - 사건 생성, 증거 업로드, 타임라인, 필터, Draft Preview

2. **AI 기반 증거 분석 파이프라인**

   - S3 Event → AI Worker → DynamoDB/OpenSearch/RDS → API

3. **법적·보안 기준을 충족하는 설계**

   - 사건별 RAG 격리, Audit Log, PIPA/변호사법 대응

4. **정리된 설계 문서 & 협업 규칙**

   - PRD/Architecture/Design 문서 + GitHub 템플릿/CI
