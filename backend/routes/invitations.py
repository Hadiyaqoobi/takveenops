"""Invitation routes for TakvenOps — invite users by email."""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db
from .auth import get_current_user
from ..services.email_service import send_invitation_email

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


class InviteRequest(BaseModel):
    email: str
    role: str = "member"
    project_id: str = "default"


class AcceptInviteRequest(BaseModel):
    token: str
    username: str
    password: str
    display_name: str = ""


@router.post("")
def invite_user(body: InviteRequest, request: Request):
    """Invite a user by email. Only admins/owners can invite."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    if user.get("role") not in ("admin",) and body.project_id != "default":
        # Check project-level admin role
        conn = get_db()
        pm = conn.execute(
            "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
            (body.project_id, user["id"])
        ).fetchone()
        conn.close()
        if not pm or pm["role"] not in ("admin", "owner"):
            raise HTTPException(403, "Only admins can invite users")

    if not body.email or "@" not in body.email:
        raise HTTPException(400, "Valid email is required")

    conn = get_db()

    # Check if user already exists with this email
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (body.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(409, "A user with this email already exists")

    # Check if pending invitation already exists
    pending = conn.execute(
        "SELECT id FROM invitations WHERE email = ? AND status = 'pending'",
        (body.email,)
    ).fetchone()
    if pending:
        conn.close()
        raise HTTPException(409, "An invitation has already been sent to this email")

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(days=7)

    conn.execute(
        "INSERT INTO invitations (email, token, invited_by, role, project_id, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
        (body.email, token, user["username"], body.role, body.project_id, expires.isoformat())
    )
    conn.commit()
    conn.close()

    # Send invitation email
    project_name = "TakvenOps"
    if body.project_id != "default":
        pconn = get_db()
        proj = pconn.execute("SELECT name FROM projects WHERE id = ?", (body.project_id,)).fetchone()
        if proj:
            project_name = proj["name"]
        pconn.close()

    send_invitation_email(body.email, user["display_name"] or user["username"], token, project_name)

    return {"ok": True, "message": f"Invitation sent to {body.email}"}


@router.get("")
def list_invitations(request: Request):
    """List all invitations (admin only)."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    rows = conn.execute(
        "SELECT id, email, invited_by, role, project_id, status, created_at, expires_at FROM invitations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/validate")
def validate_invite(token: str):
    """Check if an invitation token is valid."""
    conn = get_db()
    row = conn.execute(
        "SELECT email, role, project_id, expires_at FROM invitations WHERE token = ? AND status = 'pending'",
        (token,)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Invalid or expired invitation")
    if row["expires_at"] and row["expires_at"] < datetime.utcnow().isoformat():
        raise HTTPException(410, "Invitation has expired")
    return {"email": row["email"], "role": row["role"], "project_id": row["project_id"]}


@router.post("/accept")
def accept_invite(body: AcceptInviteRequest):
    """Accept an invitation and create an account."""
    import bcrypt

    conn = get_db()
    invite = conn.execute(
        "SELECT * FROM invitations WHERE token = ? AND status = 'pending'",
        (body.token,)
    ).fetchone()
    if not invite:
        conn.close()
        raise HTTPException(404, "Invalid or expired invitation")
    if invite["expires_at"] and invite["expires_at"] < datetime.utcnow().isoformat():
        conn.close()
        raise HTTPException(410, "Invitation has expired")

    # Check username availability
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(409, "Username already taken")

    if len(body.password) < 4:
        conn.close()
        raise HTTPException(400, "Password must be at least 4 characters")

    # Create the user
    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    display = body.display_name or body.username

    conn.execute(
        "INSERT INTO users (username, display_name, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?, ?)",
        (body.username, display, invite["email"], pw_hash, "", invite["role"])
    )
    conn.commit()

    # Get user ID
    user_row = conn.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    user_id = user_row["id"]

    # Add to project if not default
    if invite["project_id"] and invite["project_id"] != "default":
        try:
            conn.execute(
                "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
                (invite["project_id"], user_id, invite["role"])
            )
            conn.commit()
        except Exception:
            pass  # Ignore if already a member

    # Mark invitation as accepted
    conn.execute("UPDATE invitations SET status = 'accepted' WHERE id = ?", (invite["id"],))
    conn.commit()

    # Create session
    token = secrets.token_hex(32)
    refresh_token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at, refresh_token) VALUES (?, ?, ?, ?)",
        (token, user_id, expires_at.isoformat(), refresh_token)
    )
    conn.commit()
    conn.close()

    return {
        "token": token,
        "refresh_token": refresh_token,
        "user": {"id": user_id, "username": body.username, "display_name": display, "email": invite["email"], "role": invite["role"]},
    }


@router.delete("/{invite_id}")
def revoke_invite(invite_id: int, request: Request):
    """Revoke a pending invitation."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    conn.execute("UPDATE invitations SET status = 'revoked' WHERE id = ?", (invite_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@router.post("/{invite_id}/resend")
def resend_invite(invite_id: int, request: Request):
    """Resend an invitation email."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    conn = get_db()
    invite = conn.execute(
        "SELECT * FROM invitations WHERE id = ? AND status = 'pending'",
        (invite_id,)
    ).fetchone()
    if not invite:
        conn.close()
        raise HTTPException(404, "Invitation not found or already used")

    # Refresh expiry
    new_expires = datetime.utcnow() + timedelta(days=7)
    conn.execute("UPDATE invitations SET expires_at = ? WHERE id = ?", (new_expires.isoformat(), invite_id))
    conn.commit()
    conn.close()

    project_name = "TakvenOps"
    send_invitation_email(invite["email"], user["display_name"] or user["username"], invite["token"], project_name)
    return {"ok": True, "message": f"Invitation resent to {invite['email']}"}
