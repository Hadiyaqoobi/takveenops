"""My Day dashboard routes."""

from fastapi import APIRouter, HTTPException, Request
from ..database import get_db, USE_PG
from .auth import get_current_user
from .tasks import row_to_dict

router = APIRouter(prefix="/api/my-day", tags=["myday"])


@router.get("")
def my_day(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    username = user["username"]
    conn = get_db()

    # My active tasks
    my_tasks = conn.execute(
        "SELECT * FROM tasks WHERE assignee = ? AND status IN ('in-progress', 'review') "
        "ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END",
        (username,)
    ).fetchall()

    # Approaching deadlines (next 3 days)
    if USE_PG:
        deadlines = conn.execute(
            "SELECT * FROM tasks WHERE assignee = ? AND due_date IS NOT NULL "
            "AND due_date <= (CURRENT_DATE + INTERVAL '3 days') AND status NOT IN ('done') "
            "ORDER BY due_date ASC",
            (username,)
        ).fetchall()
    else:
        deadlines = conn.execute(
            "SELECT * FROM tasks WHERE assignee = ? AND due_date IS NOT NULL "
            "AND due_date <= DATE('now', '+3 days') AND status NOT IN ('done') "
            "ORDER BY due_date ASC",
            (username,)
        ).fetchall()

    # Recent notifications
    notifs = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
        (user["id"],)
    ).fetchall()

    # Stats
    all_mine = conn.execute(
        "SELECT status, COUNT(*) as c FROM tasks WHERE assignee = ? GROUP BY status",
        (username,)
    ).fetchall()

    conn.close()

    stats = {dict(r)["status"]: dict(r)["c"] for r in all_mine}

    return {
        "my_tasks": [row_to_dict(r) for r in my_tasks],
        "deadlines": [row_to_dict(r) for r in deadlines],
        "notifications": [dict(r) for r in notifs],
        "stats": stats,
    }
