from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

router = APIRouter(prefix="/cases", tags=["dashboard"])

# NOTE: This is a stub. Wire to your DB/repo layer.

@router.get("/{case_id}/dashboard")
def get_dashboard(case_id: str) -> Dict[str, Any]:
    # TODO: compute scores + top issues
    return {
        "case_id": case_id,
        "scores": {
            "deadline_risk": 0,
            "evidence_completeness": 0,
            "draft_completeness": 0,
            "procedure_progress": 0
        },
        "counters": {"evidences": 0, "keypoints": 0, "open_issues": 0, "due_soon": 0},
        "top_issues": []
    }

@router.post("/{case_id}/issues/recompute")
def recompute_issues(case_id: str) -> Dict[str, Any]:
    # TODO: apply notification_rules + templates
    return {"case_id": case_id, "created": 0, "updated": 0, "resolved": 0}

@router.get("/{case_id}/issues")
def list_issues(case_id: str, status: str = "OPEN", group: Optional[str] = None) -> Dict[str, Any]:
    return {"case_id": case_id, "items": []}

@router.patch("/{case_id}/issues/{issue_id}")
def update_issue(case_id: str, issue_id: str, status: str, note: Optional[str] = None) -> Dict[str, Any]:
    if status not in {"ACKED", "RESOLVED", "DISMISSED"}:
        raise HTTPException(status_code=400, detail="invalid status")
    return {"case_id": case_id, "issue_id": issue_id, "status": status, "note": note}

@router.get("/{case_id}/issues/{issue_id}/links")
def get_issue_links(case_id: str, issue_id: str) -> Dict[str, Any]:
    return {"case_id": case_id, "issue_id": issue_id, "links": []}
