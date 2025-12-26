# Integrated Recompute Pipeline v2.15

## Why this exists
LSSP/LEH has **many derived outputs**:
- 프로세스 상태 머신 결과(현재 단계/다음 단계/필수 행위)
- 마감/경고(협의이혼 3개월 유효기간, 재판상 이혼 신고 1개월/과태료 등)
- 타임라인(사건 진행 + 증거 타임라인)
- 증거 Key Point(핵심 사실), 체크리스트(추가로 필요한 증거)
- 판례·근거 추천 + 초안 문장 후보(변호사 "미리보기")

이 출력들은 원천 데이터(입력)가 바뀌면 **무조건 다시 계산**되어야 합니다.
문제는 "언제/무엇을/어떤 순서로" 다시 계산할지를 시스템이 강제하지 않으면
- 화면마다 데이터가 불일치
- 알림이 누락
- 초안이 오래된 사실을 근거로 생성
같은 치명적 오류가 발생합니다.

따라서 v2.15는 **Derived-State Recompute Orchestration**를 표준화합니다.

## 핵심 원칙 (non-negotiable)
1) **단일 트리거 → 단일 Job**
   - 모든 변경은 `recompute_job`로 수렴
   - Job은 "무엇이 바뀌었는지"를 기록(감사)하고, 파이프라인을 실행

2) **Idempotent / deterministic**
   - 같은 입력에서 같은 출력을 만들어야 함
   - `input_hash`가 같으면 `skipped` 처리 가능

3) **Case-level serialization**
   - 같은 `case_id`에 대해 동시에 여러 recompute가 돌면 데이터가 깨짐
   - DB advisory lock 또는 `case_recompute_lock`으로 직렬화

4) **DAG 기반**
   - 모듈 간 의존성이 명확해야 한다
   - topological order로 실행

## Recompute 대상 (모듈)
아래 모듈은 이전 pack과 연결됩니다.

- `process_engine` (v2.14)
  - 입력: process 이벤트, 주요 날짜(confirmation_date, finalization_date 등), 자녀 유무
  - 출력: `case_process_state`, `deadlines`, `warnings(seed)`
- `timeline` (v2.13)
  - 입력: process state + evidence events
  - 출력: `case_timeline_events`
- `evidence_keypoints`
  - 입력: evidence 분석 결과(텍스트/OCR/STT/메타)
  - 출력: `case_keypoints`, `evidence_tags`
- `checklists`
  - 입력: 법적 사유(G1~G6) + keypoints + process stage
  - 출력: `case_checklists`
- `legal_recommender` (v2.12)
  - 입력: keypoints + checklists + timeline
  - 출력: `case_legal_recommendations` (판례/조문/논리 블록)
- `draft_preview`
  - 입력: recommendations + user facts
  - 출력: `draft_sections` (변호사 검토 전용)

## 트리거 이벤트 (Event Taxonomy)
이벤트는 "원천 데이터 변경"만 기록합니다. derived 결과는 저장하지 않습니다.

예:
- `evidence_uploaded`
- `evidence_deleted`
- `evidence_analysis_completed` (AI worker callback)
- `process_event_added` (ex: 협의이혼 신청/확인서 수령/신고 등)
- `consultation_note_created`
- `child_info_updated` (자녀 유무/나이/양육 형태)
- `asset_liability_updated`
- `court_deadline_updated` (기일 변경/연기)

이벤트 → 어떤 모듈을 돌릴지는 `data/recompute_triggers.v2_15.json`로 관리.

## 협의이혼/재판상 이혼 데드라인을 알림에 반영
derived-state에서 반드시 만든다:
- 협의이혼: `confirmation_date + 3 months` (유효기간, 경과 시 효력 상실)
- 재판상 이혼: `finalized_date + 1 month` (미신고 과태료, 독촉 후 증액)

알림 스케줄(권장):
- 협의이혼 신고 마감: D-10 / D-3 / D-1
- 재판상 신고 마감: D-7 / D-2 / D-0 (당일)

## 실행 방식 (권장)
- Backend API는 Job을 **enqueue**만 한다.
- 실제 recompute 실행은:
  - (개발) backend background task
  - (프로덕션) worker (Celery/RQ/Dramatiq 등)
- AI Worker가 완료 콜백을 보내면 backend는 `evidence_analysis_completed` 이벤트로 Job 생성.

## 실패/재시도 정책
- step 단위로 `recompute_job_steps`에 기록
- 재시도:
  - transient(네트워크/OpenAI) → step retry
  - permanent(데이터 누락/검증 실패) → job failed + UI에 "왜 실패했는지" 노출

## 최소 제공 API
- POST `/cases/{case_id}/recompute`
- GET  `/cases/{case_id}/recompute/jobs?limit=20`
- GET  `/recompute/jobs/{job_id}`

## UI
- 사건 상세 화면에 "최근 재계산 상태" 위젯
- 실패 시: 어떤 step이 왜 실패했는지, 해결 힌트 노출
- 스태프/변호사만 "수동 재계산" 버튼 활성화

---
See also:
- `docs/API_CONTRACT_RECOMPUTE_V2_15.md`
- `docs/DB_DDL_RECOMPUTE_V2_15.sql`
- `data/recompute_graph.v2_15.json`
- `data/recompute_triggers.v2_15.json`
