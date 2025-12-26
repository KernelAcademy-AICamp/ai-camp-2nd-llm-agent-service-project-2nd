# LSSP Divorce Module Pack v2.11
Scope: Legal Authority Library + Citation Standard + Legal Grounds Tab UI spec

## Includes
- data/law_articles.v2_11.json
- data/ground_to_authorities_map.v2_11.json
- data/process_to_authorities_map.v2_11.json
- data/citation_format.v2_11.json
- docs/DB_DDL_LEGAL_AUTHORITIES_v2_11.sql
- docs/API_CONTRACT_LEGAL_AUTHORITIES_v2_11.md
- docs/LEGAL_AUTH_LIBRARY.md
- ui/LEGAL_GROUNDS_TAB_SPEC_v2_11.md
- server_fastapi_stub/legal_authorities.py

## Apply
1) Run SQL in docs/DB_DDL_LEGAL_AUTHORITIES_v2_11.sql
2) Seed authorities from data/law_articles.v2_11.json
3) Wire Draft citations to allow cite_type=AUTHORITY with ref_id=legal_authorities.id
4) Implement Legal Grounds Tab using ui spec and the maps in data/
