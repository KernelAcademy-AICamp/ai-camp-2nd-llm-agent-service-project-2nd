# API Contract: Recompute v2.15

## 1) Enqueue
`POST /cases/{case_id}/recompute`

Body (JSON):
```json
{
  "trigger_event": "evidence_uploaded",
  "trigger_entity": "evidence:550e8400-e29b-41d4-a716-446655440000",
  "mode": "async",
  "priority": 100
}
```

Response:
```json
{
  "job_id": "9b4fe1e4-f5bf-4a73-9b3c-23bd2a7d6f8a",
  "status": "queued"
}
```

Notes:
- server must validate `trigger_event` against allowlist (config JSON)
- if same `input_hash` already computed recently -> return `skipped` or reuse latest success job

## 2) List jobs by case
`GET /cases/{case_id}/recompute/jobs?limit=20`

Response:
```json
{
  "items": [
    {
      "job_id": "...",
      "trigger_event": "process_event_added",
      "status": "succeeded",
      "created_at": "...",
      "finished_at": "...",
      "error_message": null
    }
  ]
}
```

## 3) Read job detail (steps)
`GET /recompute/jobs/{job_id}`

Response:
```json
{
  "job": { "job_id": "...", "status": "failed", "error_message": "..." },
  "steps": [
    { "step_name": "process_engine", "status": "succeeded", "metrics": {"deadlines_created": 2} },
    { "step_name": "timeline", "status": "failed", "error_message": "missing confirmation_date" }
  ]
}
```

## 4) AI Worker callback (example)
`POST /ai-worker/callbacks/evidence-analysis-completed`

Body:
```json
{
  "case_id": "...",
  "evidence_id": "...",
  "analysis_version": "whisper+vision@2025-12-01",
  "result_ref": "dynamodb://.../pk/sk"
}
```

Server action:
- persist event `evidence_analysis_completed`
- enqueue recompute job
