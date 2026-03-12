"""Team member management routes."""

import json
from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..models import TeamMemberCreate, TeamMemberUpdate

router = APIRouter(prefix="/api/team", tags=["team"])


def row_to_dict(row):
    d = dict(row)
    if d.get("capabilities"):
        try:
            d["capabilities"] = json.loads(d["capabilities"])
        except (json.JSONDecodeError, TypeError):
            d["capabilities"] = []
    else:
        d["capabilities"] = []
    return d


@router.get("")
def list_team():
    conn = get_db()
    rows = conn.execute("SELECT * FROM team_members ORDER BY type, name").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@router.post("")
def add_member(member: TeamMemberCreate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM team_members WHERE id = ?", (member.id,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Team member already exists")

    conn.execute(
        "INSERT INTO team_members (id, name, type, role, capabilities, max_concurrent_tasks, avatar_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (member.id, member.name, member.type, member.role, json.dumps(member.capabilities), member.max_concurrent_tasks, member.avatar_url)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM team_members WHERE id = ?", (member.id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.put("/{member_id}")
def update_member(member_id: str, member: TeamMemberUpdate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM team_members WHERE id = ?", (member_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Team member not found")

    updates = {}
    for field, value in member.model_dump(exclude_unset=True).items():
        if field == "capabilities":
            updates[field] = json.dumps(value)
        else:
            updates[field] = value

    if not updates:
        conn.close()
        return row_to_dict(existing)

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [member_id]
    conn.execute(f"UPDATE team_members SET {set_clause} WHERE id = ?", values)
    conn.commit()

    row = conn.execute("SELECT * FROM team_members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.delete("/{member_id}")
def delete_member(member_id: str):
    conn = get_db()
    existing = conn.execute("SELECT * FROM team_members WHERE id = ?", (member_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Team member not found")

    conn.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    return {"message": f"Team member {member_id} deleted"}
