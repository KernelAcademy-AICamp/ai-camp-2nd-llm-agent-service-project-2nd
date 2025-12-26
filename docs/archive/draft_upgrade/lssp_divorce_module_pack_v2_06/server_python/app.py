from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from .draft_engine import DraftEngine

app = FastAPI(title="LSSP Draft Builder v2.06")

engine = DraftEngine()

class DraftGenerateRequest(BaseModel):
    draft_kind: str = Field(..., description="JUDICIAL_COMPLAINT | MEDIATION_REQUEST | CONSENSUAL_AGREEMENT")
    selected_claims: List[str] = Field(default_factory=list)
    selected_grounds: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)

@app.post("/cases/{case_id}/drafts/generate")
def generate(case_id: UUID, req: DraftGenerateRequest):
    # TODO: replace with DB-based case load
    case_ctx = engine.load_case_context_stub(case_id)

    draft = engine.generate(case_id=case_id, req=req.model_dump(), case_ctx=case_ctx)
    return draft

@app.get("/cases/{case_id}/drafts/{draft_id}")
def get_draft(case_id: UUID, draft_id: UUID):
    # TODO: replace with DB read
    raise HTTPException(status_code=501, detail="Not implemented (DB integration required)")
