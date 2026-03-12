"""Task CRUD routes."""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..models import TaskCreate, TaskUpdate, TaskMove, TaskAssign

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def row_to_dict(row):
    """Convert a sqlite3.Row to a dict with parsed JSON fields."""
    d = dict(row)
    for field in ("labels", "files_involved", "acceptance_criteria", "depends_on", "blocks"):
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = []
        else:
            d[field] = []
    return d


def _next_task_id(conn):
    """Generate next task ID like ROE-001."""
    row = conn.execute("SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1").fetchone()
    if row:
        num = int(row["id"].split("-")[1]) + 1
    else:
        num = 1
    return f"ROE-{num:03d}"


def _log_activity(conn, task_id, action, from_status=None, to_status=None, actor="system", details=None):
    conn.execute(
        "INSERT INTO activity_log (task_id, action, from_status, to_status, actor, details) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, action, from_status, to_status, actor, json.dumps(details) if details else None)
    )


@router.get("")
def list_tasks(status: str = None, sprint_id: int = None, assignee: str = None, priority: str = None, type: str = None):
    conn = get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if sprint_id:
        query += " AND sprint_id = ?"
        params.append(sprint_id)
    if assignee:
        query += " AND assignee = ?"
        params.append(assignee)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if type:
        query += " AND type = ?"
        params.append(type)

    query += " ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END, created_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@router.get("/{task_id}")
def get_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_dict(row)


@router.post("")
def create_task(task: TaskCreate):
    conn = get_db()
    task_id = _next_task_id(conn)
    now = datetime.utcnow().isoformat()

    conn.execute(
        """INSERT INTO tasks (id, title, type, priority, status, assignee, sprint_id, created_at, updated_at,
           due_date, estimated_hours, labels, files_involved, acceptance_criteria,
           verification_type, verification_command, verification_ai_check,
           depends_on, blocks, body_markdown)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (task_id, task.title, task.type, task.priority, task.status, task.assignee, task.sprint_id,
         now, now, task.due_date, task.estimated_hours,
         json.dumps(task.labels), json.dumps(task.files_involved), json.dumps(task.acceptance_criteria),
         task.verification_type, task.verification_command, task.verification_ai_check,
         json.dumps(task.depends_on), json.dumps(task.blocks), task.body_markdown)
    )
    _log_activity(conn, task_id, "created", to_status=task.status)
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.put("/{task_id}")
def update_task(task_id: str, task: TaskUpdate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    for field, value in task.model_dump(exclude_unset=True).items():
        if field in ("labels", "files_involved", "acceptance_criteria", "depends_on", "blocks"):
            updates[field] = json.dumps(value)
        else:
            updates[field] = value

    if not updates:
        conn.close()
        return row_to_dict(existing)

    updates["updated_at"] = datetime.utcnow().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id.upper()]
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)

    if "status" in updates:
        _log_activity(conn, task_id.upper(), "moved", existing["status"], updates["status"])

    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.delete("/{task_id}")
def delete_task(task_id: str):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id.upper(),))
    _log_activity(conn, task_id.upper(), "deleted")
    conn.commit()
    conn.close()
    return {"message": f"Task {task_id.upper()} deleted"}


@router.post("/{task_id}/move")
def move_task(task_id: str, body: TaskMove):
    valid = ["backlog", "assigned", "in-progress", "review", "done", "blocked"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {', '.join(valid)}")

    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = existing["status"]
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (body.status, now, task_id.upper()))
    _log_activity(conn, task_id.upper(), "moved", old_status, body.status)
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.post("/{task_id}/assign")
def assign_task(task_id: str, body: TaskAssign):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE tasks SET assignee = ?, updated_at = ? WHERE id = ?", (body.assignee, now, task_id.upper()))
    _log_activity(conn, task_id.upper(), "assigned", actor=body.assignee, details={"assignee": body.assignee})
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    return row_to_dict(row)
