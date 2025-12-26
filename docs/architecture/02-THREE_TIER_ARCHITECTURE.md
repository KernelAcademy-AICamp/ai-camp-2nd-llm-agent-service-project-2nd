# 02. 3-Tier 아키텍처

> **목표**: Frontend, Backend, AI Worker가 각각 무슨 역할을 하고, 어떻게 협력하는지 이해합니다.

---

## 3-Tier 아키텍처란?

**3-Tier Architecture (3계층 아키텍처)**는 애플리케이션을 세 개의 독립적인 계층으로 나누는 설계 방식입니다.

### 왜 나누나요?

**비유**: 식당을 생각해보세요.
- **홀 서빙** (Presentation Tier): 손님과 대화하고, 주문을 받고, 음식을 가져다줌
- **주방** (Application Tier): 실제 요리를 만드는 곳
- **창고/냉장고** (Data Tier): 재료를 보관하는 곳

각 역할이 분리되어 있으면:
1. 홀 직원이 바뀌어도 요리 품질은 그대로
2. 주방 시스템이 바뀌어도 손님 경험은 그대로
3. 각 부분을 독립적으로 개선 가능

---

## LEH의 3-Tier 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Presentation Tier (표현 계층)                         │
│                                                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                      FRONTEND                                   │   │
│    │                                                                 │   │
│    │   Next.js 14 + React 18 + TypeScript + Tailwind CSS            │   │
│    │                                                                 │   │
│    │   담당: 사용자 화면, 폼 입력, 파일 업로드 UI                     │   │
│    │   호스팅: CloudFront + S3 (정적 파일)                           │   │
│    └────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    │ HTTP API                            │
│                                    ▼                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                     Application Tier (애플리케이션 계층)                   │
│                                                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                       BACKEND                                   │   │
│    │                                                                 │   │
│    │   FastAPI + Python 3.12+ + SQLAlchemy                          │   │
│    │                                                                 │   │
│    │   담당: API 제공, 비즈니스 로직, 인증/인가                       │   │
│    │   호스팅: AWS Lambda (서버리스)                                 │   │
│    └────────────────────────────────────────────────────────────────┘   │
│                    │           │           │                             │
│                    │ SQL       │ NoSQL     │ Vector                      │
│                    ▼           ▼           ▼                             │
├─────────────────────────────────────────────────────────────────────────┤
│                       Data Tier (데이터 계층)                            │
│                                                                          │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│   │  PostgreSQL  │  │   DynamoDB   │  │    Qdrant    │  │     S3     │ │
│   │    (RDS)     │  │              │  │              │  │            │ │
│   │              │  │              │  │              │  │            │ │
│   │ 사용자, 케이스│  │  증거 메타   │  │  벡터 검색   │  │  파일 저장 │ │
│   │ 드래프트 등  │  │   데이터     │  │  (RAG용)    │  │  (증거원본)│ │
│   └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                                          │
│                           + AI Worker (비동기 처리)                       │
│                                                                          │
│    ┌────────────────────────────────────────────────────────────────┐   │
│    │                      AI WORKER                                  │   │
│    │                                                                 │   │
│    │   Python 3.12+ + OpenAI (GPT-4o, Whisper)                      │   │
│    │                                                                 │   │
│    │   담당: 증거 파일 분석, OCR, STT, 임베딩 생성                   │   │
│    │   트리거: S3 파일 업로드 이벤트                                 │   │
│    │   호스팅: AWS Lambda (서버리스)                                 │   │
│    └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Frontend (표현 계층)

### 역할
- 사용자 인터페이스 (UI) 렌더링
- 사용자 입력 처리 (폼, 버튼 클릭)
- Backend API 호출
- 상태 관리 (로그인 상태, 케이스 데이터 등)

### 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| **Next.js** | 14.1 | React 프레임워크, 라우팅, SSR |
| **React** | 18.2 | UI 컴포넌트 라이브러리 |
| **TypeScript** | 5.3 | 정적 타입 체크 |
| **Tailwind CSS** | 3.4 | 유틸리티 기반 스타일링 |
| **Zustand** | - | 전역 상태 관리 |
| **TanStack Query** | - | 서버 상태 관리 (API 캐싱) |
| **React Flow** | - | 당사자 관계 그래프 시각화 |

### 배포 구조

```
사용자 브라우저
      │
      ▼
CloudFront (CDN)  ←── 전세계 엣지 서버에서 빠르게 전달
      │
      ▼
S3 Bucket (Static)  ←── Next.js 빌드 결과물 (HTML, JS, CSS)
```

**왜 S3 + CloudFront?**
- Next.js를 **Static Export** 모드로 빌드
- 서버 없이 정적 파일만으로 동작
- CDN 덕분에 전세계 어디서나 빠른 로딩

### 주요 페이지 구조

```
/                     # 메인 페이지 (로그인 안 됐으면 /login으로 리다이렉트)
/login                # 로그인 페이지
/lawyer/              # 변호사 대시보드
/lawyer/cases         # 케이스 목록
/lawyer/cases/[id]    # 케이스 상세 (증거, 초안)
/lawyer/clients       # 의뢰인 관리
/client/              # 의뢰인 포털
/staff/               # 스태프 포털
/admin/               # 관리자 포털
```

---

## 2. Backend (애플리케이션 계층)

### 역할
- REST API 제공
- 비즈니스 로직 처리 (케이스 생성, 권한 체크 등)
- 인증/인가 (JWT 토큰 검증)
- 데이터베이스 CRUD
- 외부 서비스 연동 (S3, DynamoDB, Qdrant, OpenAI)

### 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| **FastAPI** | 0.110+ | Python 웹 프레임워크 |
| **Python** | 3.11+ | 프로그래밍 언어 |
| **SQLAlchemy** | 2.0+ | ORM (DB 추상화) |
| **Alembic** | - | DB 마이그레이션 |
| **python-jose** | - | JWT 토큰 처리 |
| **boto3** | - | AWS SDK |
| **Mangum** | - | FastAPI → Lambda 어댑터 |

### 배포 구조

```
CloudFront /api/*
      │
      ▼
API Gateway (HTTP)
      │
      ▼
Lambda (leh-backend)  ←── Docker 컨테이너 이미지
      │
      ▼
RDS / DynamoDB / Qdrant / S3
```

**왜 Lambda?**
- **서버리스**: 서버 관리 불필요
- **자동 스케일링**: 요청 많으면 자동으로 인스턴스 증가
- **비용 효율**: 사용한 만큼만 과금

### API 구조

```
/api
├── /auth
│   ├── POST /login         # 로그인
│   ├── POST /register      # 회원가입
│   ├── POST /logout        # 로그아웃
│   └── GET /me             # 현재 사용자 정보
│
├── /cases
│   ├── GET /               # 케이스 목록
│   ├── POST /              # 케이스 생성
│   ├── GET /{id}           # 케이스 상세
│   ├── PATCH /{id}         # 케이스 수정
│   └── DELETE /{id}        # 케이스 삭제
│
├── /evidence
│   ├── GET /               # 증거 목록
│   ├── POST /upload-url    # S3 업로드 URL 생성
│   └── GET /{id}           # 증거 상세
│
├── /drafts
│   └── POST /preview       # 초안 미리보기 생성
│
└── /search
    └── GET /rag            # RAG 검색
```

---

## 3. AI Worker (비동기 처리)

### 역할
- 증거 파일 분석 (이미지, 오디오, 비디오, PDF, 텍스트)
- AI 분석 (OCR, STT, 요약, 라벨링)
- 임베딩 생성 및 저장 (Qdrant)
- 메타데이터 저장 (DynamoDB)

### 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.11+ | 프로그래밍 언어 |
| **OpenAI** | - | GPT-4o, Whisper, Embedding |
| **qdrant-client** | 1.7+ | 벡터 DB 연동 |
| **boto3** | - | AWS SDK |
| **Tesseract** | - | OCR (이미지 → 텍스트) |
| **PyPDF2** | - | PDF 텍스트 추출 |

### 실행 방식 (Event-Driven)

```
1. Frontend에서 파일 업로드
        │
        ▼
2. S3에 파일 저장 (cases/{case_id}/raw/{filename})
        │
        ▼
3. S3 Event가 Lambda 트리거
        │
        ▼
4. AI Worker Lambda 실행
        │
        ├──▶ 파일 다운로드 (S3)
        ├──▶ 파일 타입별 파싱
        ├──▶ AI 분석 (OpenAI)
        ├──▶ 메타데이터 저장 (DynamoDB)
        └──▶ 임베딩 저장 (Qdrant)
```

**왜 Event-Driven?**
- Backend가 AI 처리를 기다리지 않음 (비동기)
- 파일 업로드 후 즉시 응답 가능
- 대용량 파일도 타임아웃 없이 처리

### 파일 타입별 처리

| 확장자 | 파서 | 처리 내용 |
|--------|------|----------|
| `.jpg`, `.png` | ImageVisionParser | GPT-4o Vision으로 이미지 분석 |
| `.pdf` | PDFParser | 텍스트 추출 + OCR 폴백 |
| `.mp3`, `.wav` | AudioParser | Whisper로 음성 → 텍스트 |
| `.mp4`, `.avi` | VideoParser | 오디오 추출 → Whisper |
| `.txt`, `.csv` | TextParser | 카카오톡 대화 포맷 감지 |

---

## 4. Data Tier (데이터 계층)

### PostgreSQL (RDS)
**용도**: 정형 데이터 (트랜잭션 필요)

저장 데이터:
- Users (사용자)
- Cases (케이스)
- CaseMembers (케이스 멤버)
- Drafts (초안)
- AuditLogs (감사 로그)

### DynamoDB
**용도**: 증거 메타데이터 (빠른 읽기/쓰기)

저장 데이터:
```json
{
  "case_id": "case_123",
  "evidence_id": "ev_456",
  "type": "image",
  "timestamp": "2024-01-15T10:30:00Z",
  "speaker": "원고",
  "labels": ["폭언", "불륜"],
  "ai_summary": "AI가 분석한 요약",
  "s3_key": "cases/123/raw/photo.jpg"
}
```

### Qdrant
**용도**: 벡터 유사도 검색 (RAG)

저장 데이터:
- 증거 텍스트의 임베딩 벡터
- 케이스별 격리된 컬렉션 (`case_rag_{case_id}`)

### S3
**용도**: 파일 저장 (증거 원본)

저장 구조:
```
s3://leh-evidence/
└── cases/
    └── {case_id}/
        └── raw/
            ├── photo1.jpg
            ├── audio1.mp3
            └── document1.pdf
```

---

## 컴포넌트 간 통신 요약

```
┌──────────────┐     HTTP/REST     ┌──────────────┐
│   Frontend   │ ◀──────────────▶  │   Backend    │
│  (Next.js)   │    (JSON API)     │  (FastAPI)   │
└──────────────┘                   └──────────────┘
       │                                  │
       │ S3 Presigned URL                 │ SQL/NoSQL/Vector
       │ (Direct Upload)                  │
       ▼                                  ▼
┌──────────────┐                   ┌──────────────┐
│      S3      │ ───S3 Event────▶  │  AI Worker   │
│  (파일저장)   │                   │  (Lambda)    │
└──────────────┘                   └──────────────┘
                                          │
                                          │ 분석 결과 저장
                                          ▼
                           ┌──────────────────────────────┐
                           │  DynamoDB     │    Qdrant    │
                           │  (메타데이터)  │  (임베딩)    │
                           └──────────────────────────────┘
```

---

## 핵심 특징

### 1. Stateless Backend
- Backend 서버는 상태를 저장하지 않음
- 모든 데이터는 외부 저장소에 저장
- Lambda가 여러 개 실행되어도 문제 없음

### 2. Event-Driven AI Processing
- AI 처리는 S3 이벤트로 트리거
- Backend가 AI 처리 완료를 기다리지 않음
- 비동기 처리로 응답 속도 향상

### 3. Case Isolation
- 각 케이스는 완전히 격리됨
- Qdrant 컬렉션도 케이스별로 분리 (`case_rag_{case_id}`)
- 다른 케이스 데이터 접근 불가

### 4. Direct Upload
- 파일은 Frontend → S3로 직접 업로드
- Backend는 Presigned URL만 제공
- 대용량 파일도 Backend 부하 없이 처리

---

**다음 문서**: [03. 백엔드 패턴](03-BACKEND_PATTERNS.md) - Clean Architecture와 Dependency Injection 패턴을 알아봅니다.
