"""Profile and dashboard routes for TakvenOps."""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from ..database import get_db
from .auth import get_current_user

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(Path(__file__).parent.parent / "uploads")))
AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 MB

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


@router.post("/avatar")
async def upload_avatar(request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in AVATAR_EXTENSIONS:
        raise HTTPException(400, "Only image files allowed (jpg, png, gif, webp)")

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(400, "Avatar too large (max 2MB)")

    # Delete old avatar files for this user
    avatar_dir = UPLOAD_DIR / "avatars"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    for old in avatar_dir.glob(f"user_{user['id']}.*"):
        old.unlink()

    # Save new avatar
    filename = f"user_{user['id']}{ext}"
    (avatar_dir / filename).write_bytes(content)

    avatar_url = f"/api/uploads/avatars/{filename}"
    conn = get_db()
    conn.execute("UPDATE users SET avatar_url = ? WHERE id = ?", (avatar_url, user["id"]))
    conn.commit()
    conn.close()

    return {"avatar_url": avatar_url}


# ── Email Preferences ────────────────────────────

class EmailPrefsUpdate(BaseModel):
    on_task_assigned: bool = True
    on_task_mentioned: bool = True
    on_task_commented: bool = True
    on_status_changed: bool = False
    on_deadline_reminder: bool = True
    on_escalation: bool = True


@router.get("/email-preferences")
def get_email_prefs(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    row = conn.execute("SELECT * FROM email_preferences WHERE user_id = ?", (user["id"],)).fetchone()
    conn.close()
    if not row:
        return {
            "on_task_assigned": True,
            "on_task_mentioned": True,
            "on_task_commented": True,
            "on_status_changed": False,
            "on_deadline_reminder": True,
            "on_escalation": True,
        }
    return {
        "on_task_assigned": bool(row["on_task_assigned"]),
        "on_task_mentioned": bool(row["on_task_mentioned"]),
        "on_task_commented": bool(row["on_task_commented"]),
        "on_status_changed": bool(row["on_status_changed"]),
        "on_deadline_reminder": bool(row["on_deadline_reminder"]),
        "on_escalation": bool(row["on_escalation"]),
    }


@router.put("/email-preferences")
def update_email_prefs(body: EmailPrefsUpdate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    existing = conn.execute("SELECT id FROM email_preferences WHERE user_id = ?", (user["id"],)).fetchone()
    if existing:
        conn.execute(
            """UPDATE email_preferences SET
               on_task_assigned = ?, on_task_mentioned = ?, on_task_commented = ?,
               on_status_changed = ?, on_deadline_reminder = ?, on_escalation = ?
               WHERE user_id = ?""",
            (body.on_task_assigned, body.on_task_mentioned, body.on_task_commented,
             body.on_status_changed, body.on_deadline_reminder, body.on_escalation,
             user["id"])
        )
    else:
        conn.execute(
            """INSERT INTO email_preferences
               (user_id, on_task_assigned, on_task_mentioned, on_task_commented,
                on_status_changed, on_deadline_reminder, on_escalation)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user["id"], body.on_task_assigned, body.on_task_mentioned, body.on_task_commented,
             body.on_status_changed, body.on_deadline_reminder, body.on_escalation)
        )
    conn.commit()
    conn.close()
    return {"ok": True}
