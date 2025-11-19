# 백엔드(H) 작업 계획서

**작성일:** 2025-11-18
**담당자:** H (Backend/Infra)
**기술 스택:** FastAPI, PostgreSQL, AWS (S3, DynamoDB, OpenSearch)

---

## 📋 프로젝트 이해 요약

### LEH(Legal Evidence Hub)란?
- **이혼 사건 전용 AI 파라리걸 시스템**
- 변호사가 증거를 S3에 업로드하면, AI가 자동으로 분석·정리·요약
- 소장 초안(Draft Preview)을 AI가 제안 (자동 제출은 금지)
- **모든 데이터는 AWS 단일 인프라 내에서 처리**

### 당신(H)의 역할
1. **FastAPI 백엔드 API 개발**
2. **PostgreSQL 데이터베이스 설계 및 구현**
3. **S3 Presigned URL 발급 로직**
4. **JWT 인증/인가 시스템**
5. **DynamoDB/OpenSearch 조회 및 연동**
6. **Draft Preview API (GPT-4o + RAG 오케스트레이션)**
7. **AWS 인프라 설정 및 배포**

---

## 🎯 개발 우선순위 (Phase별)

### Phase 1: 기초 인프라 구축 (1주차)
✅ 필수 기반 작업

1. **개발 환경 설정**
   - Python 3.11+ 가상환경 생성
   - requirements.txt 작성 (FastAPI, SQLAlchemy, boto3, openai 등)
   - .env 파일 설정 (DB, AWS, OpenAI API 키)

2. **PostgreSQL 데이터베이스 설계**
   - 테이블 생성 (users, cases, case_members, audit_logs)
   - SQLAlchemy 모델 작성
   - Alembic 마이그레이션 설정

3. **FastAPI 기본 구조**
   - `backend/app/main.py` 생성
   - 라우터 기본 구조 (auth, cases, evidence, draft)
   - CORS, 미들웨어 설정
   - Health Check 엔드포인트 (`GET /health`)

### Phase 2: 인증 시스템 (1주차)
✅ 사용자 인증/권한 관리

4. **JWT 인증 구현**
   - 비밀번호 해싱 (bcrypt)
   - JWT 생성/검증 로직
   - `/auth/login` API 구현
   - JWT 미들웨어 작성

5. **사용자 관리**
   - 회원가입 API (옵션)
   - Role 기반 접근 제어 (RBAC)
   - 사건별 권한 체크 로직

### Phase 3: 사건 관리 API (1주차)
✅ 핵심 비즈니스 로직

6. **사건(Case) CRUD**
   - `POST /cases` - 사건 생성
   - `GET /cases` - 사건 리스트 조회
   - `GET /cases/{id}` - 사건 상세 조회
   - `PATCH /cases/{id}` - 사건 수정
   - `DELETE /cases/{id}` - 사건 종료 (soft delete)

7. **사건 멤버십 관리**
   - 사건별 멤버 추가/제거
   - 권한 체크 (OWNER/MEMBER/VIEWER)

### Phase 4: 증거 업로드 (S3 연동) (1-2주차)
✅ AWS S3 Presigned URL 방식

8. **S3 설정**
   - S3 버킷 생성 (`leh-evidence`)
   - IAM 정책 설정 (최소 권한)
   - 버킷 암호화 설정 (SSE-KMS)

9. **Presigned URL API**
   - `POST /evidence/presigned-url` - 업로드 URL 발급
   - `POST /evidence/upload-complete` - 업로드 완료 알림
   - S3 Event 설정 (Lambda 트리거용)

### Phase 5: 증거 조회 (DynamoDB/OpenSearch 연동) (2주차)
✅ AI Worker가 저장한 데이터 조회

10. **DynamoDB 연동**
    - boto3로 DynamoDB 쿼리 구현
    - `GET /cases/{id}/evidence` - 증거 리스트 조회
    - 필터링 (type, label, 날짜 범위)

11. **OpenSearch 연동**
    - OpenSearch Python 클라이언트 설정
    - `GET /cases/{id}/search` - RAG 검색 API
    - 사건별 인덱스 쿼리 (`case_rag_{case_id}`)

12. **증거 상세 조회**
    - `GET /evidence/{id}` - 증거 상세 정보
    - S3 Presigned URL 발급 (다운로드용)

### Phase 6: Draft Preview API (2-3주차)
✅ GPT-4o + RAG 기반 초안 생성

13. **Draft 생성 로직**
    - `POST /cases/{id}/draft-preview`
    - DynamoDB에서 증거 목록 조회
    - OpenSearch RAG 검색
    - GPT-4o 프롬프트 생성 및 호출
    - 증거 인용문(citations) 구조화

14. **Draft Export**
    - `GET /cases/{id}/draft-export`
    - docx 파일 생성 (python-docx 라이브러리)
    - 파일 다운로드 응답

### Phase 7: 보안 및 감사 로그 (3주차)
✅ 법적 컴플라이언스 준수

15. **Audit Log 구현**
    - 모든 API 요청 로그 기록
    - 누가/언제/무엇을 했는지 추적
    - `audit_logs` 테이블에 저장

16. **보안 강화**
    - HTTPS 강제
    - Rate Limiting (선택)
    - 에러 메시지에서 민감 정보 제거

### Phase 8: 테스트 및 배포 (3-4주차)
✅ 품질 보증 및 운영 준비

17. **테스트 작성**
    - pytest로 단위 테스트
    - API 통합 테스트
    - Mock을 이용한 S3/DynamoDB 테스트

18. **AWS 배포**
    - Lambda + API Gateway 또는 ECS(Fargate) 선택
    - RDS PostgreSQL 프로비저닝
    - 환경변수 관리 (AWS Secrets Manager)
    - CloudWatch 로그 설정

19. **CI/CD 파이프라인**
    - GitHub Actions 설정
    - 자동 테스트 + 배포

---

## 🛠 기술 스택 상세

### 백엔드 프레임워크
- **FastAPI** (최신 Python 비동기 웹 프레임워크)
- **Uvicorn** (ASGI 서버)
- **Pydantic** (데이터 검증)

### 데이터베이스
- **PostgreSQL** (RDS) - 정형 데이터
- **DynamoDB** - 증거 메타데이터 (AI Worker가 저장)
- **OpenSearch** - RAG 검색용 벡터 DB

### AWS 서비스
- **S3** - 증거 원본 저장
- **Lambda** - 백엔드 실행 환경 (또는 ECS)
- **API Gateway** - REST API 엔드포인트
- **IAM** - 권한 관리
- **CloudWatch** - 로그 및 모니터링

### 외부 API
- **OpenAI API** - GPT-4o (Draft 생성), Whisper (STT)

### Python 라이브러리 (주요)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
boto3==1.29.7
opensearch-py==2.4.0
openai==1.3.0
python-multipart==0.0.6
python-docx==1.1.0
pytest==7.4.3
httpx==0.25.2
```

---

## 📁 디렉토리 구조 (BACKEND_DESIGN.md 기준)

```
backend/
├── app/
│   ├── main.py                  # FastAPI 엔트리포인트
│   ├── core/
│   │   ├── config.py            # 환경변수, 설정
│   │   ├── security.py          # JWT, 패스워드 해싱
│   │   └── logging.py           # 구조화 로그 설정
│   ├── db/
│   │   ├── session.py           # DB 연결(RDS)
│   │   ├── models.py            # SQLAlchemy 모델
│   │   └── schemas.py           # Pydantic 스키마
│   ├── routers/
│   │   ├── auth.py              # 로그인/회원 API
│   │   ├── cases.py             # 사건 CRUD
│   │   ├── evidence.py          # Presigned URL / 조회
│   │   ├── draft.py             # Draft Preview API
│   │   └── search.py            # 사건 RAG 검색 API
│   ├── services/
│   │   ├── case_service.py      # 사건 관련 비즈니스 로직
│   │   ├── evidence_service.py  # S3 연동 및 Dynamo 조회
│   │   ├── draft_service.py     # Draft 생성(LLM 호출)
│   │   └── search_service.py    # OpenSearch 쿼리
│   ├── utils/
│   │   ├── s3.py                # Presigned URL 생성기
│   │   ├── dynamo.py            # DynamoDB Helper
│   │   ├── opensearch.py        # OS Helper
│   │   └── time.py              # 공통 시간/타임존 처리
│   └── middleware/
│       ├── auth_middleware.py   # JWT 인증 미들웨어
│       ├── audit.py             # 감사 로그 기록기
│       └── error_handler.py     # 공통 에러 핸들러
└── requirements.txt
```

---

## ⚠️ 주의사항 (법적/보안)

### 절대 금지 사항
1. **자동 제출/자동 입력 금지** - AI Draft는 "Preview"만 제공
2. **민감 정보 로그 금지** - 증거 내용을 로그에 남기지 말 것
3. **직접 S3 업로드 금지** - 반드시 Presigned URL 방식 사용
4. **AI Worker 데이터 변경 금지** - 백엔드는 Read-Only, AI Worker만 Write

### 보안 체크리스트
- [ ] JWT Secret은 강력한 랜덤 문자열 사용
- [ ] 모든 API는 HTTPS만 허용
- [ ] S3 버킷은 Public Access 차단
- [ ] 패스워드는 bcrypt로 해싱
- [ ] Audit Log는 모든 요청에 대해 기록
- [ ] 에러 메시지에 민감 정보 포함 금지

---

## 🤝 팀 협업 포인트

### AI Worker(L)와의 협업
- **AI Worker가 DynamoDB에 증거 메타데이터를 저장**
- 백엔드는 이를 **조회만** 수행
- S3 Event 트리거는 백엔드가 설정

### Frontend(P)와의 협업
- **API_SPEC.md 기준으로 API 응답 형식 맞추기**
- Presigned URL 발급 → FE가 S3에 직접 업로드
- Draft Preview는 JSON 형태로 반환

### Git 브랜치 전략
- **main**: 배포용 (직접 push 금지)
- **dev**: 통합 개발 브랜치 (자유롭게 push 가능)
- **feat/**: 기능 단위 브랜치 (필요시)

---

## 📚 참고 문서

프로젝트 루트의 `docs/` 폴더:
- `PRD.md` - 제품 요구사항
- `ARCHITECTURE.md` - 전체 시스템 구조
- **`BACKEND_DESIGN.md`** - 백엔드 설계 (가장 중요!)
- `API_SPEC.md` - API 명세서
- `SECURITY_COMPLIANCE.md` - 보안/법적 규정
- `CONTRIBUTING.md` - Git 협업 규칙

---

## 🎓 비개발자를 위한 학습 자료

### FastAPI 기초
- 공식 튜토리얼: https://fastapi.tiangolo.com/tutorial/
- 한글 가이드: FastAPI 공식 한글 번역본

### AWS 기초
- S3 Presigned URL: https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html
- DynamoDB 쿼리: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html

### SQLAlchemy ORM
- 공식 문서: https://docs.sqlalchemy.org/en/20/

---

## ✅ 다음 단계

1. **개발 환경 설정** - Python, PostgreSQL, AWS 계정
2. **Phase 1부터 순차적으로 진행**
3. **막히는 부분은 문서 참고 + 팀원과 협업**
4. **각 Phase 완료 후 Git commit**

화이팅! 🚀
