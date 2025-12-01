
**문서 버전**: v2.1
**최종 업데이트**: 2025-11-18
**작성자**: Team H·P·L

---

# 🧭 0. 문서 목적

본 문서는 **Legal Evidence Hub (LEH)** MVP 개발을 위한 **단일 기준 문서(Single Source of Truth)**이다.

이 문서는

* Product 정의
* 기능/비기능 요구사항
* 최신 AWS 아키텍처
* 분석 파이프라인
* Front/Back 역할
* 협업 방법
* AI 사용 정책
  모두를 하나의 문서에 통합한다.

---

# 🚀 1. Product Vision

**“변호사에게 증거 정리 시간을 90% 이상 절감시키고, 소장 초안을 3분 내 제공하는 AI 파라리걸 시스템.”**

LEH는 기존 Paralegal 시스템(PDF 기반)보다 진화하여 다음을 핵심 가치로 한다:

| 기능    | 기존 Paralegal(PDF)  | LEH(최신)                              |
| ----- | ------------------ | ------------------------------------ |
| 저장소   | S3 + Google Drive  | **S3 단일화**                           |
| 처리    | SQS Worker 기반 분석   | **S3 Event 기반 AI Worker**            |
| DB    | Postgres 중심        | **Postgres + DynamoDB + Qdrant** |
| Draft | GPT 기반 텍스트         | **사건별 RAG 기반 논리형 초안**                |
| 증거    | OCR/STT/텍스트 추출     | **유책사유·화자·감정까지 분석**                  |

---

# 🎯 2. 제품 목표 (MVP)

* **100개 증거 → 3분 내 전체 분석**
* **초안 생성 성공률 90%**
* **사건별 RAG 완전 격리(index 단위 분리)**
* **변호사는 단 2가지만 하면 됨**

  1. 사건 생성
  2. S3 업로드
* **법률사무대리 금지 준수**
  → AI는 “자동 입력”이 아닌 **Preview 제안만 제공**

---

# 🧩 3. 시스템 아키텍처 (업데이트 반영)

PDF에서 제시된 구조(React → FastAPI → S3/SQS Worker)  를 발전시켜 다음과 같이 재구성한다.

[ FE (React) ]
    ↓
[ BE (FastAPI) ]
    ↓
[ S3 Evidence Bucket ]  ← Presigned URL로 직접 업로드
    ↓ (S3 Event)
[ AI Worker (Lambda/ECS) ]
    ↓
[ DynamoDB (Evidence JSON Metadata) ]
    ↓
[ Qdrant (Case RAG Index) ]
    ↓
[ RDS/PostgreSQL (Users/Cases) ]
    ↓
[ Draft API → GPT-4o with RAG ]

### 개선 포인트

* 기존 SQS 기반 Worker는 제거하고 **S3 Event Trigger** 방식으로 단순화
* Evidence metadata는 RDS 대신 **DynamoDB**로 이전
* 벡터 스토어는 pgvector 대신 **Qdrant** 채택
* Draft 생성은 고도화된 **사건 단위 RAG** 기반

---

# 📦 4. 기능 요구사항 (Functional Requirements)

## 4.1 사건 관리

* 사건 생성/수정/삭제(종료)
* 사건 멤버(Role: Lawyer / Staff)
* 사건 종료 시:

  * Qdrant index 삭제
  * DynamoDB soft-delete
  * S3 원본은 유지(법무법인 소유 목적)

---

## 4.2 증거 업로드

### Flow

1. FE → BE: 업로드 요청
2. BE → FE: Presigned URL 발급
3. FE → S3: 파일 직접 업로드
4. S3 Event 발생
5. AI Worker 자동 실행
6. AI Worker → DynamoDB 증거 JSON 저장
7. FE 타임라인 업데이트

### 지원 포맷

* txt, pdf
* jpg, png
* mp3/m4a (Whisper)
* mp4 (음성 추출 후 분석)

---

## 4.3 AI 분석 파이프라인

### 4.3.1 텍스트 파서

PDF 기반 PRD의 텍스트 처리 흐름 그대로 발전된 버전

* 일반 txt 메시지 처리
* 카카오톡 형식 파싱(날짜/시간/화자/메시지 분리)

### 4.3.2 이미지 OCR

* GPT-4o Vision 우선
* 실패 시 Tesseract fallback
* 감정·상황·행위 라벨 포함

### 4.3.3 음성/영상 처리

* Whisper 기반 화자 분리
* 타임스탬프·상황 추출

### 4.3.4 의미 분석 (법률 도메인 강화)

민법 제840 기준 자동 태깅:

1. 부정행위
2. 악의의 유기
3. 학대
4. 유기
5. 계속적 불화
6. 3년 실종
7. 기타 중대한 사유

---

## 4.4 타임라인

* 증거 단위 시간 순 자동 정렬
* 유책사유 필터
* 논점별 증거 그룹화

---

## 4.5 RAG 검색

* 사건별 index(`case_123`)
* Qdrant vector store
* 질의 → GPT → 벡터 검색 → 상위 증거 조합

---

## 4.6 Draft Preview (AI 초안 제안)

PDF의 Paralegal Draft 기능  을 최신 형태로 고도화한다.

**기능:**

* 청구취지/청구원인 자동 구조화
* 증거 자동 인용
* “경위 → 쟁점 → 근거” 논리 전개
* Word(docx) 다운로드 제공
* FE는 “편집(√), 자동 입력(X)”

---

# 🔒 5. 비기능 요구사항

## 5.1 보안

* IAM 최소 권한
* HTTPS 전면 적용
* S3 AES-256 암호화
* 민감정보 최소 저장(Masking 처리)
* 감사 로그 필수 저장(RDS)

## 5.2 법적 컴플라이언스

* AI 단독 제출 금지 → Preview 제공
* 사건 종료 시 RAG 삭제
* 변호사 직접 확정 필요

## 5.3 성능

* 100 evidence → 3분 내 처리
* RAG 검색 1초 내
* FE 대시보드 2초 로딩

---

# 🧠 6. 데이터 모델

## DynamoDB Evidence JSON (최종)

json
{
  "evidence_id": "uuid",
  "case_id": "case123",
  "type": "text | image | audio | video | pdf",
  "timestamp": "2024-12-25T10:20:00Z",
  "speaker": "원고",
  "labels": ["학대", "폭언"],
  "summary": "...",
  "content": "...",
  "s3_key": "cases/123/evidence/abc.jpg",
  "qdrant_vector_id": "op_123"
}

## PostgreSQL (Users/Cases/Roles/Audit)

* users
* cases
* case_members
* audit_log

---

# 💻 7. Frontend 요구사항

대시보드 구성:

* 사건 리스트
* 증거 타임라인
* 증거 상세 모달
* 유책사유 필터
* Draft Preview 창
* Skeleton UI

---

# ⚙️ 8. Backend 요구사항

* FastAPI 기반
* JWT 인증
* Presigned URL 발급
* DynamoDB & Qdrant 연동
* Draft 생성 API
* 사건 종료(삭제) API

---

# 🤖 9. AI Worker 요구사항

* Python Lambda(ECS 가능)
* OCR / STT / Parsing / Embedding
* DynamoDB write
* Qdrant index write
* 오류 발생 시 DLQ 기록

---

# 📦 10. 협업 방식

## 브랜치 전략

main = 배포
develop = 통합
feature/* = 기능 단위

## 규칙

* Squash & Merge
* Reviewer 최소 1명
* PR Template 필수

---

# 🗂️ 11. 산출물

* React Dashboard
* FastAPI Backend
* AI Worker
* Qdrant RAG Index
* DynamoDB Evidence Store
* RDS(Postgres)
* docx Template 기반 Draft Generator

---

# 📌 12. 참고 문서

* Paralegal PRD(원본 PDF) 전체 문서 참고하여 기능·용어 통합
* LEH PRD_v2 (2025-11-17)

---

# 🔚 END OF PRD.md
