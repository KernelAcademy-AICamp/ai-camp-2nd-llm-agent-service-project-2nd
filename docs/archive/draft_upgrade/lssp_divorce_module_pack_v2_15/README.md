# LSSP Divorce Module Pack v2.15
Topic: **Integrated Recompute Pipeline (Derived-State Orchestration + Triggers)**

This pack defines how the LEH/LSSP system should **recompute derived artifacts** (process state, deadlines, timeline, warnings, recommendations, drafts) whenever any input changes (evidence upload, 상담 기록, 일정 변경, 프로세스 이벤트 등).

## What you get
- DB DDL for recompute job tracking & per-module versions
- Event→Module trigger map (JSON)
- Recompute DAG (JSON)
- Backend orchestration stub (pure Python, plug into FastAPI / worker)
- UI spec for "Recompute Status" widget

## How to apply in the repo
- Put `docs/*` into your `/docs` folder (or keep as-is and link from docs index)
- Apply SQL in `docs/DB_DDL_RECOMPUTE_V2_15.sql` to your Postgres
- Wire `server_fastapi_stub/recompute_orchestrator.py` into backend service layer
- Use `data/*` as system config (load on boot, cache)

