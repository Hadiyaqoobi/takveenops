"""Authentication routes for TakvenOps."""

import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""
    email: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode()).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    conn = get_db()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def get_current_user(request: Request):
    """Extract user from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    conn = get_db()
    row = conn.execute(
        """SELECT u.id, u.username, u.display_name, u.email, u.role, u.created_at
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

    salt = secrets.token_hex(16)
    pw_hash = hash_password(body.password, salt)
    display = body.display_name or body.username

    cursor = conn.execute(
        "INSERT INTO users (username, display_name, email, password_hash, salt) VALUES (?, ?, ?, ?, ?)",
        (body.username, display, body.email, pw_hash, salt),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    token = create_session(user_id)
    return {
        "token": token,
        "user": {"id": user_id, "username": body.username, "display_name": display, "email": body.email, "role": "member"},
    }


@router.post("/login")
def login(body: LoginRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
    conn.close()

    if not user:
        raise HTTPException(401, "Invalid username or password")

    pw_hash = hash_password(body.password, user["salt"])
    if pw_hash != user["password_hash"]:
        raise HTTPException(401, "Invalid username or password")

    token = create_session(user["id"])
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "email": user["email"],
            "role": user["role"],
        },
    }


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


@router.get("/me")
def me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")
    return user
