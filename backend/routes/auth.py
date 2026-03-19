"""Authentication routes for TakvenOps."""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db

import bcrypt

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""
    email: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str, salt: str = "") -> bool:
    """Verify a password. Supports both bcrypt (new) and SHA-256 (legacy)."""
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    # Legacy SHA-256 fallback
    import hashlib
    legacy = hashlib.sha256((salt + password).encode()).hexdigest()
    return legacy == password_hash


def create_session(user_id: int) -> dict:
    """Create a session with access and refresh tokens."""
    token = secrets.token_hex(32)
    refresh_token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at, refresh_token) VALUES (?, ?, ?, ?)",
        (token, user_id, expires_at.isoformat(), refresh_token),
    )
    conn.commit()
    conn.close()
    return {"token": token, "refresh_token": refresh_token}


# ── RBAC helpers ──────────────────────────────────

def get_project_role(user_id: int, project_id: str):
    """Returns the user's role in a project, or None if not a member."""
    if not project_id or project_id == "default":
        return "member"
    conn = get_db()
    row = conn.execute(
        "SELECT role FROM project_members WHERE project_id = ? AND user_id = ?",
        (project_id, user_id)
    ).fetchone()
    conn.close()
    return row["role"] if row else None


def require_project_access(user: dict, project_id: str, min_role: str = "viewer"):
    """Raises 403 if user lacks required role. Hierarchy: viewer < member < admin < owner."""
    HIERARCHY = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}
    if user.get("role") == "admin":
        return
    role = get_project_role(user["id"], project_id)
    if role is None:
        raise HTTPException(403, "Not a member of this project")
    if HIERARCHY.get(role, 0) < HIERARCHY.get(min_role, 0):
        raise HTTPException(403, f"Requires {min_role} role or higher")


def get_current_user(request: Request):
    """Extract user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    conn = get_db()
    row = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.email, u.role, u.avatar_url, u.created_at
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.token = ? AND s.expires_at > ?""",
        (token, datetime.utcnow().isoformat()),
    ).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


@router.post("/register")
def register(body: RegisterRequest):
    if not body.username or not body.password:
        raise HTTPException(400, "Username and password required")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(409, "Username already exists")

    pw_hash = hash_password(body.password)
    display = body.display_name or body.username

    conn.execute(
        "INSERT INTO users (username, display_name, email, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
        (body.username, display, body.email, pw_hash, ""),
    )
    conn.commit()
    # Re-query to get user_id (works on both SQLite and PG)
    user_row = conn.execute("SELECT id FROM users WHERE username = ?", (body.username,)).fetchone()
    user_id = user_row["id"]
    conn.close()

    session = create_session(user_id)
    return {
        "token": session["token"],
        "refresh_token": session["refresh_token"],
        "user": {"id": user_id, "username": body.username, "display_name": display, "email": body.email, "role": "member"},
    }


@router.post("/login")
def login(body: LoginRequest):
    try:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
        conn.close()

        if not user:
            raise HTTPException(401, "Invalid username or password")

        if not verify_password(body.password, user["password_hash"], user.get("salt", "")):
            raise HTTPException(401, "Invalid username or password")

        # Transparently upgrade legacy SHA-256 hash to bcrypt
        if not (user["password_hash"].startswith("$2b$") or user["password_hash"].startswith("$2a$")):
            new_hash = hash_password(body.password)
            conn2 = get_db()
            conn2.execute("UPDATE users SET password_hash = ?, salt = '' WHERE id = ?", (new_hash, user["id"]))
            conn2.commit()
            conn2.close()

        session = create_session(user["id"])
        return {
            "token": session["token"],
            "refresh_token": session["refresh_token"],
            "user": {
                "id": user["id"],
                "username": user["username"],
                "display_name": user["display_name"],
                "email": user["email"],
                "role": user["role"],
                "avatar_url": user.get("avatar_url"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login error: {type(e).__name__}: {str(e)}")


@router.post("/logout")
def logout(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        conn = get_db()
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return {"ok": True}


@router.post("/refresh")
def refresh_token(body: RefreshRequest):
    conn = get_db()
    row = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.email, u.role, u.avatar_url
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.refresh_token = ? AND s.expires_at > ?""",
        (body.refresh_token, datetime.utcnow().isoformat()),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(401, "Invalid or expired refresh token")
    conn.execute("DELETE FROM sessions WHERE refresh_token = ?", (body.refresh_token,))
    conn.commit()
    conn.close()
    session = create_session(row["id"])
    return {
        "token": session["token"],
        "refresh_token": session["refresh_token"],
        "user": dict(row),
    }


@router.get("/me")
def me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user
