"""Standup generation routes."""

import json
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/standup", tags=["standup"])


@router.get("/today")
def get_today_standup():
    return _generate_standup()


@router.post("/generate")
def generate_standup():
    return _generate_standup()


@router.get("/history")
def standup_history():
    conn = get_db()
    # Build standups from activity log grouped by date
    rows = conn.execute(
        "SELECT DATE(timestamp) as day, COUNT(*) as actions FROM activity_log GROUP BY DATE(timestamp) ORDER BY day DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/ai-generate")
def ai_generate_standup():
    """Generate AI-style per-person standup from last 24h activity."""
    conn = get_db()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    # Get recent activity
    activities = conn.execute(
        "SELECT task_id, action, from_status, to_status, actor, timestamp, details "
        "FROM activity_log WHERE timestamp >= ? ORDER BY timestamp DESC",
        (cutoff,)
    ).fetchall()

    # Get current tasks by assignee
    tasks = conn.execute("SELECT id, title, status, assignee, priority FROM tasks WHERE assignee IS NOT NULL").fetchall()
    conn.close()

    # Group by person
    people = {}
    for a in activities:
        actor = a["actor"] or "system"
        if actor not in people:
            people[actor] = {"yesterday": [], "today": [], "blockers": []}
        action_desc = a["task_id"] or ""
        if a["action"] == "moved" and a["to_status"] == "done":
            people[actor]["yesterday"].append(f"Completed {action_desc}")
        elif a["action"] == "moved":
            people[actor]["yesterday"].append(f"Moved {action_desc} to {a['to_status']}")
        elif a["action"] == "created":
            people[actor]["yesterday"].append(f"Created {action_desc}")
        elif a["action"] == "commented":
            people[actor]["yesterday"].append(f"Commented on {action_desc}")
        elif a["action"] == "assigned":
            people[actor]["yesterday"].append(f"Assigned {action_desc}")

    for t in tasks:
        assignee = t["assignee"]
        if assignee not in people:
            people[assignee] = {"yesterday": [], "today": [], "blockers": []}
        if t["status"] == "in-progress":
            people[assignee]["today"].append(f"{t['id']}: {t['title']}")
        elif t["status"] == "blocked":
            people[assignee]["blockers"].append(f"{t['id']}: {t['title']}")

    # Build markdown
    lines = [f"# Daily Standup — {date.today().isoformat()}\n"]
    for person, data in sorted(people.items()):
        lines.append(f"## {person}")
        lines.append("**Yesterday:**")
        if data["yesterday"]:
            for item in data["yesterday"][:5]:
                lines.append(f"- {item}")
        else:
            lines.append("- (no activity)")
        lines.append("**Today:**")
        if data["today"]:
            for item in data["today"]:
                lines.append(f"- {item}")
        else:
            lines.append("- (no tasks in progress)")
        if data["blockers"]:
            lines.append("**Blockers:**")
            for item in data["blockers"]:
                lines.append(f"- {item}")
        lines.append("")

    summary_text = "\n".join(lines)
    return {"people": people, "summary_text": summary_text, "generated_at": datetime.utcnow().isoformat()}


class StandupMeetingCreate(BaseModel):
    title: str
    scheduled_time: str = "09:00"
    frequency: str = "daily"
    participants: List[str] = []
    notes: str = ""


class StandupSubmission(BaseModel):
    yesterday: List[str] = []
    today: List[str] = []
    blockers: List[str] = []
    notes: str = ""
    audio_transcript: str = ""


@router.get("/my-checklist")
def my_standup_checklist(request: Request):
    """Auto-generate a personal standup checklist from recent activity + current tasks."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    username = user["username"]
    display_name = user["display_name"]
    conn = get_db()
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

    # Yesterday: what I did (from activity log)
    activities = conn.execute(
        """SELECT task_id, action, from_status, to_status, details, timestamp
           FROM activity_log WHERE (actor = ? OR actor = ?) AND timestamp >= ?
           ORDER BY timestamp DESC""",
        (username, display_name, cutoff),
    ).fetchall()

    yesterday_items = []
    for a in activities:
        tid = a["task_id"] or ""
        task_row = conn.execute("SELECT title FROM tasks WHERE id = ?", (tid,)).fetchone() if tid else None
        title = task_row["title"] if task_row else tid
        label = f"{tid}: {title}" if tid and title != tid else tid

        if a["action"] == "moved" and a["to_status"] == "done":
            yesterday_items.append({"text": f"Completed {label}", "task_id": tid, "checked": True})
        elif a["action"] == "moved":
            yesterday_items.append({"text": f"Moved {label} to {a['to_status']}", "task_id": tid, "checked": True})
        elif a["action"] == "created":
            yesterday_items.append({"text": f"Created {label}", "task_id": tid, "checked": True})
        elif a["action"] == "commented":
            yesterday_items.append({"text": f"Commented on {label}", "task_id": tid, "checked": True})
        elif a["action"] == "assigned":
            yesterday_items.append({"text": f"Assigned {label}", "task_id": tid, "checked": True})

    # Today: my current in-progress tasks
    in_progress = conn.execute(
        "SELECT id, title, priority FROM tasks WHERE (assignee = ? OR assignee = ?) AND status = 'in-progress' ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END",
        (username, display_name),
    ).fetchall()
    today_items = [{"text": f"{t['id']}: {t['title']}", "task_id": t["id"], "checked": True} for t in in_progress]

    # Also suggest tasks in backlog assigned to me (high priority)
    backlog = conn.execute(
        "SELECT id, title, priority FROM tasks WHERE (assignee = ? OR assignee = ?) AND status = 'backlog' AND priority IN ('P0', 'P1') ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 END",
        (username, display_name),
    ).fetchall()
    for t in backlog:
        today_items.append({"text": f"{t['id']}: {t['title']} (backlog)", "task_id": t["id"], "checked": False})

    # Blockers
    blocked = conn.execute(
        "SELECT id, title FROM tasks WHERE (assignee = ? OR assignee = ?) AND status = 'blocked'",
        (username, display_name),
    ).fetchall()
    blocker_items = [{"text": f"{t['id']}: {t['title']}", "task_id": t["id"], "checked": True} for t in blocked]

    conn.close()

    return {
        "date": date.today().isoformat(),
        "username": username,
        "yesterday": yesterday_items[:10],
        "today": today_items,
        "blockers": blocker_items,
    }


@router.post("/submit")
def submit_standup(body: StandupSubmission, request: Request):
    """Submit a personal standup entry (from checklist or voice transcript)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    conn.execute(
        """INSERT INTO standup_entries (user_id, username, standup_date, yesterday, today, blockers, notes, audio_transcript)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user["id"], user["username"], date.today().isoformat(),
            json.dumps(body.yesterday), json.dumps(body.today),
            json.dumps(body.blockers), body.notes, body.audio_transcript,
        ),
    )
    conn.commit()
    conn.close()

    return {"ok": True, "date": date.today().isoformat()}


@router.get("/entries")
def list_standup_entries(request: Request, standup_date: str = ""):
    """List submitted standup entries, optionally filtered by date."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    target_date = standup_date or date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        """SELECT id, user_id, username, standup_date, yesterday, today, blockers, notes, audio_transcript, submitted_at
           FROM standup_entries WHERE standup_date = ? ORDER BY submitted_at DESC""",
        (target_date,),
    ).fetchall()
    conn.close()

    entries = []
    for r in rows:
        entry = dict(r)
        for field in ("yesterday", "today", "blockers"):
            try:
                entry[field] = json.loads(entry[field]) if entry[field] else []
            except (json.JSONDecodeError, TypeError):
                entry[field] = []
        entries.append(entry)

    return entries


@router.get("/entries/mine")
def my_standup_entries(request: Request):
    """Get current user's standup entries for the last 7 days."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    cutoff = (date.today() - timedelta(days=7)).isoformat()
    conn = get_db()
    rows = conn.execute(
        """SELECT id, standup_date, yesterday, today, blockers, notes, submitted_at
           FROM standup_entries WHERE user_id = ? AND standup_date >= ? ORDER BY standup_date DESC""",
        (user["id"], cutoff),
    ).fetchall()
    conn.close()

    entries = []
    for r in rows:
        entry = dict(r)
        for field in ("yesterday", "today", "blockers"):
            try:
                entry[field] = json.loads(entry[field]) if entry[field] else []
            except (json.JSONDecodeError, TypeError):
                entry[field] = []
        entries.append(entry)

    return entries


@router.post("/send-reminders")
def send_standup_reminders(request: Request):
    """Send standup reminder notifications to all users who haven't submitted today."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    today_str = date.today().isoformat()
    conn = get_db()

    # Get all users
    all_users = conn.execute("SELECT id, username FROM users").fetchall()

    # Get users who already submitted today
    submitted = conn.execute(
        "SELECT DISTINCT user_id FROM standup_entries WHERE standup_date = ?", (today_str,)
    ).fetchall()
    submitted_ids = {r["user_id"] for r in submitted}

    reminded = 0
    for u in all_users:
        if u["id"] not in submitted_ids:
            conn.execute(
                "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
                (u["id"], "standup_reminder", None,
                 f"Daily standup reminder: Please submit your standup for {today_str}"),
            )
            reminded += 1

    conn.commit()
    conn.close()

    return {"reminded": reminded, "date": today_str}


# ── Standup Meetings CRUD ──

@router.get("/meetings")
def list_meetings(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM standup_meetings ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    meetings = []
    for r in rows:
        m = dict(r)
        try:
            m["participants"] = json.loads(m["participants"]) if m["participants"] else []
        except (json.JSONDecodeError, TypeError):
            m["participants"] = []
        meetings.append(m)

    return meetings


@router.post("/meetings")
def create_meeting(body: StandupMeetingCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    if not body.title.strip():
        raise HTTPException(400, "Title is required")

    conn = get_db()
    conn.execute(
        """INSERT INTO standup_meetings (title, scheduled_time, frequency, participants, notes, created_by)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (body.title.strip(), body.scheduled_time, body.frequency,
         json.dumps(body.participants), body.notes, user["username"]),
    )
    conn.commit()
    conn.close()

    return {"ok": True}


@router.put("/meetings/{meeting_id}")
def update_meeting(meeting_id: int, body: StandupMeetingCreate, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    existing = conn.execute("SELECT id FROM standup_meetings WHERE id = ?", (meeting_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Meeting not found")

    conn.execute(
        """UPDATE standup_meetings SET title = ?, scheduled_time = ?, frequency = ?,
           participants = ?, notes = ? WHERE id = ?""",
        (body.title.strip(), body.scheduled_time, body.frequency,
         json.dumps(body.participants), body.notes, meeting_id),
    )
    conn.commit()
    conn.close()

    return {"ok": True}


@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    conn.execute("DELETE FROM standup_meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()

    return {"ok": True}


def _generate_standup():
    conn = get_db()

    # Get tasks by status
    statuses = {}
    for status in ["backlog", "in-progress", "review", "done", "blocked"]:
        rows = conn.execute(
            "SELECT id, title, assignee, priority, type FROM tasks WHERE status = ? ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END",
            (status,)
        ).fetchall()
        statuses[status] = [dict(r) for r in rows]

    total = sum(len(ts) for ts in statuses.values())
    done_count = len(statuses.get("done", []))
    progress_pct = int(done_count / total * 100) if total else 0

    # Recent activity
    recent = conn.execute(
        "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    conn.close()

    return {
        "date": date.today().isoformat(),
        "generated_at": datetime.utcnow().isoformat(),
        "completed": statuses.get("done", []),
        "in_progress": statuses.get("in-progress", []),
        "review": statuses.get("review", []),
        "blocked": statuses.get("blocked", []),
        "high_priority_backlog": [t for t in statuses.get("backlog", []) if t.get("priority") in ("P0", "P1")],
        "progress": {
            "total": total,
            "done": done_count,
            "percentage": progress_pct,
        },
        "recent_activity": [dict(r) for r in recent],
    }
