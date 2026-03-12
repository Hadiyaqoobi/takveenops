"""Sprint management routes."""

import json
from fastapi import APIRouter, HTTPException
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
