# Draft Block Library (v2.06)

## 블록 설계 원칙
- 블록은 “문단 1개” 단위
- 블록 포함 조건을 명시(필수 keypoint 종류/필수 evidence 태그/최소 citations)
- 블록은 항상 `block_id`, `title`, `body_template`, `required_claims`, `required_keypoints`, `required_evidence_tags`, `min_citations`를 가진다.

## 기본 블록(소장)
1) parties
2) jurisdiction_and_process (조정전치/관할 안내 등)
3) relief_requested (청구취지)
4) facts_timeline_summary (사실관계 요약 + 타임라인)
5) legal_ground_analysis_G1..G6 (선택된 G코드만)
6) limitation_check (제척기간/기간 지속성)
7) related_claims (위자료/재산분할/양육비 등)
8) evidence_plan (입증방법: 갑 제1호증~)
9) attachments_list (첨부서류 체크리스트)

## Citation 강제
- `min_citations=1` 기본
- citations=0이면 해당 블록은 `TODO_BLOCK`으로 교체:
  - 제목: “근거 부족”
  - 내용: “이 블록을 생성하려면 ○○ 증거/핵심포인트가 필요합니다.”
