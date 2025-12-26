"""FastAPI stub: consultations v2.07

This file is a reference skeleton. Wire it into your existing FastAPI app.
No persistence layer is implemented here; map to your repository/ORM.

Core rules:
- Store content_redacted for default UI rendering.
- Any raw content access must be audited.
- Extracts must include source_spans; otherwise status=TODO.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional, List, Dict

router = APIRouter(prefix="/cases/{case_id}/consultations", tags=["consultations"])

Channel = Literal["IN_PERSON","PHONE","CHAT","VIDEO","EMAIL","OTHER"]
Role = Literal["CLIENT","LAWYER","SYSTEM"]
ExtractType = Literal["ISSUE","FACT","EVIDENCE_REQUEST","ACTION_ITEM","RISK","DEADLINE","OTHER"]
ExtractStatus = Literal["TODO","CONFIRMED","DISMISSED"]

class SessionCreate(BaseModel):
    channel: Channel
    title: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    participants: List[Dict[str, Any]] = Field(default_factory=list)
    summary_text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class MessageCreate(BaseModel):
    role: Role
    content: str
    occurred_at: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

class ExtractRunOptions(BaseModel):
    mode: Literal["heuristic","llm"] = "heuristic"
    overwrite: bool = False

@router.post("/sessions")
def create_session(case_id: str, body: SessionCreate):
    # TODO: persist
    return {"id": "TODO", "case_id": case_id, **body.model_dump()}

@router.get("/sessions")
def list_sessions(case_id: str, limit: int = 50, offset: int = 0):
    return {"items": [], "limit": limit, "offset": offset}

@router.post("/sessions/{session_id}/messages")
def add_message(case_id: str, session_id: str, body: MessageCreate):
    # TODO: compute content_redacted server-side
    return {"id": "TODO", "session_id": session_id, **body.model_dump()}

@router.post("/sessions/{session_id}/extract")
def run_extract(case_id: str, session_id: str, body: ExtractRunOptions):
    # TODO: extraction engine (heuristic/llm)
    return {"extracts": []}

@router.get("/sessions/{session_id}/extracts")
def list_extracts(case_id: str, session_id: str):
    return {"items": []}

@router.patch("/extracts/{extract_id}")
def update_extract(case_id: str, extract_id: str, payload: Dict[str, Any]):
    # TODO: update status/payload/source_spans
    return {"id": extract_id, "updated": True}

@router.post("/extracts/{extract_id}/promote/keypoint")
def promote_keypoint(case_id: str, extract_id: str):
    # TODO: validate extract CONFIRMED + spans exist
    return {"keypoint_id": "TODO", "timeline_event_id": "TODO"}
