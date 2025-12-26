# v2.12 API Contract (Recommender)

## POST /legal/recommendations
설명: 케이스 컨텍스트 기반 추천(법령 + 판례)

Request
{
  "case_id": "uuid",
  "divorce_type": "JUDICIAL",
  "process_stage": "OPTIONAL",
  "ground_scores": {"G3": 95, "G6": 60},
  "keypoints": [{"kind":"POLICE_CASE","value":{},"materiality":90,"ground_tags":["G3"]}]
}

Response 200
{
  "case_id": "uuid",
  "authorities": [{"id":"...","title":"...","tags":["..."],"score":123,"reasons":["..."]}],
  "precedents": [{"id":"...","case_no":"...","gist":"...","tags":["..."],"score":98,"reasons":["..."]}]
}

## POST /cases/{case_id}/drafts/{draft_id}/citations/auto-insert
설명: 특정 draft의 블록들에 추천 citation을 자동 삽입

Request
{
  "strategy": "TOP_N_PER_BLOCK",
  "n": 2,
  "only_if_missing": true
}
