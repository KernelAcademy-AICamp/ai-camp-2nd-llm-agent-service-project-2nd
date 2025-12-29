# Team H·P·L - Legal Evidence Hub (LEH)

> **KernelAcademy AI Camp 2기 - LLM Agent Service Project**

---

## 프로젝트 소개

**Legal Evidence Hub (LEH)**는 이혼 사건 전용 AI 파라리걸 & 증거 허브 플랫폼입니다.

> "변호사는 사건만 생성하고 증거를 S3에 올린다.
> AI는 AWS 안에서 증거를 정리·분석해 '소장 초안 후보'를 보여준다.
> 최종 문서는 언제나 변호사가 직접 결정한다."

### 해결하는 문제

| 기존 문제 | LEH 솔루션 |
|-----------|-----------|
| 카톡/이메일/USB로 중구난방 도착 | S3 Presigned URL 업로드 |
| 수작업 정리 1~2주 소요 | AI 자동 분석 파이프라인 |
| 중요 증거 누락·오용 리스크 | 구조화된 타임라인 & 필터 |
| 증거 무결성(해시, Chain of Custody) 부담 | SHA-256 + Audit Log |

---

## 팀 구성

| 역할 | 담당자 | GitHub | 주요 책임 |
|:-----|:-------|:-------|:----------|
| **Backend / Infra** | H | [@leaf446](https://github.com/leaf446) | FastAPI, RDS, S3, 인증·권한, 증거 무결성, 배포 파이프라인 |
| **AI / Data** | L | [@vsun410](https://github.com/vsun410) | AI Worker, STT/OCR, 파서, 요약·라벨링, 임베딩·RAG |
| **Frontend / PM** | P | [@x-ordo](https://github.com/x-ordo) | Next.js 대시보드, UX, GitHub 운영, 문서 관리, PR 승인 |

### 기여 통계

| 기여자 | 커밋 수 |
|--------|---------|
| x-ordo | 206 |
| vsun410 | 180 |
| leaf446 | 141 |
| HSP | 100 |
| tae yeon | 81 |

---

## 기술 스택

| 영역 | 기술 |
|:-----|:-----|
| **Frontend** | Next.js 14, TypeScript, React 18, Tailwind CSS |
| **Backend** | FastAPI, Python 3.12+ |
| **Database** | PostgreSQL (RDS), DynamoDB |
| **Storage** | AWS S3 |
| **Vector DB** | Qdrant (RAG) |
| **AI** | OpenAI GPT-4o, Whisper, Vision |
| **CDN** | CloudFront |
| **CI/CD** | GitHub Actions |

---

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                           AWS Cloud                                  │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │ CloudFront│───▶│  Next.js  │    │  FastAPI  │◀──▶│ PostgreSQL│  │
│  │   (CDN)   │    │ (Frontend)│───▶│ (Backend) │    │   (RDS)   │  │
│  └───────────┘    └───────────┘    └─────┬─────┘    └───────────┘  │
│                                          │                          │
│                                          ▼                          │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │    S3     │───▶│  Lambda   │───▶│ DynamoDB  │    │  Qdrant   │  │
│  │ (Evidence)│    │(AI Worker)│    │ (Metadata)│    │   (RAG)   │  │
│  └───────────┘    └─────┬─────┘    └───────────┘    └───────────┘  │
│                         │                                           │
│                         ▼                                           │
│                   ┌───────────┐                                     │
│                   │  OpenAI   │                                     │
│                   │(GPT/STT)  │                                     │
│                   └───────────┘                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **증거 업로드**: 변호사 → Presigned URL → S3
2. **AI 분석**: S3 Event → Lambda (AI Worker) → OCR/STT/요약
3. **메타데이터 저장**: AI Worker → DynamoDB + Qdrant (임베딩)
4. **초안 생성**: Backend → RAG 검색 → GPT-4o → Draft Preview

---

## 주요 기능

### 변호사 대시보드
- 사건 생성 및 관리
- 증거 업로드 (이미지, 오디오, 비디오, PDF, 텍스트)
- 증거 타임라인 및 필터링
- 소장/준비서면 초안 미리보기

### AI 증거 분석
- **OCR**: 이미지/PDF 텍스트 추출
- **STT**: 음성/영상 자동 전사
- **요약**: 증거별 핵심 내용 요약
- **라벨링**: 민법 840조 기반 유책사유 태깅
- **RAG**: 사건별 증거 임베딩 및 검색

### 법적 준수
- SHA-256 해시 기반 증거 무결성
- Chain of Custody 관리
- 감사 로그 (Audit Trail)
- 사건별 데이터 격리

---

## 프로젝트 기간

**2024년 11월 ~ 2025년 1월** (약 3개월)

- Sprint 1-2: 기획 및 설계
- Sprint 3-4: 핵심 기능 개발
- Sprint 5-6: AI 파이프라인 구축
- Sprint 7-8: 통합 및 최적화

---

## 라이선스

**랜딩 페이지 (이 저장소)**: MIT License - 교육 목적으로 자유롭게 사용 가능

**전체 시스템 (Backend, AI Worker, Dashboard)**: Business License - All Rights Reserved
- 실제 운영 시스템의 소스 코드는 비공개이며 비즈니스 라이선스로 보호됩니다.

---

## 문의

프로젝트 관련 문의는 팀원들에게 연락해 주세요.

- H (Backend): [@leaf446](https://github.com/leaf446)
- L (AI): [@vsun410](https://github.com/vsun410)
- P (Frontend/PM): [@x-ordo](https://github.com/x-ordo)
