"""Auto-escalation service."""

from datetime import datetime, timedelta
from ..database import get_db, USE_PG
from .notifications import notify_status_changed


ESCALATION_RULES = [
    {"from": "P2", "to": "P1", "hours": 72},
    {"from": "P1", "to": "P0", "hours": 48},
]


def check_escalation():
    """Escalate stale tasks by priority."""
    conn = get_db()
    escalated = []

    for rule in ESCALATION_RULES:
        cutoff = (datetime.utcnow() - timedelta(hours=rule["hours"])).isoformat()
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE priority = ? AND status NOT IN ('done') AND updated_at < ?",
            (rule["from"], cutoff)
        ).fetchall()

        for task in tasks:
            conn.execute(
                "UPDATE tasks SET priority = ?, updated_at = ? WHERE id = ?",
                (rule["to"], datetime.utcnow().isoformat(), task["id"])
            )
            conn.execute(
                "INSERT INTO activity_log (task_id, action, from_status, to_status, actor, details) VALUES (?, ?, ?, ?, ?, ?)",
                (task["id"], "escalated", rule["from"], rule["to"], "system",
                 f"Auto-escalated from {rule['from']} to {rule['to']} (untouched {rule['hours']}h)")
            )
            escalated.append({"task_id": task["id"], "from": rule["from"], "to": rule["to"]})

    conn.commit()
    conn.close()
    return escalated
