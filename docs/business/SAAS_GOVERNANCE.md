# SAAS_GOVERNANCE.md — SaaS 운영 및 거버넌스 가이드

**버전:** v1.0
**작성일:** 2025-12-24
**목적:** LEH 솔루션의 멀티테넌시 격리, 권한 체계(RBAC), 및 테넌트 관리 표준을 정의함.

---

## 1. 멀티테넌시 격리 모델 (Multi-tenancy Isolation)

LEH는 **Case-Centric Logical Isolation** 모델을 채택합니다.

- **격리 단위**: `Case (사건)`가 실질적인 테넌트(Tenant) 경계 역할을 수행합니다.
- **접근 제어**: `CaseMember`가 존재하지 않는 사용자는 해당 사건의 데이터(Postgres, S3, DynamoDB, Qdrant)에 어떤 방식으로도 접근할 수 없습니다.
- **물리적 격리**: RAG 데이터는 Qdrant의 `case_{id}` 컬렉션 단위로 분리되어 벡터 유사도 검색 시 테넌트 간 데이터 혼입을 원천 차단합니다.

## 2. RBAC 권한 계층 (Role-Based Access Control)

SaaS 환경의 유연한 사용자 관리를 위해 Role 기반 권한 체계를 적용합니다.

| 역할 (Role) | 주요 권한 | 비고 |
|:---|:---|:---|
| **Admin** | 시스템 설정, 전체 사용자 관리, 감사 로그 조회 | 로펌 관리자 |
| **Lawyer** | 사건 생성, AI 분석 실행, 초안 생성, 과금 관리 | 주담당자 |
| **Staff** | 증거 업로드 지원, 타임라인 정리, 초안 검토 | 보조인력 |
| **Client** | 자신의 사건 증거 업로드, 현황 조회 | 외부 사용자 |
| **Detective** | 허가된 증거 항목 업로드 | 외부 협력자 |

### 권한 매트릭스 (Permission Matrix)
`RoleManagementService`를 통해 각 서비스(Cases, Evidence, Billing, Admin)별 세부 권한(Read/Write/Delete)을 제어하며, 이는 SaaS 규모 확장에 따라 동적으로 확장 가능한 구조입니다.

## 3. 과금 및 구독 거버넌스 (Monetization)

- **Pay-per-Case (MVP)**: 개별 사건의 복잡도와 데이터 규모에 따른 Case 단위 인보이스 발행. (`BillingService` 구현체)
- **Subscription (Enterprise)**: 로펌 단위의 월간 고정 구독 모델 (향후 로드맵).
- **Quota Management**: 로펌/사용자별 월간 AI 토큰 사용량 할당량을 설정하여 FinOps 리스크를 관리합니다.

## 4. 데이터 주권 및 법적 준거성 (Compliance)

- **Data Ownership**: 모든 업로드된 원본 증거(S3)와 분석 결과물은 고객사의 자산으로 처리됩니다.
- **Right to be Forgotten**: 사건 종료(`DELETE /cases/{id}`) 시, 검색용 벡터(Qdrant)와 메타데이터(DynamoDB)는 즉시 파기하거나 익명화 처리하여 데이터 최소화 원칙을 준수합니다.
- **Chain of Custody**: 감사 로그(Audit Log)를 통해 누가, 언제, 어떤 데이터에 접근했는지 SaaS 운영사가 아닌 **로펌 자체 관리자가 검증**할 수 있는 도구를 제공합니다.
