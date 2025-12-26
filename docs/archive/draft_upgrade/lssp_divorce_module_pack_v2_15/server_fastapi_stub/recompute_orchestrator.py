from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import hashlib
import json
import uuid

# This is a pure-Python orchestration stub.
# Plug it into:
# - your FastAPI route layer (enqueue)
# - your DB/repo layer (load inputs, persist outputs)
# - your worker (execute job)

@dataclass
class Job:
    job_id: str
    case_id: str
    trigger_event: str
    trigger_entity: Optional[str]
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class StepResult:
    step_name: str
    status: str
    metrics: Dict[str, Any]
    error_message: Optional[str] = None

class RecomputeOrchestrator:
    def __init__(self, graph: Dict[str, Any], triggers: Dict[str, Any]):
        self.graph = graph
        self.triggers = triggers

    def plan(self, trigger_event: str) -> List[str]:
        if trigger_event not in self.triggers["events"]:
            raise ValueError(f"Unknown trigger_event: {trigger_event}")
        requested = self.triggers["events"][trigger_event]["modules"]
        # expand with dependencies (DAG)
        deps = {m["name"]: set(m.get("depends_on", [])) for m in self.graph["modules"]}
        expanded: set[str] = set()

        def visit(mod: str):
            for d in deps.get(mod, set()):
                if d not in expanded:
                    visit(d)
            expanded.add(mod)

        for m in requested:
            visit(m)

        # keep graph topological order
        ordered: List[str] = []
        for m in self.graph["topological_order"]:
            if m in expanded:
                ordered.append(m)
        return ordered

    def compute_input_hash(self, case_id: str, trigger_event: str, inputs: Dict[str, Any]) -> str:
        payload = {"case_id": case_id, "trigger_event": trigger_event, "inputs": inputs}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def run(self, job: Job, inputs: Dict[str, Any]) -> Tuple[Job, List[StepResult]]:
        # NOTE: Real implementation must:
        # - acquire case-level lock
        # - read+write DB
        # - call downstream modules
        job.started_at = datetime.utcnow()
        steps: List[StepResult] = []

        try:
            plan = self.plan(job.trigger_event)
            job.input_hash = self.compute_input_hash(job.case_id, job.trigger_event, inputs)
            job.status = "running"

            for step_name in plan:
                # stub step execution
                res = self._execute_step(step_name, job.case_id, inputs)
                steps.append(res)
                if res.status == "failed":
                    job.status = "failed"
                    job.error_message = res.error_message
                    break

            if job.status != "failed":
                job.status = "succeeded"
                # output_hash stub
                job.output_hash = hashlib.sha256(("ok:" + job.input_hash).encode("utf-8")).hexdigest()

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)

        job.finished_at = datetime.utcnow()
        return job, steps

    def _execute_step(self, step_name: str, case_id: str, inputs: Dict[str, Any]) -> StepResult:
        # Replace this with calls to your real modules.
        # Example:
        #   if step_name == "process_engine": process_engine.apply_event(...)
        #   if step_name == "timeline": timeline.recompute(...)
        # etc.
        metrics: Dict[str, Any] = {}
        try:
            if step_name == "process_engine":
                metrics["deadlines_created"] = 2 if inputs.get("confirmation_date") else 0
            elif step_name == "timeline":
                metrics["events_written"] = 5
            elif step_name == "evidence_keypoints":
                metrics["keypoints"] = 12
            elif step_name == "checklists":
                metrics["items"] = 20
            elif step_name == "legal_recommender":
                metrics["recommendations"] = 6
            elif step_name == "draft_preview":
                metrics["sections"] = 8
            elif step_name == "warnings":
                metrics["warnings"] = 1
            else:
                metrics["noop"] = True
            return StepResult(step_name=step_name, status="succeeded", metrics=metrics)
        except Exception as e:
            return StepResult(step_name=step_name, status="failed", metrics={}, error_message=str(e))


def new_job(case_id: str, trigger_event: str, trigger_entity: Optional[str] = None) -> Job:
    return Job(
        job_id=str(uuid.uuid4()),
        case_id=case_id,
        trigger_event=trigger_event,
        trigger_entity=trigger_entity,
        status="queued",
        created_at=datetime.utcnow(),
    )
