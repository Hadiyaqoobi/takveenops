"""Webhook firing service."""

import json
import urllib.request
from ..database import get_db


def fire_webhook(event: str, payload: dict):
    """Send event to all active webhooks matching the event type."""
    conn = get_db()
    configs = conn.execute("SELECT * FROM webhook_config WHERE active = 1").fetchall()
    conn.close()

    for config in configs:
        try:
            events = json.loads(config["events"]) if config["events"] else []
        except (json.JSONDecodeError, TypeError):
            events = []
        if events and event not in events:
            continue
        fire_single_webhook(config["url"], {"event": event, **payload})


def fire_single_webhook(url: str, data: dict) -> bool:
    """Send a single webhook POST. Returns success."""
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False
