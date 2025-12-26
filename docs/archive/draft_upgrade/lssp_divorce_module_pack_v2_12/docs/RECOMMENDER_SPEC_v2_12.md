# v2.12 Recommender Spec (Authorities + Precedents)

목적
- 케이스 입력값(divorce_type, stage) + grounds(G1~G6) 점수 + keypoints를 기반으로
  1) 관련 법령(조문/스니펫)
  2) 관련 판례(요지/적용요소)
  를 추천하고, 초안(Draft Builder) 블록에 '인용(Citation)'을 자동 삽입한다.

핵심 원칙
- 추천은 '근거 제안'이고, 초안 문장에는 반드시 citation이 붙는다.
- citation 없는 블록은 [TODO] 상태로 남긴다.
- 알고리즘은 룰 기반(설명 가능) + (추후) 랭킹 모델로 확장 가능.

입력(Features)
- divorce_type: CONSENSUAL | JUDICIAL | DE_FACTO
- process_stage: enum (각 파이프라인별)
- ground_scores: { G1..G6: number }
- keypoints: [{kind, value, materiality, ground_tags[]}, ...]
- deadlines: [{penalty_type, due_at, status}, ...]  # 옵션

출력(Output)
- authorities: [{id, title, tags, score, reasons[]}]
- precedents: [{id, case_no, gist, tags, score, reasons[]}]
- insertion_plan: draft_block_id -> [citations...]

스코어링(요약)
- base(authority)=50, base(precedent)=40
- ground_boost: 상위 1~2개 ground 점수 비중 반영
- keypoint_boost: POLICE_CASE/MEDICAL/ADMISSION 등 강한 키포인트 가중
- tag_match/keyword_match: 결과물 tags/keywords가 케이스 신호와 맞으면 가점
- explain: 상위 5개 이유만 노출

안전장치
- '사실 단정' 금지: 추천이 있는 것과 사실 인정은 다름.
- 법령/판례 데이터는 운영자가 승인/버전관리(Seed + 변경로그) 한다.
