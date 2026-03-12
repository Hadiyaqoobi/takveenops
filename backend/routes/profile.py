"""Profile and dashboard routes for TakvenOps."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    display_name: str = None
    email: str = None


@router.get("/dashboard")
def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()

    # Task stats by status
    stats = {}
    for status in ["backlog", "in-progress", "review", "done", "blocked"]:
        row = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status = ?", (status,)).fetchone()
        stats[status] = row["c"]
    stats["total"] = sum(stats.values())

    # Tasks assigned to this user (by username or display_name)
    assigned = conn.execute(
        "SELECT id, title, type, priority, status, assignee, due_date FROM tasks WHERE assignee = ? OR assignee = ? ORDER BY priority, created_at DESC LIMIT 20",
        (user["username"], user["display_name"]),
    ).fetchall()

    # Recent activity
    activity = conn.execute(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 15"
    ).fetchall()

    conn.close()

    return {
        "user": user,
        "stats": stats,
        "assigned_tasks": [dict(t) for t in assigned],
        "recent_activity": [dict(a) for a in activity],
    }


@router.put("/update")
def update_profile(body: ProfileUpdate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    updates = []
    params = []
    if body.display_name is not None:
        updates.append("display_name = ?")
        params.append(body.display_name)
    if body.email is not None:
        updates.append("email = ?")
        params.append(body.email)

    if updates:
        params.append(user["id"])
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()

    return {"ok": True}
