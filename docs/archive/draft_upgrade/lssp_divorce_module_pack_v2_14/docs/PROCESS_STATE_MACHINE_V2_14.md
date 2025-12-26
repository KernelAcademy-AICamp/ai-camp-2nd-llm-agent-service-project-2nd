# Process State Machine V2.14 (LSSP/LEH)

이 문서는 '이혼 업무 보조 서비스'의 절차를 **상태 머신(State Machine)** 으로 고정하기 위한 규격이다.
목표:
- 케이스가 현재 어디에 있고, 다음에 무엇을 해야 하며,
- 무엇이 **막혀 있는지(누락 단계)**,
- 무엇이 **급한지(기한/패널티)** 를 시스템이 자동으로 산출한다.

## 1. 공통 원칙
- 상태(state)는 *UI 진행표시*, *알림 계산*, *초안/서류 생성 가능 여부*의 단일 기준이다.
- 이벤트(event)는 상태를 바꾸며, 모든 이벤트는 감사 로그(audit log)를 남긴다.
- "기한(Deadline)"은 state_machine이 생성하는 1급 객체로, 타임라인/대시보드/경고에 같은 데이터로 노출한다.

## 2. 협의이혼(CONSENSUAL) 상태 흐름
### States
- DRAFT → FILED → COOLING_OFF → CONFIRMATION_SCHEDULED → CONFIRMED → REPORTED
- 예외 종결: WITHDRAWN / AUTO_WITHDRAWN / EXPIRED

### 핵심 로직
- 숙려기간 산정:
  - 미성년 자녀(임신 포함) 있으면 3개월(특례: 성년 도달 임박 시 성년일까지 단축)
  - 자녀 없으면 1개월
  - 가정폭력 등 급박한 사정으로 단축/면제 승인 시 즉시 종료
- 확인서 등본 교부/송달 후 3개월 내 신고: 기한 경과 시 효력 상실(EXPIRED)

### 불출석(기일) 로직
- NO_SHOW_CONFIRMATION 이벤트 누적 2회 → AUTO_WITHDRAWN

## 3. 재판상 이혼(JUDICIAL) 상태 흐름
- 조정전치: MEDIATION_REQUIRED에서 소송 직접 제기 이벤트는 차단/안내.
- 조정 성립 또는 판결 확정 시 FINALIZED가 되며,
- FINALIZED + 1개월이 신고 기한(과태료 성격).

## 4. 사실혼 해소(DE_FACTO)
- 신고나 법원절차는 필수 아님.
- 다만 재산분할/위자료 등 청구로 이어질 수 있어 Claims 서브플로우를 둔다.

## 5. 특수 모듈
- DV: 긴급임시조치(48h) → 임시조치(2M, 연장) → 보호명령(6M~) 상태/기한 관리
- INTL: 준거법/관할 판단을 라우팅 state로 관리(서브모듈)

## 6. Missing Step Warnings
- 누락 입력/누락 단계/기한 임박·초과를 규칙으로 분리한다.
- 경고는 항상 "해결 방법"을 포함한다.
