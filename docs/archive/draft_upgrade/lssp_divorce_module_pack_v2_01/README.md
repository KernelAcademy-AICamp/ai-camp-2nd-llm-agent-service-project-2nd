# LSSP Divorce Module Pack v2.01 (적용용 자료)

이 폴더는 **이혼 업무 보조 서비스**에 바로 꽂아 넣을 수 있도록 만든 '도메인 데이터 + 로직 설계' 패키지입니다.

## 포함 파일
- `seeds/legal_grounds.v2_01.json` : 민법 840조 사유 코드(G1~G6) 메타데이터
- `seeds/evidence_checklist.v2_01.json` : 사유별 증거 체크리스트(카테고리/우선순위/추적 포인트 포함)
- `seeds/process_timeline.v2_01.json` : 이혼 유형별 상태 머신 + 마감 기한 규칙 + 알림 오프셋
- `seeds/documents_required.v2_01.json` : 단계별 필수 서류
- `SPEC_DB_SCHEMA_v2_01.md` : DB/엔드포인트 설계 제안(프로젝트에 맞춰 조정)

## 핵심 원칙 (서비스가 지켜야 할 3가지)
1) **증거는 '파일'이 아니라 '사실(Fact)'로 바꿔야 가치가 생김**  
   → Evidence 업로드 후, `EvidenceExtract`(타임라인/금액/인물/발언) 구조화가 필수.

2) **절차는 상태 머신으로 고정**  
   → 사용자가 어디까지 왔는지(STATE) + 다음 행동(ACTION) + 마감(DEADLINE)을 분리.

3) **마감 미준수의 결과가 유형별로 다름**  
   - 협의이혼: 신고 지연 = 확인 효력 상실(처음부터)  
   - 재판상 이혼: 신고 지연 = 효력 유지 + (과태료 가능)  
