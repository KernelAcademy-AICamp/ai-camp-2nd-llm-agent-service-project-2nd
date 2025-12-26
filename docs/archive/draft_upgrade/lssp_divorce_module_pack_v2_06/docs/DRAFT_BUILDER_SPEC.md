# Draft Builder UI Spec (detail/case > 초안 탭)

## 탭 구조(권장)
- 증거정리(Evidence Vault)
- 핵심포인트(Keypoints)
- 타임라인(Timeline)
- 초안(Draft Builder)  ← v2.06 대상
- 문서(DOCX/PDF Export) ← v2.05 연동

## 초안 탭 핵심 플로우
1) “초안 종류” 선택
   - 재판상 이혼 소장
   - 조정신청서
   - 협의이혼 합의서(양육/재산/위자료 옵션)
2) “청구 항목(Claims)” 체크
   - 이혼(기본)
   - 위자료
   - 재산분할
   - 양육자/친권
   - 양육비/면접교섭
3) “누락 데이터” 자동 표시
   - 필수 Keypoint 미충족
   - 근거(증거) status가 ADMISSIBLE 아님
   - 제척기간/신고기한 임박 등 경고
4) “블록 조립 결과” 출력
   - 블록별로 (근거보기) 버튼: 사용된 Evidence/Keypoint 리스트로 점프
   - Citation이 0개인 블록은 생성 불가 → TODO 블록으로만 출력

## UX 원칙
- 문단 단위 편집: 블록은 개별로 수정/숨김/고정 가능
- “근거 중심”: 사용자는 ‘글’을 믿는 게 아니라 ‘근거’를 보고 결정한다
- 경고는 상단 고정 배너(절차 기한/제척기간/필수 서류 누락)

## 출력 포맷
- JSON Draft(블록 배열 + citations)
- HTML(렌더링)
- DOCX/PDF(Export 서비스로 전달)
