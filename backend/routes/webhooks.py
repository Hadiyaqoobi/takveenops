"""Webhook configuration routes."""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..database import get_db

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: list[str] = []
    active: bool = True


@router.get("")
def list_webhooks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM webhook_config ORDER BY name").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["events"] = json.loads(d["events"])
        except (json.JSONDecodeError, TypeError):
            d["events"] = []
        result.append(d)
    return result


@router.post("")
def create_webhook(body: WebhookCreate):
    conn = get_db()
    conn.execute(
        "INSERT INTO webhook_config (name, url, events, active) VALUES (?, ?, ?, ?)",
        (body.name, body.url, json.dumps(body.events), 1 if body.active else 0)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@router.delete("/{webhook_id}")
def delete_webhook(webhook_id: int):
    conn = get_db()
    conn.execute("DELETE FROM webhook_config WHERE id = ?", (webhook_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{webhook_id}/test")
def test_webhook(webhook_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM webhook_config WHERE id = ?", (webhook_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Webhook not found")

    from ..services.webhook_service import fire_single_webhook
    success = fire_single_webhook(row["url"], {"event": "test", "message": "TakvenOps webhook test"})
    return {"ok": success}
