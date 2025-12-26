from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import uuid
import datetime

router = APIRouter(prefix="/legal-authorities", tags=["legal-authorities"])

class Authority(BaseModel):
    id: str
    kind: str = "STATUTE"   # STATUTE|PRECEDENT|GUIDELINE
    jurisdiction: str = "KR"
    code: str
    article: str
    title: str
    summary: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    source_ref: Optional[str] = None

class Snippet(BaseModel):
    id: str
    authority_id: str
    snippet: str
    pinpoint: Optional[str] = None
    source_ref: str
    created_at: str

# In-memory store for stub/demo
AUTHORITIES: Dict[str, Authority] = {}
SNIPPETS: Dict[str, List[Snippet]] = {}

@router.get("", response_model=List[Authority])
def list_authorities(q: Optional[str] = None, kind: Optional[str] = None, code: Optional[str] = None):
    items = list(AUTHORITIES.values())
    if kind:
        items = [x for x in items if x.kind == kind]
    if code:
        items = [x for x in items if x.code == code]
    if q:
        ql = q.lower()
        items = [x for x in items if ql in (x.title.lower() + " " + x.code.lower() + " " + x.article.lower())]
    return items

@router.get("/{authority_id}")
def get_authority(authority_id: str):
    if authority_id not in AUTHORITIES:
        raise HTTPException(status_code=404, detail="authority not found")
    return {
        "authority": AUTHORITIES[authority_id],
        "snippets": SNIPPETS.get(authority_id, [])
    }

class SeedReq(BaseModel):
    items: List[Authority]

@router.post("/seed")
def seed(req: SeedReq):
    for item in req.items:
        AUTHORITIES[item.id] = item
        SNIPPETS.setdefault(item.id, [])
    return {"ok": True, "count": len(req.items)}

class SnippetReq(BaseModel):
    snippet: str
    pinpoint: Optional[str] = None
    source_ref: str

@router.post("/{authority_id}/snippets")
def add_snippet(authority_id: str, req: SnippetReq):
    if authority_id not in AUTHORITIES:
        raise HTTPException(status_code=404, detail="authority not found")
    sid = "SNIP-" + uuid.uuid4().hex[:12]
    sn = Snippet(
        id=sid,
        authority_id=authority_id,
        snippet=req.snippet,
        pinpoint=req.pinpoint,
        source_ref=req.source_ref,
        created_at=datetime.datetime.utcnow().isoformat() + "Z"
    )
    SNIPPETS.setdefault(authority_id, []).append(sn)
    return {"ok": True, "snippet": sn}
