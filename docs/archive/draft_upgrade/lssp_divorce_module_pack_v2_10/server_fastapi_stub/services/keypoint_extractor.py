import json, re
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class Rule:
    evidence_type: str
    kind: str
    name: str
    pattern: str
    flags: str
    value_template: Dict[str, Any]
    ground_tags: List[str]
    base_confidence: float
    base_materiality: int

def _flags(s: str) -> int:
    f = 0
    s = (s or "").lower()
    if "i" in s: f |= re.IGNORECASE
    if "m" in s: f |= re.MULTILINE
    if "s" in s: f |= re.DOTALL
    return f

def load_rules(path: str) -> List[Rule]:
    obj = json.loads(open(path, "r", encoding="utf-8").read())
    out: List[Rule] = []
    for r in obj.get("rules", []):
        out.append(Rule(
            evidence_type=r["evidence_type"],
            kind=r["kind"],
            name=r["name"],
            pattern=r["pattern"],
            flags=r.get("flags",""),
            value_template=r.get("value_template",{}),
            ground_tags=r.get("ground_tags",[]),
            base_confidence=float(r.get("base_confidence",0.5)),
            base_materiality=int(r.get("base_materiality",40)),
        ))
    return out

def _render(tpl: Dict[str, Any], match: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k,v in tpl.items():
        out[k] = v.replace("${match}", match) if isinstance(v, str) else v
    if "text" not in out:
        out["text"] = match
    return out

def extract_candidates_rule_based(evidence_type: str, text: str, rules: List[Rule]) -> List[Dict[str, Any]]:
    cands: List[Dict[str, Any]] = []
    for rule in rules:
        if rule.evidence_type != evidence_type:
            continue
        rx = re.compile(rule.pattern, _flags(rule.flags))
        for m in rx.finditer(text):
            mt = m.group(0)
            cands.append({
                "kind": rule.kind,
                "value": _render(rule.value_template, mt),
                "ground_tags": rule.ground_tags,
                "confidence": rule.base_confidence,
                "materiality": rule.base_materiality,
                "source_span": {"source":"text", "start": m.start(), "end": m.end()},
                "rule_name": rule.name
            })
    return cands
