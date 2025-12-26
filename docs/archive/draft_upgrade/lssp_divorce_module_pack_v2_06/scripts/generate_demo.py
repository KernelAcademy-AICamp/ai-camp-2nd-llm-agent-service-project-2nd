import json
from uuid import UUID
from server_python.draft_engine import DraftEngine

engine = DraftEngine()

case_id = UUID("00000000-0000-0000-0000-000000000001")
req = {
  "draft_kind": "JUDICIAL_COMPLAINT",
  "selected_claims": ["DIVORCE", "ALIMONY", "PROPERTY_DIVISION"],
  "selected_grounds": ["G1"],
  "options": {"require_admissible_only": True}
}
ctx = engine.load_case_context_stub(case_id)
out = engine.generate(case_id=case_id, req=req, case_ctx=ctx)
print(json.dumps(out, ensure_ascii=False, indent=2))
