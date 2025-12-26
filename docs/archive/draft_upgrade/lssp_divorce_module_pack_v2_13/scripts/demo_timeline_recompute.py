"""Demo: generate a few timeline events for a case.

Run:
  python scripts/demo_timeline_recompute.py

This is a local-only demo; wire to your DB + services in production.
"""

import uuid
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

def main():
    case_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    events = [
        dict(category="PROCEDURE", event_type="STAGE_CHANGED", title="조정 신청", summary="조정전치 단계 진입", occurred_at=now - timedelta(days=12), severity=1, risk_score=0, penalty_type="NONE", tags=["PROCEDURE"], meta={"stage":"MEDIATION"}),
        dict(category="EVIDENCE", event_type="EVIDENCE_UPLOADED", title="증거 업로드", summary="카톡 대화 내역", occurred_at=now - timedelta(days=10), severity=1, risk_score=0, penalty_type="NONE", tags=["G1"], meta={"review_status":"UNREVIEWED","storage_folder":"G1_ADULTERY"}),
        dict(category="FACT", event_type="KEYPOINT_APPROVED", title="핵심포인트 확정", summary="상간자 특정 + 날짜", occurred_at=now - timedelta(days=9), severity=1, risk_score=0, penalty_type="NONE", tags=["G1"], meta={"kind":"PERSON+DATE"}),
        dict(category="DEADLINE", event_type="DEADLINE_DUE", title="재판/조정 이혼 신고 마감", summary="확정일로부터 1개월", occurred_at=now + timedelta(days=5), severity=4, risk_score=70, penalty_type="ADMIN_FINE", tags=["REPORTING"], meta={"rule_id":"JUDICIAL_REPORT_DUE","due_at":(now+timedelta(days=5)).isoformat()}),
    ]

    out = {
        "case_id": case_id,
        "events": [
            {**e, "occurred_at": e["occurred_at"].isoformat()} for e in events
        ]
    }

    Path("out").mkdir(exist_ok=True)
    Path("out/timeline_demo.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote out/timeline_demo.json for case:", case_id)

if __name__ == "__main__":
    main()
