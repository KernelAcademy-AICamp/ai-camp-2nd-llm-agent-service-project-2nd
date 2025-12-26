# LSSP/LEH Module Pack v2.12
주제: 법령/판례 추천 + 초안 자동 인용 삽입

포함
- 추천 룰/포맷 시드: data/
- DB DDL: docs/DB_DDL_PRECEDENTS_v2_12.sql
- API 계약: docs/API_CONTRACT_RECOMMENDER_v2_12.md
- FastAPI 스텁: server_fastapi_stub/
- 데모: scripts/recommender_demo.py

주의
- precedent_index는 TODO placeholder입니다. 운영자가 '검증된 판례 요지'로 채워야 합니다.
- 본 모듈은 초안 문단에 citation을 강제하여, 무근거 문장을 구조적으로 방지합니다.
