"""Analytics routes."""

import json
from fastapi import APIRouter
from ..database import get_db, USE_PG

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/velocity")
def velocity():
    """Tasks completed per sprint, by assignee."""
    conn = get_db()
    rows = conn.execute("""
        SELECT sprint_id, assignee, COUNT(*) as completed
        FROM tasks WHERE status = 'done' AND sprint_id IS NOT NULL
        GROUP BY sprint_id, assignee
        ORDER BY sprint_id
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/burndown")
def burndown():
    """Sprint burndown data — tasks completed over time."""
    conn = get_db()
    rows = conn.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as completed
        FROM activity_log WHERE action = 'moved' AND to_status = 'done'
        GROUP BY DATE(timestamp)
        ORDER BY day
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/ai-ratio")
def ai_ratio():
    """AI vs human task completion ratio."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            CASE WHEN t.assignee IN (SELECT id FROM team_members WHERE type = 'ai-agent')
                 THEN 'ai' ELSE 'human' END as worker_type,
            COUNT(*) as count
        FROM tasks t WHERE t.status = 'done'
        GROUP BY worker_type
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/cycle-time")
def cycle_time():
    """Average cycle time (created to done) in days."""
    conn = get_db()
    if USE_PG:
        sql = """SELECT assignee,
                   AVG(EXTRACT(EPOCH FROM (updated_at - created_at)) / 86400) as avg_days,
                   COUNT(*) as count
                FROM tasks WHERE status = 'done' GROUP BY assignee"""
    else:
        sql = """SELECT assignee,
                   AVG(JULIANDAY(updated_at) - JULIANDAY(created_at)) as avg_days,
                   COUNT(*) as count
                FROM tasks WHERE status = 'done' GROUP BY assignee"""
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/summary")
def summary():
    """Overall dashboard summary stats."""
    conn = get_db()

    total = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()["count"]
    by_status = conn.execute(
        "SELECT status, COUNT(*) as count FROM tasks GROUP BY status"
    ).fetchall()
    by_priority = conn.execute(
        "SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority"
    ).fetchall()
    by_type = conn.execute(
        "SELECT type, COUNT(*) as count FROM tasks GROUP BY type"
    ).fetchall()
    by_assignee = conn.execute(
        "SELECT assignee, COUNT(*) as count FROM tasks WHERE assignee IS NOT NULL GROUP BY assignee"
    ).fetchall()

    conn.close()

    return {
        "total_tasks": total,
        "by_status": {r["status"]: r["count"] for r in by_status},
        "by_priority": {r["priority"]: r["count"] for r in by_priority},
        "by_type": {r["type"]: r["count"] for r in by_type},
        "by_assignee": {r["assignee"]: r["count"] for r in by_assignee},
    }
