"""Standup generation routes."""

import json
from datetime import datetime, date
from fastapi import APIRouter
from ..database import get_db

router = APIRouter(prefix="/api/standup", tags=["standup"])


@router.get("/today")
def get_today_standup():
    return _generate_standup()


@router.post("/generate")
def generate_standup():
    return _generate_standup()


@router.get("/history")
def standup_history():
    conn = get_db()
    # Build standups from activity log grouped by date
    rows = conn.execute(
        "SELECT DATE(timestamp) as day, COUNT(*) as actions FROM activity_log GROUP BY DATE(timestamp) ORDER BY day DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _generate_standup():
    conn = get_db()

    # Get tasks by status
    statuses = {}
    for status in ["backlog", "in-progress", "review", "done", "blocked"]:
        rows = conn.execute(
            "SELECT id, title, assignee, priority, type FROM tasks WHERE status = ? ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END",
            (status,)
        ).fetchall()
        statuses[status] = [dict(r) for r in rows]

    total = sum(len(ts) for ts in statuses.values())
    done_count = len(statuses.get("done", []))
    progress_pct = int(done_count / total * 100) if total else 0

    # Recent activity
    recent = conn.execute(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    conn.close()

    return {
        "date": date.today().isoformat(),
        "generated_at": datetime.utcnow().isoformat(),
        "completed": statuses.get("done", []),
        "in_progress": statuses.get("in-progress", []),
        "review": statuses.get("review", []),
        "blocked": statuses.get("blocked", []),
        "high_priority_backlog": [t for t in statuses.get("backlog", []) if t.get("priority") in ("P0", "P1")],
        "progress": {
            "total": total,
            "done": done_count,
            "percentage": progress_pct,
        },
        "recent_activity": [dict(r) for r in recent],
    }
