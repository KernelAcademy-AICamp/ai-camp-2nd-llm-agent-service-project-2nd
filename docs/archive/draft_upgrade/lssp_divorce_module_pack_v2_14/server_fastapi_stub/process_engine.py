from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import uuid

# NOTE: This is a stub. Plug into your DB/repo layer.
# Philosophy:
# - Apply event -> validate guards -> transition state
# - Effects create deadlines / timeline events in downstream services
# - Return warnings (missing steps, deadline risks)

@dataclass
class TransitionResult:
    case_id: str
    machine_name: str
    prev_state: str
    next_state: str
    deadlines_created: List[str]
    warnings: List[Dict[str, Any]]

class ProcessEngine:
    def __init__(self, machine_defs: Dict[str, Any], warning_rules: Dict[str, Any]):
        self.machine_defs = machine_defs
        self.warning_rules = warning_rules

    def apply_event(self, case_id: str, machine_name: str, state_code: str, event_code: str, payload: Dict[str, Any]) -> TransitionResult:
        machine = self._get_machine(machine_name)
        prev_state = state_code
        next_state, deadlines = self._transition(machine, state_code, event_code, payload)
        warnings = self._evaluate_warnings(machine_name, next_state, payload)
        return TransitionResult(
            case_id=case_id,
            machine_name=machine_name,
            prev_state=prev_state,
            next_state=next_state,
            deadlines_created=deadlines,
            warnings=warnings,
        )

    def _get_machine(self, machine_name: str) -> Dict[str, Any]:
        for m in self.machine_defs["machines"]:
            if m["name"] == machine_name:
                return m
        raise ValueError(f"Unknown machine_name: {machine_name}")

    def _transition(self, machine: Dict[str, Any], state_code: str, event_code: str, payload: Dict[str, Any]) -> Tuple[str, List[str]]:
        deadlines_created: List[str] = []
        # choose first matching transition (ordered in defs)
        for t in machine.get("transitions", []):
            if t["from"] != state_code:
                continue
            if t["event"] != event_code:
                continue
            # guard evaluation is stubbed; real code should parse expressions safely.
            guards = t.get("guards", [])
            if any(g == "false" for g in guards):
                # blocked transition, keep state
                return state_code, deadlines_created
            # effects
            for eff in t.get("effects", []):
                if eff.startswith("create_deadline:"):
                    deadlines_created.append(eff.split(":", 1)[1])
            return t["to"], deadlines_created
        # no transition -> keep
        return state_code, deadlines_created

    def _evaluate_warnings(self, machine_name: str, state_code: str, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Very small stub: returns static example warnings.
        out: List[Dict[str, Any]] = []
        for r in self.warning_rules.get("rules", []):
            if r["when"]["machine"] != machine_name:
                continue
            if state_code not in r["when"].get("state_in", []):
                continue
            # expression engine omitted; you will evaluate against merged ctx (case dates + now).
            # Here we only emit when caller explicitly flags it.
            if ctx.get("_emit_rule") == r["id"]:
                out.append({"rule_id": r["id"], "severity": r["severity"], "message": r["message"], "fix_hint": r["fix_hint"]})
        return out
