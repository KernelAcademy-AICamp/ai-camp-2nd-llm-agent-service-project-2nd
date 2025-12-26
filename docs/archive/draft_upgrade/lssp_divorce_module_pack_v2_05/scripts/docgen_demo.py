import json
from pathlib import Path

from server_python.app.services.doc_render import render_docx

DOC_TYPES = [
  "CONSENSUAL_INTENT_FORM",
  "CHILD_CUSTODY_AGREEMENT",
  "EVIDENCE_INDEX",
  "ASSET_INVENTORY",
  "CASE_TIMELINE_SUMMARY",
]

def main():
    base = Path(__file__).resolve().parents[1]
    payload = json.loads((base / "data" / "demo_case.json").read_text(encoding="utf-8"))
    out_dir = base / "out"
    out_dir.mkdir(exist_ok=True)
    for dt in DOC_TYPES:
        out = out_dir / f"demo_{dt}.docx"
        render_docx(dt, payload, out)
        print("generated:", out)

if __name__ == "__main__":
    main()
