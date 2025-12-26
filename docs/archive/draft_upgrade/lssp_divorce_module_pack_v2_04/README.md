# LSSP Divorce Module Pack v2.04 — Draft Engine (Blocks + Citations)

이번 팩은 v2.01(프로세스/증거/서류) + v2.02(판례/초안 매핑) + v2.03(핵심포인트 추적) 위에
**‘초안 생성(문서 블록 조립) + 근거(증거/키포인트) 연결 + 판례 추천’**을 구현하기 위한 설계/시드/DDL을 제공합니다.

## 포함 파일
- docs/DRAFT_ENGINE_SPEC_v2_04.md : Draft Engine(블록 조립) 핵심 설계
- docs/UI_DETAIL_CASE_DRAFTS_v2_04.md : detail/case 화면 ‘초안’ 탭 스펙
- docs/API_CONTRACT_DRAFTS_v2_04.md : 초안/블록/인용 API 계약
- docs/DB_DDL_DRAFTS_v2_04.sql : Postgres DDL(추가 테이블)
- data/draft_blocks.v2_04.json : 문단(블록) 라이브러리 + 요구 키포인트/증거 조건
- data/draft_templates.v2_04.json : 문서 타입별(소장/조정/준비서면/증거목록 등) 조립 템플릿
- data/precedent_kb_additions.v2_04.json : v2.02 판례 KB 보강(케이스번호 기반)
- prompts/draft_generator_v2_04.md : “근거 기반” 문장 생성용 프롬프트(LLM 옵션)
- tasks/IMPLEMENTATION_CHECKLIST_v2_04.md : 구현 순서 체크리스트

## 설계 원칙(핵심)
1) **사실은 Keypoint에서만** 가져온다. (LLM이 사실을 만들면 즉시 실패)
2) 블록은 “포함 조건 + 요구 증거/키포인트”를 만족해야 자동 포함.
3) 모든 블록은 최소 1개 이상의 Citation(Extract/Keypoint)을 가진다. (없으면 TODO 블록 + 경고)
4) Precedent는 “참고자료”로만(요지+팩터). 사실 대체 금지.
