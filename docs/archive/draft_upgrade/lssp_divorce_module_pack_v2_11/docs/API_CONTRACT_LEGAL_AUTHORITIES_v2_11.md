# API Contract v2.11 - Legal Authorities

## 1) Authorities
- `GET /legal-authorities`
  - query: `q`, `kind`, `code`
  - returns: list of authorities

- `GET /legal-authorities/{id}`
  - returns: authority + snippets[]

- `POST /legal-authorities/seed`
  - body: `{ items: Authority[] }` (관리자/마이그레이션용)

## 2) Snippets (pinpoint)
- `POST /legal-authorities/{id}/snippets`
  - body: `{ snippet, pinpoint?, source_ref }`

## 3) Case linking (선택)
- `POST /cases/{caseId}/authority-links`
  - body: `{ authority_id, note? }`
  - 목적: 사건별로 자주 쓰는 조문/판례 핀 고정

## 4) Draft citations
- `POST /drafts/{draftId}/citations`
  - body: `{ cite_type:'AUTHORITY', ref_id:authority_id, label, snippet?, source_ref? }`
  - 정책: 초안 블록 인스턴스마다 최소 1개 citation (v2.06 규칙)
