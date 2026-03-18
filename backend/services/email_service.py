"""Email service for TakvenOps.

Sends emails via SMTP. Configure with environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_USE_TLS
Falls back to console logging if SMTP is not configured.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@takvenops.com")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")


def is_email_configured():
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def send_email(to_email: str, subject: str, html_body: str):
    """Send an email. Logs to console if SMTP is not configured."""
    if not to_email:
        return False

    if not is_email_configured():
        logger.info(f"[EMAIL-PREVIEW] To: {to_email} | Subject: {subject}")
        logger.info(f"[EMAIL-PREVIEW] Body: {html_body[:200]}...")
        return True  # Return True so app logic continues

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ── Email templates ──────────────────────────────


def _wrap_html(content: str) -> str:
    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 560px; margin: 0 auto; padding: 24px;">
        <div style="border-bottom: 3px solid #0078d4; padding-bottom: 12px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #0078d4; font-size: 20px;">TakvenOps</h2>
        </div>
        {content}
        <div style="margin-top: 24px; padding-top: 12px; border-top: 1px solid #e0e0e0;
                    font-size: 12px; color: #888;">
            Sent by TakvenOps &mdash; AI-powered project management
        </div>
    </div>
    """


def send_invitation_email(to_email: str, invited_by: str, invite_token: str, project_name: str = "TakvenOps"):
    signup_url = f"{FRONTEND_URL}?invite={invite_token}"
    html = _wrap_html(f"""
        <h3 style="color: #333;">You're invited to join {project_name}!</h3>
        <p style="color: #555; line-height: 1.6;">
            <strong>{invited_by}</strong> has invited you to collaborate on <strong>{project_name}</strong>.
        </p>
        <p style="margin: 24px 0;">
            <a href="{signup_url}"
               style="background: #0078d4; color: white; padding: 12px 28px;
                      text-decoration: none; border-radius: 4px; font-weight: 600;">
                Accept Invitation
            </a>
        </p>
        <p style="color: #888; font-size: 13px;">
            Or copy this link: <code>{signup_url}</code>
        </p>
    """)
    return send_email(to_email, f"You're invited to {project_name}", html)


def send_task_assigned_email(to_email: str, task_id: str, task_title: str, assigned_by: str):
    task_url = f"{FRONTEND_URL}/board"
    html = _wrap_html(f"""
        <h3 style="color: #333;">Task Assigned to You</h3>
        <p style="color: #555; line-height: 1.6;">
            <strong>{assigned_by}</strong> assigned you a task:
        </p>
        <div style="background: #f5f5f5; padding: 12px 16px; border-left: 3px solid #0078d4;
                    margin: 16px 0; border-radius: 2px;">
            <strong>{task_id}</strong> &mdash; {task_title}
        </div>
        <p><a href="{task_url}" style="color: #0078d4;">View in TakvenOps</a></p>
    """)
    return send_email(to_email, f"Task assigned: {task_id} - {task_title}", html)


def send_task_mentioned_email(to_email: str, task_id: str, task_title: str, mentioned_by: str):
    html = _wrap_html(f"""
        <h3 style="color: #333;">You were mentioned</h3>
        <p style="color: #555; line-height: 1.6;">
            <strong>{mentioned_by}</strong> mentioned you in task
            <strong>{task_id}</strong> &mdash; {task_title}
        </p>
        <p><a href="{FRONTEND_URL}/board" style="color: #0078d4;">View in TakvenOps</a></p>
    """)
    return send_email(to_email, f"You were mentioned in {task_id}", html)


def send_task_status_email(to_email: str, task_id: str, task_title: str, actor: str, new_status: str):
    html = _wrap_html(f"""
        <h3 style="color: #333;">Task Status Updated</h3>
        <p style="color: #555; line-height: 1.6;">
            <strong>{actor}</strong> moved <strong>{task_id}</strong> ({task_title})
            to <strong>{new_status}</strong>.
        </p>
        <p><a href="{FRONTEND_URL}/board" style="color: #0078d4;">View in TakvenOps</a></p>
    """)
    return send_email(to_email, f"Task updated: {task_id} is now {new_status}", html)


def send_comment_email(to_email: str, task_id: str, task_title: str, commenter: str):
    html = _wrap_html(f"""
        <h3 style="color: #333;">New Comment on Your Task</h3>
        <p style="color: #555; line-height: 1.6;">
            <strong>{commenter}</strong> commented on
            <strong>{task_id}</strong> &mdash; {task_title}
        </p>
        <p><a href="{FRONTEND_URL}/board" style="color: #0078d4;">View in TakvenOps</a></p>
    """)
    return send_email(to_email, f"New comment on {task_id}", html)


def send_deadline_reminder_email(to_email: str, task_id: str, task_title: str, due_date: str):
    html = _wrap_html(f"""
        <h3 style="color: #e8590c;">Deadline Approaching</h3>
        <p style="color: #555; line-height: 1.6;">
            Your task <strong>{task_id}</strong> ({task_title}) is due on
            <strong>{due_date}</strong>.
        </p>
        <p><a href="{FRONTEND_URL}/board" style="color: #0078d4;">View in TakvenOps</a></p>
    """)
    return send_email(to_email, f"Deadline reminder: {task_id} due {due_date}", html)
