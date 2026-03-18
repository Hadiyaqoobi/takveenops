"""Notification creation service for TakvenOps.

Creates in-app notifications and sends email notifications
based on user email preferences.
"""

import threading
from ..database import get_db
from .email_service import (
    send_task_assigned_email,
    send_task_mentioned_email,
    send_task_status_email,
    send_comment_email,
    send_deadline_reminder_email,
)


def _get_user_email_prefs(user_id):
    """Get a user's email preferences. Returns defaults if none set."""
    conn = get_db()
    row = conn.execute("SELECT * FROM email_preferences WHERE user_id = ?", (user_id,)).fetchone()
    user = conn.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    email = user["email"] if user else ""
    if not row:
        return {
            "email": email,
            "on_task_assigned": True,
            "on_task_mentioned": True,
            "on_task_commented": True,
            "on_status_changed": False,
            "on_deadline_reminder": True,
            "on_escalation": True,
        }
    return {
        "email": email,
        "on_task_assigned": bool(row["on_task_assigned"]),
        "on_task_mentioned": bool(row["on_task_mentioned"]),
        "on_task_commented": bool(row["on_task_commented"]),
        "on_status_changed": bool(row["on_status_changed"]),
        "on_deadline_reminder": bool(row["on_deadline_reminder"]),
        "on_escalation": bool(row["on_escalation"]),
    }


def _send_email_async(func, *args):
    """Send email in a background thread to avoid blocking the request."""
    threading.Thread(target=func, args=args, daemon=True).start()


def notify_task_assigned(assignee_username, task_id, task_title, actor):
    if not assignee_username or assignee_username == actor:
        return
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (assignee_username,)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
            (user["id"], "assigned", task_id, f"{actor} assigned {task_id} ({task_title}) to you")
        )
        conn.commit()
        # Email notification
        prefs = _get_user_email_prefs(user["id"])
        if prefs["on_task_assigned"] and prefs["email"]:
            _send_email_async(send_task_assigned_email, prefs["email"], task_id, task_title, actor)
    conn.close()


def notify_comment(task_id, task_title, commenter, assignee):
    if not assignee or assignee == commenter:
        return
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (assignee,)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
            (user["id"], "commented", task_id, f"{commenter} commented on {task_id} ({task_title})")
        )
        conn.commit()
        # Email notification
        prefs = _get_user_email_prefs(user["id"])
        if prefs["on_task_commented"] and prefs["email"]:
            _send_email_async(send_comment_email, prefs["email"], task_id, task_title, commenter)
    conn.close()


def notify_status_changed(task_id, task_title, assignee, actor, new_status):
    if not assignee or assignee == actor:
        return
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (assignee,)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
            (user["id"], "status_changed", task_id, f"{actor} moved {task_id} ({task_title}) to {new_status}")
        )
        conn.commit()
        # Email notification
        prefs = _get_user_email_prefs(user["id"])
        if prefs["on_status_changed"] and prefs["email"]:
            _send_email_async(send_task_status_email, prefs["email"], task_id, task_title, actor, new_status)
    conn.close()


def notify_mention(task_id, task_title, mentioner, mentioned_username):
    if not mentioned_username or mentioned_username == mentioner:
        return
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (mentioned_username,)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
            (user["id"], "mention", task_id, f"{mentioner} mentioned you in {task_id} ({task_title})")
        )
        conn.commit()
        # Email notification
        prefs = _get_user_email_prefs(user["id"])
        if prefs["on_task_mentioned"] and prefs["email"]:
            _send_email_async(send_task_mentioned_email, prefs["email"], task_id, task_title, mentioner)
    conn.close()


def notify_escalation(task_id, task_title, assignee, old_priority, new_priority):
    if not assignee:
        return
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (assignee,)).fetchone()
    if user:
        conn.execute(
            "INSERT INTO notifications (user_id, type, task_id, message) VALUES (?, ?, ?, ?)",
            (user["id"], "escalation", task_id, f"{task_id} ({task_title}) escalated from {old_priority} to {new_priority}")
        )
        conn.commit()
        # Email notification
        prefs = _get_user_email_prefs(user["id"])
        if prefs["on_escalation"] and prefs["email"]:
            from .email_service import send_email, _wrap_html
            html = _wrap_html(f"""
                <h3 style="color: #e8590c;">Priority Escalation</h3>
                <p style="color: #555;"><strong>{task_id}</strong> ({task_title}) escalated from {old_priority} to {new_priority}.</p>
            """)
            _send_email_async(send_email, prefs["email"], f"Escalation: {task_id} now {new_priority}", html)
    conn.close()
