from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/legal", tags=["legal-recommender"])

class Keypoint(BaseModel):
    kind: str
    value: Dict[str, Any] = {}
    materiality: int = 0
    ground_tags: List[str] = []

class CaseContext(BaseModel):
    case_id: str
    divorce_type: str
    process_stage: Optional[str] = None
    ground_scores: Dict[str, float] = {}
    keypoints: List[Keypoint] = []

class RecItem(BaseModel):
    id: str
    title: str
    tags: List[str] = []
    score: float
    reasons: List[str] = []

class PrecedentItem(BaseModel):
    id: str
    case_no: str
    gist: str
    tags: List[str] = []
    score: float
    reasons: List[str] = []

class Recommendations(BaseModel):
    case_id: str
    authorities: List[RecItem] = []
    precedents: List[PrecedentItem] = []

def _load_json(path: str) -> Any:
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _score(ctx: CaseContext, rules: Dict[str, Any],
           authorities: List[Dict[str, Any]], precedents: List[Dict[str, Any]]
           ) -> Tuple[List[RecItem], List[PrecedentItem]]:
    sig = rules.get("signals", {})
    kp_boosts = sig.get("keypoints", {})
    ground_sig = sig.get("grounds", {})
    process_sig = sig.get("process", {})

    derived_tags: List[str] = []
    kp_total_boost = 0.0
    for kp in ctx.keypoints:
        rule = kp_boosts.get(kp.kind)
        if rule:
            kp_total_boost += float(rule.get("boost", 0))
            derived_tags += rule.get("adds_tags", [])
    derived_tags = list(dict.fromkeys(derived_tags))

    top_grounds = sorted(ctx.ground_scores.items(), key=lambda x: x[1], reverse=True)[:2]
    ground_boost_total = 0.0
    ground_keywords: List[str] = []
    for g, sc in top_grounds:
        gr = ground_sig.get(g, {})
        ground_boost_total += float(gr.get("boost", 0)) * (float(sc) / 100.0 if sc else 1.0)
        ground_keywords += gr.get("keywords", [])
    ground_keywords = list(dict.fromkeys(ground_keywords))

    proc = process_sig.get(ctx.divorce_type, {})
    required_authorities = set(proc.get("required_authorities", []))
    proc_boost = float(proc.get("boost", 0))

    def score_item(item: Dict[str, Any], base: float) -> Tuple[float, List[str]]:
        tags = item.get("tags", [])
        title = item.get("title", "") or item.get("gist", "")
        score = base + proc_boost + ground_boost_total + kp_total_boost
        reasons: List[str] = []

        tag_hits = set(tags).intersection(set(derived_tags + [g for g, _ in top_grounds]))
        if tag_hits:
            score += 8 * len(tag_hits)
            reasons.append("tag match: " + ", ".join(sorted(tag_hits)))

        kw_hits = [kw for kw in ground_keywords if kw and kw in title]
        if kw_hits:
            score += 5 * len(kw_hits)
            reasons.append("keyword match: " + ", ".join(kw_hits[:3]))

        if item.get("authority_code") in required_authorities:
            score += 50
            reasons.append("required for this process")

        if kp_total_boost:
            reasons.append(f"keypoint signals +{int(kp_total_boost)}")

        if top_grounds:
            reasons.append("top grounds: " + ", ".join([g for g, _ in top_grounds]))

        return score, reasons[:5]

    auth_out: List[RecItem] = []
    for a in authorities:
        s, r = score_item(a, base=50)
        auth_out.append(RecItem(
            id=a.get("authority_id", a.get("id", "UNKNOWN")),
            title=a.get("title", "Untitled"),
            tags=a.get("tags", []),
            score=s,
            reasons=r,
        ))
    auth_out.sort(key=lambda x: x.score, reverse=True)

    prec_out: List[PrecedentItem] = []
    for p in precedents:
        p2 = dict(p)
        p2["title"] = p.get("gist", "")
        s, r = score_item(p2, base=40)
        prec_out.append(PrecedentItem(
            id=p.get("precedent_id", p.get("id", "UNKNOWN")),
            case_no=p.get("case_no", "UNKNOWN"),
            gist=p.get("gist", ""),
            tags=p.get("tags", []),
            score=s,
            reasons=r,
        ))
    prec_out.sort(key=lambda x: x.score, reverse=True)

    return auth_out[:10], prec_out[:10]

@router.post("/recommendations", response_model=Recommendations)
def recommend(ctx: CaseContext):
    import os
    root = os.path.dirname(__file__)
    rules = _load_json(os.path.join(root, "..", "data", "recommender_rules.v2_12.json"))

    # Authorities should come from DB. For local demo, load v2.11 seed if present.
    authorities: List[Dict[str, Any]] = []
    a_path = os.path.join(root, "..", "data", "law_articles.v2_11.json")
    if os.path.exists(a_path):
        raw = _load_json(a_path)
        for a in raw.get("authorities", raw if isinstance(raw, dict) else []):
            authorities.append(a)

    p_path = os.path.join(root, "..", "data", "precedent_index.v2_12.json")
    precedents = _load_json(p_path).get("precedents", [])

    auth, prec = _score(ctx, rules, authorities, precedents)
    return Recommendations(case_id=ctx.case_id, authorities=auth, precedents=prec)
