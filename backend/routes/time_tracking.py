"""Time tracking routes."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["time-tracking"])


class TimeEntry(BaseModel):
    hours: float
    description: str = ""


@router.get("/{task_id}/time")
def get_time_entries(task_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM time_entries WHERE task_id = ? ORDER BY logged_at DESC",
        (task_id.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/{task_id}/time")
def log_time(task_id: str, body: TimeEntry, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    if body.hours <= 0:
        raise HTTPException(400, "Hours must be positive")

    conn = get_db()
    task = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")

    conn.execute(
        "INSERT INTO time_entries (task_id, user_id, username, hours, description) VALUES (?, ?, ?, ?, ?)",
        (task_id.upper(), user["id"], user["username"], body.hours, body.description)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/{task_id}/time/{entry_id}")
def delete_time_entry(task_id: str, entry_id: int):
    conn = get_db()
    conn.execute("DELETE FROM time_entries WHERE id = ? AND task_id = ?", (entry_id, task_id.upper()))
    conn.commit()
    conn.close()
    return {"ok": True}
