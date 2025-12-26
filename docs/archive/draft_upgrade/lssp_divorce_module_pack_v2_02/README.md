# LSSP Divorce Module Pack v2.02

목적: LSSP(이혼 법률 서비스 플랫폼)에서 **'재판초안/협의서 초안 탭'**을 구현하기 위한
- (1) 이혼사유(G1~G6)별 *증거 → 핵심포인트 → 초안 문단* 매핑
- (2) 판례/법조항 라이브러리(요지 + 적용조건)
- (3) DB/API 설계 가이드(최소 스키마 + 추천 확장)

본 패키지는 'detail/case' 페이지에 **증거 정리 탭(폴더+상태)**, **타임라인 뷰**, **법적 근거 탭**, **초안 탭**을
일관된 데이터 모델로 묶는 것을 목표로 한다.

## Contents
- docs/DRAFT_MAPPING.md : 사유별 매핑, 초안 구조, RAG/프롬프트 적용 포인트
- docs/DATA_MODEL.md : 테이블/필드(권장) + API 계약(초안)
- data/precedents.json : 핵심 판례 요지(검색용 메타 포함)
- data/ground_draft_map.json : G1~G6 → key_points/evidence_types/precedents/draft_blocks
- prompts/draft_snippet_rules.md : 문구 제안 규칙(안전/중립/재현성)

