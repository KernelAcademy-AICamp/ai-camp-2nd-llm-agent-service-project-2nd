# Maintenance & Troubleshooting Guide

이 문서는 LEH 시스템의 안정적인 운영과 원활한 유지를 위한 가이드입니다. 에러 추적, 로그 분석, 보안 감사 및 서비스 복구 절차를 다룹니다.

---

## 1. 에러 추적 및 로그 분석

LEH의 모든 백엔드 요청은 **Correlation ID**를 통해 추적됩니다.

### 1.1 Error ID 연추적
에러가 발생하면 클라이언트는 아래와 같은 응답을 받습니다:
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "...",
    "error_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-24T12:00:00Z"
  }
}
```
- **조치 방법**: CloudWatch 또는 Sentry에서 `error_id` 값인 `550e8400-e29b-41d4-a716-446655440000`을 검색하면 해당 에러의 전체 Stack trace를 확인할 수 있습니다.

### 1.2 로그 필터링 (보안)
백엔드에는 `SensitiveDataFilter`가 적용되어 있어 아래 정보는 자동으로 마스킹(`***`) 처리됩니다:
- 비밀번호 (password, hashed_password)
- 이메일 주소
- JWT 토큰 (Bearer, eyJ...)
- 한국어 증거 내용 (Sensitive PII)
- AWS / OpenAI API Keys

> [!WARNING]
> 운영 환경에서 마스킹되지 않은 민감 정보를 로그에 남기지 않도록 `logger.info` 사용 시 주의하십시오.

---

## 2. 주요 기술 부채 및 개선 포인트

### 2.1 백엔드: LSSP 파이프라인 캡슐화 (중요)
- **현황**: `backend/app/api/lssp/pipeline.py`의 일부 로직이 Router 내에 인라인으로 구현되어 있습니다.
- **개선**: `LSSPService`를 생성하여 비즈니스 로직(RegEx 추출 등)을 Router와 분리해야 합니다.

### 2.2 프론트엔드: 레거시 토큰 정리
- **현황**: `lib/api/client.ts`에 `localStorage` 토큰을 삭제하는 코드가 남아 있습니다.
- **개선**: LEH는 HTTP-only Cookie 기반 인증을 사용하므로, LocalStorage 관련 레거시 코드를 제거하여 혼선을 방지해야 합니다.

---

## 3. 운영 체크리스트

### 3.1 모니터링
- **Sentry**: 5xx 에러 실시간 알림 확인.
- **AWS Budgets**: OpenAI 및 AWS 비용 한도 초과 여부 체크.
- **Health Checks**: `/api/health/ready`를 통해 DB 및 외부 서비스 연결 상태 확인.

### 3.2 배포 전 주의사항
- `DATABASE_URL` 등 환경 변수가 production용으로 설정되었는지 확인.
- `APP_ENV=prod` 설정 시 Swagger UI(`docs_url`)가 비활성화되는지 확인.

---

**유지보수 담당자**: H (Infra/Backend)  
**최종 업데이트**: 2025-12-24
