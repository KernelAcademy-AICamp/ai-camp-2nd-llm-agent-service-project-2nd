from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.doc_render import render_docx, DocType

router = APIRouter(prefix="/cases", tags=["documents"])

class GenerateDocReq(BaseModel):
    doc_type: DocType
    format: str = Field(default="docx", pattern="^docx$")
    locale: str = "ko-KR"
    options: Dict[str, Any] = Field(default_factory=dict)

# NOTE: This is a reference implementation.
# Replace payload assembly with DB queries by case_id.
@router.post("/{case_id}/documents/generate")
def generate_document(case_id: str, req: GenerateDocReq):
    try:
        demo_path = Path(__file__).resolve().parents[3] / "data" / "demo_case.json"
        payload = json.loads(demo_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to load payload: {e}")

    if req.doc_type == "CONSENSUAL_INTENT_FORM":
        ws = payload["parties"].get("witnesses", [])
        if len(ws) < 2:
            raise HTTPException(status_code=400, detail="witnesses (2 adults) required for CONSENSUAL_INTENT_FORM")

    document_id = str(uuid4())
    out_dir = Path(__file__).resolve().parents[3] / "out"
    out_path = out_dir / f"{document_id}_{req.doc_type}.docx"
    render_docx(req.doc_type, payload, out_path)

    return {
        "document_id": document_id,
        "status": "READY",
        "download_url": f"/cases/{case_id}/documents/{document_id}/download"
    }
