"""Recurring tasks routes."""

import json
from datetime import datetime, timedelta, date
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/recurring", tags=["recurring"])

FREQ_DAYS = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30}


class RecurringCreate(BaseModel):
    title: str
    type: str = "feature"
    priority: str = "P2"
    assignee: Optional[str] = None
    labels: list[str] = []
    body_markdown: str = ""
    frequency: str = "weekly"
    next_run: str  # YYYY-MM-DD


class RecurringUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    assignee: Optional[str] = None
    labels: Optional[list[str]] = None
    body_markdown: Optional[str] = None
    frequency: Optional[str] = None
    next_run: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
def list_rules():
    conn = get_db()
    rows = conn.execute("SELECT * FROM recurring_rules ORDER BY next_run ASC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["labels"] = json.loads(d["labels"])
        except (json.JSONDecodeError, TypeError):
            d["labels"] = []
        result.append(d)
    return result


@router.post("")
def create_rule(body: RecurringCreate, request: Request):
    user = get_current_user(request)
    conn = get_db()
    conn.execute(
        "INSERT INTO recurring_rules (title, type, priority, assignee, labels, body_markdown, frequency, next_run, created_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (body.title, body.type, body.priority, body.assignee, json.dumps(body.labels),
         body.body_markdown, body.frequency, body.next_run, user["username"] if user else None)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/{rule_id}")
def delete_rule(rule_id: int):
    conn = get_db()
    conn.execute("DELETE FROM recurring_rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/run")
def run_recurring():
    """Create tasks for any active rules past their next_run date."""
    conn = get_db()
    today = date.today().isoformat()
    rules = conn.execute(
        "SELECT * FROM recurring_rules WHERE active = 1 AND next_run <= ?", (today,)
    ).fetchall()

    created = []
    for rule in rules:
        # Generate next task ID
        row = conn.execute("SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1").fetchone()
        if row:
            num = int(row["id"].split("-")[1]) + 1
        else:
            num = 1
        task_id = f"ROE-{num:03d}"

        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO tasks (id, title, type, priority, status, assignee, labels, body_markdown, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, rule["title"], rule["type"], rule["priority"], "backlog",
             rule["assignee"], rule["labels"], rule["body_markdown"], now, now)
        )

        # Advance next_run
        freq = rule["frequency"]
        days = FREQ_DAYS.get(freq, 7)
        next_date = date.fromisoformat(str(rule["next_run"])) + timedelta(days=days)
        conn.execute("UPDATE recurring_rules SET next_run = ? WHERE id = ?", (next_date.isoformat(), rule["id"]))

        created.append({"task_id": task_id, "rule_id": rule["id"]})

    conn.commit()
    conn.close()
    return {"created": created}
