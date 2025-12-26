# Implementation Checklist (v2.03)

## Backend (FastAPI)
- [ ] evidence_extracts 테이블/모델/CRUD
- [ ] keypoints 테이블/모델/CRUD
- [ ] keypoint_extract_links / keypoint_ground_links (M:N) 구현
- [ ] READY 전환 검증(필수필드 + 링크 체크)
- [ ] 중복 Keypoint 탐지(경고만)
- [ ] timeline_events 자동 생성(키포인트 생성/수정 시)
- [ ] audit log(누가 언제 무엇을 바꿨는지)

## Frontend (detail/case)
- [ ] 증거 정리 탭: 파일 리스트 + 폴더(G1~G6) + 상태 뱃지
- [ ] Extract UI: PDF는 페이지 범위 선택, 이미지/동영상은 시간 범위 선택, 채팅은 메시지 범위 선택
- [ ] 키포인트 리스트: 필터(ground/status/type/date), 검색, 중복 경고 표시
- [ ] 키포인트 편집: 5요소 입력 위저드 + READY 전환 버튼
- [ ] 타임라인: 자동 생성 이벤트 + 수동 이벤트 추가

## Worker (선택)
- [ ] OCR/ASR(있는 경우) → extracted_text 저장
- [ ] keypoint_suggest endpoint 연동(유저 승인형)

## QA
- [ ] 협의이혼/재판상 이혼/사실혼 각각 샘플 케이스로 플로우 검증
- [ ] 위법수집 리스크 플래그가 UI에 노출되는지 확인
