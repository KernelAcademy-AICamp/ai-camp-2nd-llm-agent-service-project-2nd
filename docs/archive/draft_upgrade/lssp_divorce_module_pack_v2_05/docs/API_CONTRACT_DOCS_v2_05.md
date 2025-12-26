# API Contract: Documents v2.05

## POST /cases/{case_id}/documents/generate
Request JSON:
{
  "doc_type": "CONSENSUAL_INTENT_FORM" | "CHILD_CUSTODY_AGREEMENT" | "EVIDENCE_INDEX" | "ASSET_INVENTORY" | "CASE_TIMELINE_SUMMARY",
  "format": "docx",
  "locale": "ko-KR",
  "options": {
    "include_citations": true,
    "include_watermark": false
  }
}

Response JSON:
{
  "document_id": "uuid",
  "status": "READY",
  "download_url": "/cases/{case_id}/documents/{document_id}/download"
}

## GET /cases/{case_id}/documents
Response: 생성된 문서 리스트(메타 + 생성 시각 + doc_type + status)

## GET /cases/{case_id}/documents/{document_id}/download
- Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
- Attachment download

## POST /cases/{case_id}/documents/{document_id}/regenerate
- 동일 doc_type으로 최신 case 데이터로 재생성(새 document_id 발급 권장)
