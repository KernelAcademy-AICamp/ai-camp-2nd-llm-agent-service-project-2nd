from __future__ import annotations
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/legal/precedents", tags=["precedents"])

class Precedent(BaseModel):
    precedent_id: str
    case_no: str
    court: Optional[str] = None
    date: Optional[str] = None
    gist: str
    tags: List[str] = []
    factors: List[str] = []

def _load_index() -> Dict[str, Any]:
    import json, os
    root = os.path.dirname(__file__)
    path = os.path.join(root, "..", "data", "precedent_index.v2_12.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/search", response_model=List[Precedent])
def search(q: str = Query("", min_length=0), tag: Optional[str] = None):
    idx = _load_index()
    out: List[Precedent] = []
    for p in idx.get("precedents", []):
        if tag and tag not in p.get("tags", []):
            continue
        hay = (p.get("gist","") + " " + p.get("case_no",""))
        if q and q not in hay:
            continue
        out.append(Precedent(
            precedent_id=p.get("precedent_id",""),
            case_no=p.get("case_no",""),
            court=p.get("court"),
            date=p.get("date"),
            gist=p.get("gist",""),
            tags=p.get("tags", []),
            factors=p.get("factors", []),
        ))
    return out
