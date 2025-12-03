# Quickstart: Draft Document Export

**Feature**: 001-draft-export
**Date**: 2025-12-03

This guide walks through the export feature from a user's perspective.

---

## Prerequisites

1. User is authenticated and logged in
2. User has MEMBER or OWNER role on a case
3. Case has at least one AI-generated draft document

---

## User Flow 1: Export Draft to Word

### Step 1: Navigate to Case

1. Open the case dashboard
2. Click on a case from the list
3. Navigate to "Drafts" tab

### Step 2: Select Draft

1. View list of available drafts
2. Click on a draft to open preview

### Step 3: Preview and Edit (Optional)

1. Review the draft content in WYSIWYG editor
2. Make any necessary text edits
3. Changes auto-save

### Step 4: Export to Word

1. Click "Export" button in toolbar
2. Select "Word (.docx)" format
3. Wait for progress indicator (if document is large)
4. File downloads automatically

### Expected Result

- `.docx` file downloads to browser
- Document opens in Microsoft Word
- All formatting preserved (margins, fonts, headers)
- Korean text displays correctly

---

## User Flow 2: Export Draft to PDF

### Step 1-3: Same as Word Export

(Navigate, select, optionally edit)

### Step 4: Export to PDF

1. Click "Export" button in toolbar
2. Select "PDF" format
3. Wait for progress indicator
4. File downloads automatically

### Expected Result

- `.pdf` file downloads to browser
- Document opens in PDF reader
- Headers and footers on each page
- Page numbers centered in footer
- Document is non-editable (fixed layout)

---

## User Flow 3: Large Document Export (30+ pages)

### Step 1-3: Same as above

### Step 4: Initiate Export

1. Click "Export" button
2. Select format
3. Progress modal appears: "Generating document..."
4. Progress bar shows percentage

### Step 5: Wait for Completion

1. Stay on page or continue working
2. Notification appears when ready
3. Click "Download" to get file

### Expected Result

- Export completes within 30 seconds for 50-page document
- Download available for 1 hour
- Can export again if needed

---

## API Usage Examples

### List Drafts for Case

```bash
curl -X GET "https://api.leh.example.com/api/v1/cases/{case_id}/drafts" \
  -H "Authorization: Bearer {token}"
```

Response:
```json
{
  "drafts": [
    {
      "id": "draft-uuid",
      "title": "이혼소송 준비서면",
      "document_type": "brief",
      "status": "draft",
      "version": 1,
      "created_at": "2025-12-03T10:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Draft Content

```bash
curl -X GET "https://api.leh.example.com/api/v1/cases/{case_id}/drafts/{draft_id}" \
  -H "Authorization: Bearer {token}"
```

### Export to PDF

```bash
curl -X POST "https://api.leh.example.com/api/v1/cases/{case_id}/drafts/{draft_id}/export" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"format": "pdf"}'
```

Response (small document - immediate):
```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "format": "pdf",
  "file_size": 245678,
  "page_count": 15,
  "expires_at": "2025-12-03T11:30:00Z"
}
```

Response (large document - async):
```json
{
  "id": "job-uuid",
  "status": "processing",
  "format": "pdf",
  "started_at": "2025-12-03T10:30:00Z"
}
```

### Poll Export Job Status

```bash
curl -X GET "https://api.leh.example.com/api/v1/cases/{case_id}/exports/{job_id}" \
  -H "Authorization: Bearer {token}"
```

Response (completed):
```json
{
  "id": "job-uuid",
  "status": "completed",
  "format": "pdf",
  "download_url": "https://s3.amazonaws.com/...",
  "file_size": 1234567,
  "page_count": 75,
  "completed_at": "2025-12-03T10:30:45Z",
  "expires_at": "2025-12-04T10:30:45Z"
}
```

---

## Validation Checklist

After implementing, verify:

- [ ] Word export downloads valid .docx file
- [ ] PDF export downloads valid .pdf file
- [ ] Korean text renders correctly in both formats
- [ ] Page margins match Korean court standards (25mm top/bottom, 20mm left/right)
- [ ] Headers appear on each page with case info
- [ ] Footers show page numbers (e.g., "1 / 15")
- [ ] Font is Batang (or fallback) at 12pt
- [ ] Line spacing is 1.6
- [ ] Export action appears in audit log
- [ ] Large document (50+ pages) shows progress indicator
- [ ] Download URL works and expires after 1 hour
- [ ] Non-case members cannot export drafts

---

## Troubleshooting

### Export Fails with "Permission Denied"

- Verify user has MEMBER or OWNER role on case
- Check JWT token is valid and not expired

### Korean Text Shows as Boxes/Symbols

- Ensure Korean fonts are installed (Batang, Malgun Gothic)
- For PDF: verify WeasyPrint font configuration
- For DOCX: open in Microsoft Word (not Google Docs)

### Export Takes Too Long

- Documents over 100 pages may take 30-60 seconds
- Check server resources (memory, CPU)
- Consider async export for very large documents

### Downloaded File Won't Open

- Verify file extension matches format selected
- Try opening with alternative application
- Check if download was interrupted (file size matches expected)
