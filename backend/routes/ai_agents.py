"""AI Agent session tracking routes."""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])


class SessionStart(BaseModel):
    task_id: Optional[str] = None
    agent_id: str
    model: str
    action: str = ""
    project_id: str = "default"


class SessionEnd(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    status: str = "completed"
    notes: str = ""


@router.post("/sessions/start")
def start_session(body: SessionStart, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    now = datetime.utcnow().isoformat()
    conn.execute(
        """INSERT INTO ai_agent_sessions
           (task_id, agent_id, model, action, project_id, started_at, status)
           VALUES (?, ?, ?, ?, ?, ?, 'active')""",
        (body.task_id, body.agent_id, body.model, body.action, body.project_id, now)
    )
    conn.commit()
    # Re-query to get the new session ID (works on both SQLite and PG)
    row = conn.execute(
        "SELECT id FROM ai_agent_sessions WHERE agent_id = ? AND started_at = ? ORDER BY id DESC LIMIT 1",
        (body.agent_id, now)
    ).fetchone()
    session_id = row["id"] if row else None
    conn.close()
    return {"session_id": session_id, "started_at": now}


@router.post("/sessions/{session_id}/end")
def end_session(session_id: int, body: SessionEnd, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    session = conn.execute(
        "SELECT * FROM ai_agent_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if not session:
        conn.close()
        raise HTTPException(404, "Session not found")

    now = datetime.utcnow().isoformat()
    try:
        start_dt = datetime.fromisoformat(str(session["started_at"]))
        duration = (datetime.utcnow() - start_dt).total_seconds()
    except Exception:
        duration = None

    total_tokens = body.input_tokens + body.output_tokens

    conn.execute(
        """UPDATE ai_agent_sessions SET
           ended_at = ?, duration_seconds = ?, input_tokens = ?,
           output_tokens = ?, total_tokens = ?, cost_usd = ?,
           status = ?, notes = ?
           WHERE id = ?""",
        (now, duration, body.input_tokens, body.output_tokens,
         total_tokens, body.cost_usd, body.status, body.notes, session_id)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM ai_agent_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row)


@router.get("/sessions")
def list_sessions(agent_id: str = None, task_id: str = None, project_id: str = None, limit: int = 50):
    conn = get_db()
    query = "SELECT * FROM ai_agent_sessions WHERE 1=1"
    params = []
    if agent_id:
        query += " AND agent_id = ?"
        params.append(agent_id)
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)
    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    query += " ORDER BY started_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/cost-summary")
def cost_summary(project_id: str = None):
    conn = get_db()
    params = []
    filter_clause = "WHERE 1=1"
    if project_id:
        filter_clause += " AND project_id = ?"
        params.append(project_id)

    by_agent = conn.execute(
        f"""SELECT agent_id, model,
               COUNT(*) as session_count,
               SUM(total_tokens) as total_tokens,
               SUM(cost_usd) as total_cost_usd,
               AVG(duration_seconds) as avg_duration_seconds
            FROM ai_agent_sessions
            {filter_clause}
            GROUP BY agent_id, model
            ORDER BY total_cost_usd DESC""",
        params
    ).fetchall()

    by_project = conn.execute(
        """SELECT project_id,
               COUNT(*) as session_count,
               SUM(total_tokens) as total_tokens,
               SUM(cost_usd) as total_cost_usd
            FROM ai_agent_sessions
            GROUP BY project_id
            ORDER BY total_cost_usd DESC"""
    ).fetchall()

    conn.close()
    return {
        "by_agent": [dict(r) for r in by_agent],
        "by_project": [dict(r) for r in by_project],
    }
