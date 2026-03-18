"""Notification routes for TakvenOps."""

from fastapi import APIRouter, HTTPException, Request
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(request: Request, unread: bool = None):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    if unread:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? AND read = 0 ORDER BY created_at DESC LIMIT 50",
            (user["id"],)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user["id"],)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/unread-count")
def unread_count(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND read = 0",
        (user["id"],)
    ).fetchone()
    conn.close()
    return {"count": row["c"]}


@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    conn.execute(
        "UPDATE notifications SET read = 1 WHERE id = ? AND user_id = ?",
        (notif_id, user["id"])
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    conn.execute(
        "UPDATE notifications SET read = 1 WHERE user_id = ? AND read = 0",
        (user["id"],)
    )
    conn.commit()
    conn.close()
    return {"ok": True}
