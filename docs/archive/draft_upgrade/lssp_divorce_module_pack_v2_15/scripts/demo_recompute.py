import json
from pathlib import Path
from datetime import date

from server_fastapi_stub.recompute_orchestrator import RecomputeOrchestrator, new_job

ROOT = Path(__file__).resolve().parents[1]
graph = json.loads((ROOT / "data" / "recompute_graph.v2_15.json").read_text(encoding="utf-8"))
triggers = json.loads((ROOT / "data" / "recompute_triggers.v2_15.json").read_text(encoding="utf-8"))

orch = RecomputeOrchestrator(graph, triggers)

# Example: consensual divorce confirmation received today
job = new_job(case_id="11111111-1111-1111-1111-111111111111", trigger_event="process_event_added", trigger_entity="process_event:aaaa")
inputs = {
  "confirmation_date": str(date.today()),
  "has_minor_child": True,
  "legal_ground": "G1"
}

job, steps = orch.run(job, inputs)

print("JOB:", job.status, job.job_id, job.input_hash)
for s in steps:
    print("-", s.step_name, s.status, s.metrics, (s.error_message or ""))
