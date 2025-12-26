# LSSP Divorce Module Pack v2.06 — Draft Builder (소장/조정신청서/합의서 초안 엔진)

이 패키지는 **증거(Evidence) → 핵심포인트(Keypoint) → 타임라인(Event)** 데이터가 이미 쌓인 상태에서,
`detail/case` 화면의 **“재판초안/협의서 초안 탭”**에서 바로 쓸 수 있는 **문단(블록) 조립형 초안 생성 엔진**을 제공합니다.

## 목표
- “그럴듯한 헛소리” 금지: **모든 문단은 최소 1개 이상 Citation(근거 링크)을 강제**합니다.
- 초안은 “문서 한 장”이 아니라 **블록들의 조립 결과**입니다.
- 블록 포함 여부는 **조건식(필수 keypoint/evidence/status)**으로 결정됩니다.

## 포함 기능
- 소장(재판상 이혼) 기본 골격: 청구취지 / 청구원인 / 입증방법(증거목록)
- 조정신청서 기본 골격
- 협의이혼 합의서(양육/재산/위자료 포함 옵션) 기본 골격
- Claim Library(청구 단위 템플릿) + Block Library(문단 템플릿)
- DB DDL(추가 테이블) + API 계약 + FastAPI 레퍼런스 구현 스켈레톤

## 통합 전제(이미 있어야 하는 것)
- evidences / keypoints / timeline_events 테이블(또는 동등한 데이터 모델)
- evidence.status = UNREVIEWED | REVIEWED | ADMISSIBLE | QUESTIONABLE
- keypoint.kind (DATE_EVENT, PERSON, LOCATION, ADMISSION, VIOLENCE, SPENDING, ...)

## 빠른 적용 순서
1) `docs/DB_DDL_DRAFT_BUILDER_v2_06.sql` 마이그레이션 적용
2) `data/*.json` 시드 로딩(템플릿/블록/법조항 참조)
3) `server_python/app.py` 참고하여 API 구현
4) `detail/case`에 Draft Builder 탭 붙이기: 블록 미충족 항목을 TODO로 표시

## 폴더
- docs/ : 스펙/DDL/API 계약
- data/ : 템플릿 시드(JSON)
- server_python/ : FastAPI 스켈레톤
- scripts/ : 데모 데이터/생성 예시
