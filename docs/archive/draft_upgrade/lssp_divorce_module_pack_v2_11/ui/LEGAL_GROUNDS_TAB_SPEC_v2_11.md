# UI Spec v2.11 - Legal Grounds Tab

## Goals
- 사용자가 **G1~G6** 또는 절차(협의/재판/사실혼/가정폭력/국제/양육비)를 선택하면
  관련 조문이 자동 노출되고, 초안/체크리스트/쟁점에 연결된다.

## Layout (detail/case)
- 상단: 경고·알림(Deadlines/제척기간 위험/효력상실/과태료)
- 좌측: Grounds 목록(G1~G6 + Special)
- 우측: 근거 카드 + 입력필드 + 버튼

## Ground Card 구성
- (A) 설명: 사유 요약(짧게)
- (B) 관련 조문: chips (from ground_to_authorities_map)
- (C) 입력필드: 인지일/발생일/지속여부(해당 시)
- (D) 계산결과: 제척기간/가능여부(Boolean) + 리스크 메모
- (E) 연결 상태:
  - Evidence coverage: SATISFIED/PARTIAL/MISSING (v2.09)
  - Draft coverage: 블록 충족률 (v2.06)
- (F) 액션:
  - “초안에 삽입”: 선택 조문을 Draft citations로 추가
  - “누락 증거 요청”: v2.09 EvidenceRequest 생성

## Special 섹션
- Domestic Violence: 임시조치/보호명령(조문 chips)
- International: 준거법 판단(조문 chips)
- Child Support/Enforcement: 이행명령/제재(조문 chips)
