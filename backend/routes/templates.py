"""Task template CRUD routes."""

import json
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateCreate(BaseModel):
    name: str
    type: str = "feature"
    priority: str = "P2"
    labels: list[str] = []
    body_markdown: str = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    labels: Optional[list[str]] = None
    body_markdown: Optional[str] = None


def _tpl_to_dict(row):
    d = dict(row)
    try:
        d["labels"] = json.loads(d["labels"])
    except (json.JSONDecodeError, TypeError):
        d["labels"] = []
    return d


@router.get("")
def list_templates():
    conn = get_db()
    rows = conn.execute("SELECT * FROM task_templates ORDER BY name").fetchall()
    conn.close()
    return [_tpl_to_dict(r) for r in rows]


@router.post("")
def create_template(body: TemplateCreate, request: Request):
    user = get_current_user(request)
    conn = get_db()
    conn.execute(
        "INSERT INTO task_templates (name, type, priority, labels, body_markdown, created_by) VALUES (?, ?, ?, ?, ?, ?)",
        (body.name, body.type, body.priority, json.dumps(body.labels), body.body_markdown, user["username"] if user else None)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/{template_id}")
def delete_template(template_id: int):
    conn = get_db()
    conn.execute("DELETE FROM task_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return {"ok": True}
