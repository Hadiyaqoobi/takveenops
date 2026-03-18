"""AI auto-assignment service."""

import json
from ..database import get_db


def auto_assign_tasks(task_ids=None):
    """Distribute tasks based on team capacity and capabilities."""
    conn = get_db()

    # Get team members
    members = conn.execute("SELECT * FROM team_members").fetchall()
    if not members:
        conn.close()
        return []

    # Build member info
    member_info = []
    for m in members:
        caps = json.loads(m["capabilities"]) if m["capabilities"] else []
        active = conn.execute(
            "SELECT COUNT(*) as c FROM tasks WHERE assignee = ? AND status IN ('in-progress', 'review')",
            (m["id"],)
        ).fetchone()
        member_info.append({
            "id": m["id"],
            "name": m["name"],
            "capabilities": caps,
            "max": m["max_concurrent_tasks"] or 3,
            "active": active["c"],
        })

    # Get tasks to assign
    if task_ids:
        placeholders = ", ".join("?" for _ in task_ids)
        tasks = conn.execute(
            f"SELECT * FROM tasks WHERE id IN ({placeholders}) AND (assignee IS NULL OR assignee = '')",
            [tid.upper() for tid in task_ids]
        ).fetchall()
    else:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE (assignee IS NULL OR assignee = '') AND status NOT IN ('done') "
            "ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END"
        ).fetchall()

    assignments = []
    for task in tasks:
        task_type = task["type"] or "feature"

        # Find eligible members (capabilities match or empty capabilities = can do anything)
        eligible = [m for m in member_info if not m["capabilities"] or task_type in m["capabilities"]]
        if not eligible:
            eligible = member_info  # fallback: anyone

        # Pick member with lowest load ratio
        eligible.sort(key=lambda m: m["active"] / max(m["max"], 1))
        best = eligible[0]

        if best["active"] >= best["max"]:
            continue  # everyone at capacity

        conn.execute("UPDATE tasks SET assignee = ? WHERE id = ?", (best["id"], task["id"]))
        best["active"] += 1
        assignments.append({"task_id": task["id"], "assignee": best["id"]})

    conn.commit()
    conn.close()
    return assignments
