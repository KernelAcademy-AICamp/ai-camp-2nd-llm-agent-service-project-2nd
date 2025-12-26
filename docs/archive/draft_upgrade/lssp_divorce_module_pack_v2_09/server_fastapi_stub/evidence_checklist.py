"""
FastAPI stub: Evidence Checklist v2.09
- This file is intentionally framework-light so you can copy into your existing app structure.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/cases", tags=["evidence-checklist"])

# --- Pydantic models ---
class SuggestedLink(BaseModel):
    evidence_id: str
    reason: str

class ChecklistItemDTO(BaseModel):
    item_key: str
    title: str
    is_required: bool
    status: str
    required_min_count: int
    satisfied_count: int
    suggested_links: List[SuggestedLink] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)

class GroundChecklistDTO(BaseModel):
    code: str
    title: str
    score: int
    required_total: int
    required_satisfied: int
    items: List[ChecklistItemDTO]

class ChecklistResponse(BaseModel):
    case_id: str
    computed_at: datetime
    by_ground: List[GroundChecklistDTO]
    overall_score: int
    missing_required: List[Dict[str, Any]]

class EvaluateRequest(BaseModel):
    create_requests: bool = True
    request_due_days: int = 7

# --- Dependency placeholders ---
def get_db():
    """Return your DB session/connection."""
    raise NotImplementedError

# --- Routes ---
@router.get("/{case_id}/evidence-checklist", response_model=ChecklistResponse)
def get_evidence_checklist(case_id: str, grounds: Optional[str] = None, include_links: bool = True, db=Depends(get_db)):
    """
    - Loads requirement_sets/items (seeded)
    - Loads evidences/keypoints for the case
    - Computes satisfied_count and status per item
    - Returns per-ground progress + missing required items
    """
    raise NotImplementedError

@router.post("/{case_id}/evidence-checklist/evaluate")
def evaluate_evidence_checklist(case_id: str, req: EvaluateRequest = Body(...), db=Depends(get_db)):
    """
    Recompute status rows and optionally create evidence request tickets for missing required items.
    """
    raise NotImplementedError

@router.post("/{case_id}/evidence-requests")
def create_evidence_request(case_id: str, payload: Dict[str, Any] = Body(...), db=Depends(get_db)):
    """
    Create a request ticket manually.
    """
    raise NotImplementedError

@router.patch("/{case_id}/evidence-checklist/items/{requirement_item_id}/waive")
def waive_requirement_item(case_id: str, requirement_item_id: int, payload: Dict[str, Any] = Body(...), db=Depends(get_db)):
    """
    Mark as WAIVED with reason (audit).
    """
    raise NotImplementedError
