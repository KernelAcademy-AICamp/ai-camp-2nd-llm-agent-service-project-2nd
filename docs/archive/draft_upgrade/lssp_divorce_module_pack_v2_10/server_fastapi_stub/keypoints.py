from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/cases", tags=["keypoints"])

class ExtractRequest(BaseModel):
    extract_id: Optional[str] = None
    mode: str = Field(default="rule_based")
    evidence_type: str

@router.post("/{case_id}/evidences/{evidence_id}/keypoints/extract")
def extract(case_id: str, evidence_id: str, req: ExtractRequest):
    raise HTTPException(status_code=501, detail="Stub: fetch extracted text, run rule engine, store candidates")

@router.get("/{case_id}/keypoints/candidates")
def list_candidates(case_id: str, status: str = "CANDIDATE", evidence_id: Optional[str] = None):
    raise HTTPException(status_code=501, detail="Stub")

@router.patch("/{case_id}/keypoints/candidates/{candidate_id}")
def update_candidate(case_id: str, candidate_id: int, patch: Dict[str, Any]):
    raise HTTPException(status_code=501, detail="Stub")

@router.post("/{case_id}/keypoints/promote")
def promote(case_id: str, body: Dict[str, Any]):
    raise HTTPException(status_code=501, detail="Stub: create canonical keypoints + merge + refresh checklist/drafts/issues")
