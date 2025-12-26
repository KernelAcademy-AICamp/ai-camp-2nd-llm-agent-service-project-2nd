# Implementation Checklist v2.04 — Draft Engine

## Backend
- [ ] draft_templates / draft_blocks seed 로더
- [ ] /cases/{id}/drafts 생성(Generate) 엔드포인트
- [ ] block inclusion(조건/요구키포인트/증거태그) 로직 구현
- [ ] citations 저장(블록 ↔ keypoint/extract)
- [ ] coverage_score 계산 + 품질 게이트

## Frontend (detail/case)
- [ ] 탭: 증거정리 / 핵심포인트 / 초안
- [ ] 문서 타입 카드 + 생성 버튼
- [ ] 블록 에디터(섹션 접기/펼치기, 근거 보기)
- [ ] 경고/알림 영역(기한/제척기간/서류 누락)
- [ ] DOCX export 다운로드

## Data
- [ ] v2.02 precedents.json + v2.04 additions 병합
- [ ] ground_draft_map과 draft_blocks 연결(블록 id 기준)
- [ ] keypoint_types/v2.03와 draft_blocks.required_keypoint_types 정합성 확인

## Safety
- [ ] Citation 없는 블록은 저장 금지(or TODO 처리)
- [ ] “증거 위조/조작” 요청 감지 시 차단
