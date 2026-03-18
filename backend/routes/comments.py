"""Comment routes for TakvenOps tasks."""

import re
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db
from .auth import get_current_user
from ..services.notifications import notify_comment, notify_mention

router = APIRouter(prefix="/api/tasks", tags=["comments"])


class CommentCreate(BaseModel):
    body: str


@router.get("/{task_id}/comments")
def list_comments(task_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM comments WHERE task_id = ? ORDER BY created_at ASC",
        (task_id.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/{task_id}/comments")
def add_comment(task_id: str, body: CommentCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    if not body.body.strip():
        raise HTTPException(400, "Comment body is required")

    conn = get_db()
    task = conn.execute("SELECT id, title, assignee FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")

    conn.execute(
        "INSERT INTO comments (task_id, user_id, username, body) VALUES (?, ?, ?, ?)",
        (task_id.upper(), user["id"], user["username"], body.body.strip())
    )
    conn.execute(
        "INSERT INTO activity_log (task_id, action, actor, details) VALUES (?, ?, ?, ?)",
        (task_id.upper(), "commented", user["username"], body.body.strip()[:200])
    )
    conn.commit()
    conn.close()

    notify_comment(task_id.upper(), task["title"], user["username"], task["assignee"])

    # Scan for @mentions
    mentions = set(re.findall(r'@(\w+)', body.body))
    for mentioned in mentions:
        if mentioned != user["username"]:
            notify_mention(task_id.upper(), task["title"], user["username"], mentioned)

    return {"ok": True}


@router.get("/{task_id}/activity")
def task_activity(task_id: str):
    conn = get_db()
    activities = conn.execute(
        "SELECT id, task_id, action, from_status, to_status, actor, timestamp, details "
        "FROM activity_log WHERE task_id = ? ORDER BY timestamp DESC LIMIT 50",
        (task_id.upper(),)
    ).fetchall()
    conn.close()
    return [dict(a) for a in activities]
