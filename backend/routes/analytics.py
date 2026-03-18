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


@router.get("/workload")
def workload():
    """Per-assignee task counts grouped by status — for heatmap."""
    conn = get_db()
    rows = conn.execute("""
        SELECT assignee, status, COUNT(*) as count
        FROM tasks WHERE assignee IS NOT NULL AND assignee != ''
        GROUP BY assignee, status
        ORDER BY assignee, status
    """).fetchall()
    conn.close()

    heatmap = {}
    for r in rows:
        assignee = r["assignee"]
        if assignee not in heatmap:
            heatmap[assignee] = {}
        heatmap[assignee][r["status"]] = r["count"]
    return {"workload": heatmap}


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


@router.get("/ai-velocity")
def ai_velocity(project_id: str = None):
    """Human vs AI velocity split by sprint."""
    conn = get_db()
    params = []
    filter_clause = ""
    if project_id:
        filter_clause = " AND t.project_id = ?"
        params.append(project_id)

    rows = conn.execute(
        f"""SELECT t.sprint_id,
               CASE WHEN tm.type = 'ai-agent' THEN 'ai' ELSE 'human' END as worker_type,
               COUNT(*) as tasks_done,
               SUM(COALESCE(t.estimated_hours, 0)) as story_points
            FROM tasks t
            LEFT JOIN team_members tm ON t.assignee = tm.id
            WHERE t.status = 'done' AND t.sprint_id IS NOT NULL {filter_clause}
            GROUP BY t.sprint_id, worker_type
            ORDER BY t.sprint_id, worker_type""",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/ai-cost-per-point")
def ai_cost_per_point(project_id: str = None):
    """Cost per story point by agent."""
    conn = get_db()
    params = []
    filter_clause = "WHERE s.task_id IS NOT NULL"
    if project_id:
        filter_clause += " AND s.project_id = ?"
        params.append(project_id)

    rows = conn.execute(
        f"""SELECT s.agent_id,
               SUM(s.cost_usd) as total_cost,
               SUM(COALESCE(t.estimated_hours, 0)) as total_points,
               COUNT(DISTINCT s.task_id) as tasks_touched,
               CASE WHEN SUM(COALESCE(t.estimated_hours, 0)) > 0
                    THEN SUM(s.cost_usd) / SUM(COALESCE(t.estimated_hours, 0))
                    ELSE 0 END as cost_per_point
            FROM ai_agent_sessions s
            LEFT JOIN tasks t ON s.task_id = t.id
            {filter_clause}
            GROUP BY s.agent_id
            ORDER BY cost_per_point ASC""",
        params
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/agent-performance")
def agent_performance(project_id: str = None):
    """Per-agent performance: sessions, tokens, cost, tasks completed."""
    conn = get_db()
    agent_params = []
    agent_filter = "WHERE 1=1"
    if project_id:
        agent_filter += " AND project_id = ?"
        agent_params.append(project_id)

    session_rows = conn.execute(
        f"""SELECT agent_id, model,
               COUNT(*) as total_sessions,
               SUM(total_tokens) as total_tokens,
               SUM(cost_usd) as total_cost,
               AVG(duration_seconds) as avg_duration,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_sessions
            FROM ai_agent_sessions
            {agent_filter}
            GROUP BY agent_id, model""",
        agent_params
    ).fetchall()

    task_params = []
    task_filter = "WHERE t.status = 'done' AND tm.type = 'ai-agent'"
    if project_id:
        task_filter += " AND t.project_id = ?"
        task_params.append(project_id)

    task_rows = conn.execute(
        f"""SELECT t.assignee as agent_id, COUNT(*) as tasks_done
            FROM tasks t
            LEFT JOIN team_members tm ON t.assignee = tm.id
            {task_filter}
            GROUP BY t.assignee""",
        task_params
    ).fetchall()
    tasks_by_agent = {r["agent_id"]: r["tasks_done"] for r in task_rows}

    conn.close()
    result = []
    for r in session_rows:
        d = dict(r)
        d["tasks_done"] = tasks_by_agent.get(r["agent_id"], 0)
        result.append(d)
    return result
