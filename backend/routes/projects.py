"""Project management routes."""
import secrets
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    key: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


def _generate_key(name: str) -> str:
    words = name.upper().split()
    if len(words) >= 2:
        return "".join(w[0] for w in words[:4])
    return name.upper()[:4] if len(name) >= 2 else name.upper()


@router.get("")
def list_projects(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT p.* FROM projects p
           LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.user_id = ?
           WHERE p.id = 'default' OR pm.user_id = ?
           ORDER BY p.created_at DESC""",
        (user["id"], user["id"])
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("")
def create_project(body: ProjectCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    if not body.name.strip():
        raise HTTPException(400, "Project name required")

    project_id = secrets.token_hex(6)
    key = body.key.upper() if body.key else _generate_key(body.name)

    conn = get_db()
    conn.execute(
        "INSERT INTO projects (id, name, description, key, owner_id) VALUES (?, ?, ?, ?, ?)",
        (project_id, body.name.strip(), body.description, key, user["id"])
    )
    conn.execute(
        "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
        (project_id, user["id"], "owner")
    )
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/{project_id}")
def get_project(project_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Project not found")
    return dict(row)


@router.put("/{project_id}")
def update_project(project_id: str, body: ProjectUpdate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    member = conn.execute(
        "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
        (project_id, user["id"])
    ).fetchone()
    if not member and user["role"] != "admin" and project_id != "default":
        conn.close()
        raise HTTPException(403, "Not authorized")

    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", list(updates.values()) + [project_id])
        conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/{project_id}/members")
def list_members(project_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    rows = conn.execute(
        """SELECT pm.*, u.username, u.display_name, u.email, u.avatar_url
           FROM project_members pm JOIN users u ON pm.user_id = u.id
           WHERE pm.project_id = ?""",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.post("/{project_id}/members")
def add_member(project_id: str, body: dict, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    username = body.get("username", "")
    role = body.get("role", "member")
    if not username:
        raise HTTPException(400, "username required")
    conn = get_db()
    target = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(404, "User not found")
    try:
        conn.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, target["id"], role)
        )
        conn.commit()
    except Exception:
        conn.close()
        raise HTTPException(409, "User is already a member")
    conn.close()
    return {"ok": True}
