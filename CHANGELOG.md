# Changelog

All notable changes to the Legal Evidence Hub (LEH) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- AI Worker: Qdrant 벡터 저장소 통합 예정 (#21)

### Changed
- 케이스 삭제 시 Qdrant 컬렉션 삭제 로직 추가 예정 (#13)

---

## [0.2.0] - 2025-11-27

### Added

#### Backend
- **DynamoDB 실연동**: Mock 구현을 실제 boto3 클라이언트로 교체 (#10)
- **Qdrant 벡터 DB**: OpenSearch를 Qdrant로 완전 전환 (#10)
- **OpenAI API 연동**: Chat completion, Embedding 실제 API 호출
- **Draft Export**: DOCX/PDF 형식 초안 다운로드 기능 (#8)
- **PATCH /cases/{id}**: 케이스 제목/설명 수정 API (#8)
- **POST /evidence/upload-complete**: 업로드 완료 알림 API (#8)

#### Frontend
- **Design System**: 디자인 토큰 및 프리미티브 컴포넌트 구현
- **접근성 개선**: 버튼 type 속성, aria-label 추가
- **SEO 최적화**: sitemap.xml, robots.txt, 메타 태그 설정
- **반응형 디자인**: 태블릿 브레이크포인트 추가
- **Mock 인증**: 백엔드 미실행 시 개발용 Mock 로그인

#### AI Worker
- **handler.py 버그 수정**: case_id 추출, /tmp 정리 (#6)
- **Parser 메타데이터 표준화**: 모든 파서에 표준 메타데이터 추가 (#12)
- **DLQ 에러 핸들링**: 재시도 가능/불가능 에러 분류 (#16)

#### Infrastructure
- **CI 파이프라인**: GitHub Actions 테스트 자동화
- **PostgreSQL 로컬 설정**: docker-compose 통합 (#18)

### Changed
- OpenSearch → Qdrant 전환 (모든 벡터 검색 기능)
- 환경 변수 이름 변경: `OPENSEARCH_*` → `QDRANT_*`

### Fixed
- AI Worker handler.py: bucket_name을 case_id로 잘못 사용하던 버그 (#6)
- 누락된 API 엔드포인트 구현 (#8)

---

## [0.1.0] - 2025-11-20

### Added

#### Backend (Phase 1)
- **인증 시스템**: JWT 기반 로그인, 회원가입
- **RBAC**: 역할 기반 접근 제어 (Admin, Lawyer, Staff)
- **케이스 관리**: CRUD API
- **Evidence Upload**: S3 Presigned URL 발급
- **Evidence 조회**: DynamoDB 메타데이터 조회
- **Draft Preview**: RAG 기반 초안 생성
- **사용자 관리**: Admin 초대, 목록, 삭제
- **케이스 공유**: 다중 멤버 권한 관리
- **Article 840 태그**: 유책사유 태그 연동
- **Audit Log**: 활동 로그 기록 및 조회

#### Frontend (Phase 1)
- **로그인/회원가입 페이지**
- **케이스 목록 대시보드**
- **케이스 상세 페이지**
- **증거 업로드 UI**
- **타임라인 뷰**
- **Draft 탭**: 초안 미리보기 및 편집
- **랜딩 페이지**: 12개 섹션 구현
- **Admin 페이지**: 사용자, 역할, 감사 로그

#### AI Worker (Phase 1)
- **S3 Event 파싱**: Lambda 트리거 처리
- **텍스트 파서**: .txt, 카카오톡 형식
- **PDF 파서**: 텍스트 추출 + OCR fallback
- **이미지 파서**: GPT-4o Vision + Tesseract OCR
- **오디오 파서**: Whisper STT
- **Article 840 Tagger**: 유책사유 자동 태깅
- **임베딩 생성**: text-embedding-3-small

#### Security
- HTTP Security Headers 적용
- 민감정보 로깅 필터
- Hardcoded Secrets 검사 스크립트

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.2.0 | 2025-11-27 | AWS 실서비스 연동, Qdrant 전환, Design System |
| 0.1.0 | 2025-11-20 | MVP 기능 완성, 핵심 API 및 UI 구현 |

---

## Contributors

- **H (Backend/Infra)**: FastAPI, AWS 연동, 인증/권한
- **L (AI/Data)**: AI Worker, 파서, RAG, 임베딩
- **P (Frontend/PM)**: React 대시보드, UX, GitHub 운영

---

[Unreleased]: https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/KernelAcademy-AICamp/ai-camp-2nd-llm-agent-service-project-2nd/releases/tag/v0.1.0
