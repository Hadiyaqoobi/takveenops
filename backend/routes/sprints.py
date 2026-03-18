"""Sprint management routes."""

import csv
import io
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..database import get_db
from ..models import SprintCreate, SprintUpdate

router = APIRouter(prefix="/api/sprints", tags=["sprints"])


@router.get("")
def list_sprints():
    conn = get_db()
    rows = conn.execute("SELECT * FROM sprints ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("")
def create_sprint(sprint: SprintCreate):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO sprints (name, goal, start_date, end_date) VALUES (?, ?, ?, ?)",
        (sprint.name, sprint.goal, sprint.start_date, sprint.end_date)
    )
    sprint_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    conn.close()
    return dict(row)


@router.put("/{sprint_id}")
def update_sprint(sprint_id: int, sprint: SprintUpdate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Sprint not found")

    updates = {k: v for k, v in sprint.model_dump(exclude_unset=True).items()}
    if not updates:
        conn.close()
        return dict(existing)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [sprint_id]
    conn.execute(f"UPDATE sprints SET {set_clause} WHERE id = ?", values)
    conn.commit()

    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/{sprint_id}/tasks")
def get_sprint_tasks(sprint_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE sprint_id = ? ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END",
        (sprint_id,)
    ).fetchall()
    conn.close()

    from .tasks import row_to_dict
    return [row_to_dict(r) for r in rows]


@router.get("/{sprint_id}/suggestions")
def get_sprint_suggestions(sprint_id: int):
    """Suggest tasks for sprint based on priority and team capacity."""
    conn = get_db()
    sprint = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    if not sprint:
        conn.close()
        raise HTTPException(404, "Sprint not found")

    # Get backlog tasks not in any sprint, ordered by priority
    backlog = conn.execute(
        "SELECT * FROM tasks WHERE (sprint_id IS NULL OR sprint_id = 0) AND status NOT IN ('done') "
        "ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END, created_at ASC"
    ).fetchall()

    # Get current sprint tasks
    sprint_tasks = conn.execute("SELECT * FROM tasks WHERE sprint_id = ?", (sprint_id,)).fetchall()

    # Team capacity
    members = conn.execute("SELECT id, name, max_concurrent_tasks FROM team_members").fetchall()

    # Calculate load per member
    member_load = {}
    for m in members:
        member_load[m["id"]] = {
            "name": m["name"],
            "capacity": m["max_concurrent_tasks"],
            "current": 0,
        }
    for t in sprint_tasks:
        if t["assignee"] and t["assignee"] in member_load and t["status"] != "done":
            member_load[t["assignee"]]["current"] += 1

    # Warnings
    warnings = []
    for mid, info in member_load.items():
        if info["current"] >= info["capacity"]:
            warnings.append(f"{info['name']} is at capacity ({info['current']}/{info['capacity']} tasks)")

    high_priority_backlog = [dict(t) for t in backlog if t["priority"] in ("P0", "P1")]
    if high_priority_backlog:
        warnings.append(f"{len(high_priority_backlog)} high-priority task(s) in backlog")

    conn.close()

    from .tasks import row_to_dict
    return {
        "suggestions": [row_to_dict(t) for t in backlog[:15]],
        "sprint_tasks": [row_to_dict(t) for t in sprint_tasks],
        "team_capacity": list(member_load.values()),
        "warnings": warnings,
    }


@router.post("/{sprint_id}/add-task")
def add_task_to_sprint(sprint_id: int, body: dict):
    task_id = body.get("task_id", "")
    if not task_id:
        raise HTTPException(400, "task_id is required")
    conn = get_db()
    conn.execute("UPDATE tasks SET sprint_id = ? WHERE id = ?", (sprint_id, task_id.upper()))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{sprint_id}/remove-task")
def remove_task_from_sprint(sprint_id: int, body: dict):
    task_id = body.get("task_id", "")
    if not task_id:
        raise HTTPException(400, "task_id is required")
    conn = get_db()
    conn.execute("UPDATE tasks SET sprint_id = NULL WHERE id = ? AND sprint_id = ?", (task_id.upper(), sprint_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/{sprint_id}/report")
def sprint_report(sprint_id: int, format: str = "json"):
    """Sprint report with completion %, per-assignee breakdown, velocity."""
    conn = get_db()
    sprint = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    if not sprint:
        conn.close()
        raise HTTPException(404, "Sprint not found")

    tasks = conn.execute("SELECT * FROM tasks WHERE sprint_id = ?", (sprint_id,)).fetchall()
    conn.close()

    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "done")
    completion_pct = round((done / total * 100) if total else 0, 1)

    # Per-assignee breakdown
    by_assignee = {}
    for t in tasks:
        a = t["assignee"] or "Unassigned"
        if a not in by_assignee:
            by_assignee[a] = {"total": 0, "done": 0, "in_progress": 0, "estimated_hours": 0}
        by_assignee[a]["total"] += 1
        if t["status"] == "done":
            by_assignee[a]["done"] += 1
        elif t["status"] == "in-progress":
            by_assignee[a]["in_progress"] += 1
        by_assignee[a]["estimated_hours"] += t["estimated_hours"] or 0

    report = {
        "sprint": dict(sprint),
        "total_tasks": total,
        "completed": done,
        "completion_pct": completion_pct,
        "by_assignee": by_assignee,
    }

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Task ID", "Title", "Type", "Priority", "Status", "Assignee", "Estimated Hours"])
        for t in tasks:
            writer.writerow([t["id"], t["title"], t["type"], t["priority"], t["status"], t["assignee"] or "", t["estimated_hours"] or 0])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sprint-{sprint_id}-report.csv"}
        )

    return report
