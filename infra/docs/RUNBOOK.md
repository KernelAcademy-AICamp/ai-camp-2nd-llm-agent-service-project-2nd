# RUNBOOK.md — 운영 및 장애 대응 매뉴얼

**버전:** v1.0
**작성일:** 2025-11-19
**대상:** DevOps, On-call 개발자

---

## 🚨 1. 긴급 연락망 및 에스컬레이션 (Escalation Path)

장애 발생 시 상황의 심각도에 따라 아래 순서대로 전파하고 대응합니다.

| 레벨 | 담당자 | 응답 목표 | 호출 기준 |
|:---:|:---:|:---:|:---|
| **Lv 1** | 당직 개발자 (On-call) | 30분 내 | 서비스 접속 불가, 주요 기능 오류 발생 시 |
| **Lv 2** | Tech Lead | 1시간 내 | Lv 1에서 해결 불가하거나 데이터 무결성 이슈 발생 시 |
| **Lv 3** | CTO / PM | 즉시 | 데이터 유출, 보안 사고, 대규모 데이터 손실 등 치명적 장애 시 |

---

## 🛠 2. 장애 유형별 대응 시나리오 (SOP)

### 시나리오 A: AI Worker 멈춤 (업로드 후 무한 '처리 중')
* **증상:** S3에 파일은 정상적으로 업로드되었으나, DynamoDB/OpenSearch에 데이터가 생성되지 않고 UI에서 '처리 중' 상태가 지속됨.
* **진단:**
  ```bash
  # 1. CloudWatch Logs에서 최근 에러 확인
  aws logs filter-log-events --log-group-name /aws/lambda/leh-ai-worker --filter-pattern "ERROR"
  
  # 2. DLQ (Dead Letter Queue)에 쌓인 메시지 확인
  aws sqs get-queue-attributes --queue-url <DLQ_URL> --attribute-names ApproximateNumberOfMessages
  ```

  * **복구 절차:**
    1.  **외부 장애 확인:** OpenAI API Status 페이지를 확인하여 외부 장애인지 파악합니다. (외부 장애 시 공지 후 대기)
    2.  **일시적 오류:** 일시적인 네트워크/API 오류라면 DLQ의 메시지를 원본 큐로 재전송(Redrive)하여 재처리합니다. (AWS Console 또는 스크립트 사용)
    3.  **코드 버그:** 코드 문제로 판명되면 핫픽스 배포 후 `POST /admin/reprocess-evidence {evidence_id}` API를 호출하여 개별 건을 재처리합니다.

### 시나리오 B: 실수로 사건 '종료(삭제)'

  * **상황:** 변호사가 진행 중인 사건을 실수로 '삭제' 버튼을 눌러 종료시킴.
  * **복구 절차 (Soft Delete 복구):**
    1.  **DB 복구:** `cases` 테이블에서 해당 사건의 상태를 `closed`에서 `active`로 변경합니다.
        ```sql
        UPDATE cases SET status = 'active' WHERE id = '{case_id}';
        ```
    2.  **인덱스 복구:** OpenSearch 인덱스가 삭제되었다면, `POST /admin/reindex-case {case_id}` API를 호출하여 DynamoDB에 저장된 데이터를 기반으로 검색 인덱스를 재생성합니다.

### 시나리오 C: OpenAI 비용 급증 (Bill Shock)

  * **상황:** 특정 사건이나 계정에서 비정상적으로 많은 토큰 소모가 감지됨.
  * **대응 절차:**
    1.  **Circuit Breaker 발동:** 해당 `case_id`에 대한 AI 처리를 즉시 일시 정지합니다.
    2.  **로그 분석:** 업로드 로그를 분석하여 악의적인 대량 파일 업로드 공격(DDoS) 여부를 확인합니다.
    3.  **조치:** 공격으로 판단되면 해당 사용자 계정을 블락(Block)하고, 환불 또는 과금 조정을 검토합니다.

-----

## 🧹 3. 정기 점검 리스트 (Weekly)

안정적인 서비스 운영을 위해 매주 다음 항목을 점검합니다.

  - [ ] **S3 버킷 용량:** 불필요한 임시 파일(`tmp/`)이 자동 삭제 규칙(Lifecycle Rule)에 의해 잘 정리되고 있는지 확인합니다.
  - [ ] **RDS 백업:** 최근 자동 스냅샷이 정상적으로 생성되었는지 확인합니다.
  - [ ] **SSL 인증서:** 도메인 SSL 인증서의 만료일을 확인하고 자동 갱신 여부를 체크합니다.
  - [ ] **Audit Log 샘플링:** 감사 로그에 민감 정보(주민번호, 비밀번호 등)가 평문으로 남지 않았는지 무작위로 샘플링하여 검사합니다.
