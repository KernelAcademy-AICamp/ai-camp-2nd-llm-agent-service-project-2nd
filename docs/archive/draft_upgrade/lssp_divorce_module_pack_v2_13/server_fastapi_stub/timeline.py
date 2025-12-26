from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/cases", tags=["timeline"])

# --- Pydantic models ---
class TimelineLinks(BaseModel):
    evidence_id: Optional[str] = None
    evidence_extract_id: Optional[str] = None
    keypoint_id: Optional[str] = None
    draft_id: Optional[str] = None
    draft_block_id: Optional[str] = None
    issue_id: Optional[str] = None
    checklist_item_id: Optional[str] = None
    consultation_id: Optional[str] = None

class TimelineCreate(BaseModel):
    category: str
    event_type: str
    event_subtype: Optional[str] = None
    title: str
    summary: Optional[str] = None
    occurred_at: datetime
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    severity: int = 0
    penalty_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    links: TimelineLinks = Field(default_factory=TimelineLinks)

class TimelineRecompute(BaseModel):
    mode: str = "INCREMENTAL"
    since: Optional[datetime] = None

# --- In-memory demo store (replace with DB) ---
_DEMO: Dict[str, List[Dict[str, Any]]] = {}

@router.get("/{case_id}/timeline")
def get_timeline(case_id: str, category: Optional[str] = None, limit: int = 200):
    items = _DEMO.get(case_id, [])
    if category:
        items = [x for x in items if x.get("category") == category]
    items = sorted(items, key=lambda x: x["occurred_at"], reverse=True)[:limit]
    return {"case_id": case_id, "items": items}

@router.post("/{case_id}/timeline/events")
def create_event(case_id: str, body: TimelineCreate):
    item = body.model_dump()
    item["id"] = len(_DEMO.get(case_id, [])) + 1
    item["occurred_at"] = body.occurred_at.isoformat()
    if body.start_at: item["start_at"] = body.start_at.isoformat()
    if body.end_at: item["end_at"] = body.end_at.isoformat()
    _DEMO.setdefault(case_id, []).append(item)
    return {"id": item["id"]}

@router.post("/{case_id}/timeline/recompute")
def recompute(case_id: str, body: TimelineRecompute):
    # Stub: in production, derive events from deadlines/procedure/keypoints/evidence/consultations
    return {"created": 0, "updated": 0, "deleted": 0, "mode": body.mode}
