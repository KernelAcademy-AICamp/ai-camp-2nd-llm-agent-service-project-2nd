import json
import os
from uuid import UUID, uuid4
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def _load_json(relpath: str):
    with open(os.path.join(BASE_DIR, relpath), "r", encoding="utf-8") as f:
        return json.load(f)

class DraftEngine:
    def __init__(self):
        self.claim_templates = _load_json("data/claim_templates.v2_06.json")
        self.blocks = _load_json("data/draft_blocks.v2_06.json")
        self.legal_refs = _load_json("data/legal_refs.v2_06.json")

    # ---------- DB integration stubs ----------
    def load_case_context_stub(self, case_id: UUID) -> Dict[str, Any]:
        # 실제 프로젝트에선 case_id로 DB에서 아래를 읽어야 함:
        # - parties, children, income, assets/debts
        # - keypoints(kind별 카운트 + 각 keypoint가 연결된 evidence/extract)
        # - evidence status/tag
        return {
            "parties": {
                "plaintiff": {"name": "원고(샘플)", "addr": "주소(샘플)"},
                "defendant": {"name": "피고(샘플)", "addr": "주소(샘플)"}
            },
            "keypoints": [
                {"id":"kp1","kind":"DATE_EVENT","text":"2024-05-01 부정행위 의심 정황 확인"},
            ],
            "evidence": [
                {"id":"ev1","tags":["CHAT_EXPORT"],"status":"ADMISSIBLE","label":"갑 제1호증"},
            ],
            "timeline": [
                {"date":"2024-05-01","title":"정황 확인","ref_keypoint_id":"kp1"}
            ]
        }

    # ---------- core ----------
    def generate(self, case_id: UUID, req: Dict[str, Any], case_ctx: Dict[str, Any]) -> Dict[str, Any]:
        draft_id = uuid4()
        selected_claims = set(req.get("selected_claims") or [])
        selected_grounds = set(req.get("selected_grounds") or [])
        draft_kind = req.get("draft_kind")

        blocks_out = []
        warnings = []

        # precompute availability
        keypoint_kinds = {kp["kind"] for kp in case_ctx.get("keypoints", [])}
        evidence_tags = set()
        admissible_evidence = []
        for ev in case_ctx.get("evidence", []):
            for t in ev.get("tags", []):
                evidence_tags.add(t)
            if ev.get("status") == "ADMISSIBLE":
                admissible_evidence.append(ev)

        for order_no, blk in enumerate(self.blocks, start=1):
            # required_claims
            if blk["required_claims"]:
                if not set(blk["required_claims"]).issubset(selected_claims | set(["DIVORCE"])) and "DIVORCE" not in selected_claims:
                    # allow DIVORCE as baseline when building judicial complaint
                    continue

            # required_grounds
            if blk["required_grounds"]:
                if not set(blk["required_grounds"]).issubset(selected_grounds):
                    continue

            missing = []
            # required_keypoints
            for k in blk.get("required_keypoint_kinds", []):
                if k not in keypoint_kinds:
                    missing.append({"type":"KEYPOINT_KIND","value":k})

            # required evidence tags (soft requirement: any one tag present)
            req_tags = blk.get("required_evidence_tags", [])
            if req_tags and not (set(req_tags) & evidence_tags):
                missing.append({"type":"EVIDENCE_TAG_ANY_OF","value":req_tags})

            citations = []
            # citation rule
            if blk.get("min_citations", 0) >= 1:
                # simplistic: use first admissible evidence as citation
                if admissible_evidence:
                    citations.append({"evidence_id": admissible_evidence[0]["id"], "label": admissible_evidence[0].get("label")})
                else:
                    missing.append({"type":"CITATION","value":"ADMISSIBLE evidence required"})

            is_todo = len(missing) > 0 and blk.get("min_citations", 0) >= 1

            content_html = blk["body_template"]
            if is_todo:
                content_html = f"<p><b>[TODO]</b> 근거 부족으로 '{blk['title']}' 블록을 생성할 수 없습니다.</p>"

            blocks_out.append({
                "block_id": blk["block_id"],
                "title": blk["title"],
                "order_no": order_no,
                "html": content_html,
                "citations": citations,
                "missing": missing,
                "is_todo": is_todo
            })

        status = "COMPLETE" if all(not b["is_todo"] for b in blocks_out) else "INCOMPLETE"
        return {
            "draft_id": str(draft_id),
            "case_id": str(case_id),
            "draft_kind": draft_kind,
            "status": status,
            "warnings": warnings,
            "blocks": blocks_out
        }
