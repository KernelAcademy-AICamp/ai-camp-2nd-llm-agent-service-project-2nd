# v2.05 빠른 적용(개발)

1) 백엔드에 documents 라우터 추가
- POST generate: case 데이터를 모아 payload_json을 구성 → python-docx로 렌더 → file_key 저장
- GET download: file_key로 파일 반환

2) 프론트 detail/case에 Documents 탭 추가
- 문서 타입 선택 드롭다운
- "생성" 버튼 → 다운로드 링크 표시
- EVIDENCE_INDEX는 케이스 제출용으로 “갑1~” 번호를 자동 부여(정렬: 사건일 asc → 업로드일).

3) 강제 규칙
- EVIDENCE_INDEX는 evidence.status(미검토/검토완료/증거적합)를 반드시 포함.
- CONSENSUAL_INTENT_FORM은 증인 2명 입력값 없으면 생성 불가(VALIDATION_ERROR).

샘플 실행:
python scripts/docgen_demo.py
→ out/ 폴더에 예시 docx 생성
