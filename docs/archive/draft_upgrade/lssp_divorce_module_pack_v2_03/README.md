# LSSP Divorce Module Pack v2.03

목적: LSSP(이혼 법률 서비스 플랫폼) `detail/case` 페이지에 **'증거 → 핵심포인트(FACT) → 타임라인/초안'**으로 이어지는
**'증거 핵심포인트 추적(Keypoint Tracking)'** 모듈을 바로 구현할 수 있게 하는 패키지입니다.

핵심은 단순 파일 보관이 아니라,
- 증거(파일/링크/진술)에서 **법원이 읽을 수 있는 '사실 단위(Fact Unit)'**를 뽑아내고
- 그 사실을 **시간/인물/금액/행위/법적요건(G1~G6)**에 연결해
- 타임라인/초안 작성에 재사용 가능하게 만드는 것입니다.

## Contents
- docs/KEYPOINT_TRACKING.md : 핵심포인트 정의/상태/품질 기준 + UI 플로우
- docs/DB_SCHEMA_APPENDIX_v2_03.md : (v2.01/02에 추가되는) 테이블/필드/관계
- docs/API_CONTRACT_v2_03.md : detail/case에서 필요한 API 계약(최소)
- data/keypoint_types.v2_03.json : 키포인트 유형/필수필드/자동생성 규칙
- data/extraction_rules.v2_03.json : 증거 유형별로 뽑아낼 포인트(휴리스틱)
- prompts/keypoint_suggest.v2_03.md : (선택) AI 제안 프롬프트/제약(허위 금지)
- tasks/IMPLEMENTATION_CHECKLIST.md : 백엔드/프론트/워커 구현 체크리스트
