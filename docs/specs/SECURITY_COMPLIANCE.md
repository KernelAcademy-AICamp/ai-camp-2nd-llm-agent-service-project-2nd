
### *보안 아키텍처 · 법적 준수 · 개인정보 보호 정책*

**버전:** v2.0  
**작성일:** 2025-11-18  
**작성자:** Team H · P · L  
**관련 문서:**  
`PRD.md`, `ARCHITECTURE.md`, `BACKEND_DESIGN.md`, `AI_PIPELINE_DESIGN.md`, `FRONTEND_SPEC.md`, `API_SPEC.md`

---

# 📌 0. 문서 목적

본 문서는 LEH(Legal Evidence Hub)의 **보안(Security)** 및 **법적 준수(Compliance)** 기준을 정의한다.

- 사건/증거 데이터의 기밀성(Confidentiality)  
- 변호사 의뢰인 정보 보호(Personal Data Protection)  
- 법률사무대리 금지 준수  
- 파일/데이터 접근 제어  
- AI 출력의 법적 기준  
- AWS 인프라 보안 메커니즘  

LEH는 **변호사가 사용하는 사건 관리 플랫폼**이므로,  
모든 보안 규칙은 **한국 법률시장·이혼 소송 데이터 특수성**을 기준으로 설계된다.

---

# 🧭 1. 보안 기본 원칙 (Security Principles)

### ✔ 1. 최소 권한 원칙(Least Privilege)

- 모든 IAM Role/S3 Policy/DB 권한은 “필요한 최소 기능”만 허용한다.

### ✔ 2. Zero Trust 접근  

- FE → BE 모든 요청: JWT 인증 필수  
- 백엔드 → AWS 서비스: IAM 기반 Role Only  
- 외부 네트워크에서 Qdrant/DynamoDB 직접 접근 **불가**

### ✔ 3. 민감정보의 **저장 최소화**

- 민감한 원문 데이터는 S3 원본 파일에만 존재  
- FE/BE/로그/Analytics 어디에도 전문 저장 금지

### ✔ 4. 암호화(Encryption Everywhere)

- 저장: KMS 기반 AES-256  
- 전송: HTTPS(TLS 1.2 이상) 강제  
- JWT: 강한 Secret + 24h TTL

### ✔ 5. AI는 법률사무를 **대체하지 않는다**

- AI가 생성하는 Draft는 “표현 제안(초안)”이며 자동 제출 금지  
- 변호사가 직접 편집 → 제출해야 법적 효력 발생

---

# 🛡 2. 인프라 보안 (AWS Security)

LEH는 AWS 환경에서 동작하며, 모든 구성 요소는 VPC 내부에서 보호된다.

## 2.1 네트워크

- **VPC Private Subnet**:  
  - Backend (Lambda/ECS)  
  - AI Worker (Lambda/ECS)  
  - RDS(Postgres)  
  - DynamoDB (VPC Endpoint)  
  - Qdrant (VPC Only)

- **Public Subnet**:  
  - CloudFront → S3 Static Hosting  
  - API Gateway/ALB (Backend 진입 지점)

## 2.2 IAM 정책

### Backend IAM Role

- S3 `GetObject` (download-only for processed/)  
- DynamoDB `Query`/`GetItem`  
- Qdrant HTTP request (index-level)

### AI Worker IAM Role

- S3 `GetObject` / `PutObject`  
- DynamoDB `PutItem` / `UpdateItem`  
- Qdrant `index/write`  
- CloudWatch Logs write

> AI Worker만 증거 메타데이터를 변경할 수 있다 (BE는 Read-Only).

## 2.3 로그 & 모니터링

- CloudWatch Logs (Backend/Lambda)  
- AWS WAF + Shield (선택)  
- API Gateway Access Log  
- 알람(Alarm):  
  - 5xx 증가  
  - Lambda 오류  
  - Qdrant cluster health red  

---

# 🔐 3. 데이터 보안(Data Security)

## 3.1 데이터 종류 분류

| 데이터 유형 | 보관 위치 | 보안 요구사항 |
|-------------|-----------|----------------|
| 사건 메타 | PostgreSQL | 암호화 + RBAC |
| 증거 원본 (이미지/문서/음성) | **S3(raw/)** | SSE-KMS, Presigned URL 제한 |
| 증거 분석 결과 | DynamoDB | 접근 제어 + PK 기반 분리 |
| 임베딩/텍스트 | Qdrant | 사건 단위 index 격리 |
| Draft 초안 | 백엔드 메모리/일시 저장 | 영구 저장 금지 |

---

## 3.2 S3 보안

- 버킷 전체 **Public Access Block = ON**
- SSE-KMS (AWS-managed key 또는 CMK)
- Presigned URL 유효기간: **최대 5분**
- 파일 경로 규칙:

s3://leh-evidence/
cases/{case_id}/raw/{uuid_filename}
cases/{case_id}/processed/{uuid}.json

---

## 3.3 RDS(PostgreSQL)

- 암호화: AES-256 at rest  
- 연결: VPC 내부 전용  
- 백업: 자동 백업 7일  
- Access: Backend IAM Role 기반 프라이빗 엔드포인트만

---

## 3.4 DynamoDB

- 사건 단위 파티션 키 → 사건 격리  
- VPC Endpoint로만 접근  
- Worker 외에는 Write 금지

---

## 3.5 Qdrant 보안

- Public Endpoint 금지  
- VPC 전용  
- 사건별 Index 분리 (`case_rag_{case_id}`)  
- IAM SigV4 인증  
- Query 요청은 Backend를 통해서만 가능

---

# 📁 4. 개인정보 보호 (Privacy Compliance)

LEH는 변호사·의뢰인의 개인정보 및 민감정보를 취급하므로 다음을 의무적으로 준수한다.

## 4.1 저장 금지 항목

아래 정보는 FE/BE/로그/Analytics 어떤 환경에도 **저장 금지**:

- 카카오톡 채팅 전문  
- 사진/영상의 민감한 장면 텍스트  
- 음성 STT 전문  
- 사건 관련 주민등록번호/계좌번호  
- 상대방 인적 사항 세부 내용

→ 원본은 **S3에만 저장**, 분석 텍스트는 **DynamoDB/Qdrant에 저장하되 최소화**.

## 4.2 FE 금지 규칙

- LocalStorage에 증거 전문 저장 금지  
- 브라우저 캐시(IndexedDB)에 증거 데이터 저장 금지  
- 스크린샷 경고(Optional)

## 4.3 로그 금지 규칙

- 로그에는 민감 텍스트/개인정보 포함 금지  
- Error log에는 “evidence_id”까지만 포함 가능  
- 클라이언트 IP 등은 hashing하여 저장

---

# ⚖️ 5. 한국 법률 준수 규정

LEH는 **변호사법·전자문서법·민법·개인정보보호법(PIPA)** 기준을 준수한다.

## 5.1 변호사법 — 법률사무대리 금지

### AI가 해서는 **절대 안 되는 기능**

- 자동 문서 제출  
- 자동 서명/날인  
- 법률적 판단 확정  
- “가능성/승소율” 등 결과 예측 제공  
- 상대방 주장에 대한 법적 조언 자동 제공

### LEH가 제공하는 기능 (합법)

- 증거 정리  
- 요약  
- Draft “초안 제안”  
- 사건 타임라인 제공  
- 유책사유 분류 (사실정보 기반)

→ LEH는 **법률적 판단을 대신하지 않고**, 변호사 판단을 도와주는 “AI 사무지원 도구로 한정”.

---

## 5.2 전자문서법

- 모든 증거 파일은 원본 유지 (삭제 금지)
- 변조 방지를 위해 S3 Object Lock 옵션 제공 가능

---

## 5.3 개인정보보호법(PIPA)

- 저장 최소화 원칙  
- 익명화/가명처리 우선  
- 접근 로그 필수 저장  
- 외부 전송 시(예: LLM API 호출) 민감 정보 마스킹

### LLM API 호출 규칙

- Whisper → 음성 STT 때 개인정보 포함 가능  
- GPT-4o Vision → 얼굴/개인 식별 정보 포함 가능  
- **AI 호출 전 마스킹 정책 적용 (Regex 기반)**

---

# 🤖 6. AI 안전성 / 리스크 관리

## 6.1 환각(Hallucination) 방지

- 증거 기반 RAG 필터링  
- RAG Score < Threshold 항목 인용 금지  
- Draft에서 “추정/예측” 문구 제거  
- LLM Prompt에 명시:

사실이 아닌 내용, 추정, 판단을 절대 생성하지 마라.
증거에 근거하지 않은 문장은 생성 금지.

## 6.2 Harmful Content 차단

- 욕설/폭언 인식 알고리즘은 “탐지”만 수행  
- 사용자에게 공격적 표현을 “생성”하지 않는다

## 6.3 AI 모델 호출 로그 보호

- 프롬프트 전체 저장 금지  
- `evidence_id, case_id, timestamp` 정도만 보관  
- LLM Provider로 전송되는 데이터는 최소화된 형태로

---

# 🧪 7. 보안 테스트 & 감사

## 7.1 정적 분석 / SAST

- GitHub CodeQL  
- SonarCloud (옵션)

## 7.2 동적 분석 / DAST

- 로그인/사건 조회 등 주요 엔드포인트 테스트  
- CSRF/Injection/XXE 점검 (패턴 기반)

## 7.3 침투 테스트

- 연 1회 외부 전문 업체  
- 예:  
  - Qdrant RCE  
  - Presigned URL 탈취  
  - JWT 변조 공격  
  - AI Worker 취약점 확인

---

# 📦 8. 데이터 보관 정책

| 데이터 | 보관 기간 | 근거 |
|--------|------------|-------|
| 사건 데이터 | 사건 종료 후 5년(권장) | 법무법인 내부 규정 |
| 증거 원본 | 동일 | 원본 보존 의무 |
| 로그(Audit) | 1년 이상 | 컴플라이언스 요구 |
| Draft Preview | 영구 저장하지 않음 | 법률사무대리 회피 |

---

# 🔚 END OF SECURITY_COMPLIANCE.md
