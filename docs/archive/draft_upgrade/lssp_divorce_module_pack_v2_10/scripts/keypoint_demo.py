import json
from pathlib import Path
from server_fastapi_stub.services.keypoint_extractor import load_rules, extract_candidates_rule_based

RULES_PATH = Path(__file__).resolve().parents[1] / "data" / "keypoint_rules.v2_10.json"

sample = """2025-12-01 A: 미안, 나 바람 피웠어.
2025-12-02 B: 집 나갈게. 돈 좀 송금해."""

if __name__ == "__main__":
    rules = load_rules(str(RULES_PATH))
    cands = extract_candidates_rule_based("CHAT_EXPORT", sample, rules)
    print(json.dumps(cands, ensure_ascii=False, indent=2))
