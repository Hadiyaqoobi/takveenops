"""GitHub integration routes."""

import json
import re
import hashlib
import hmac
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db

router = APIRouter(prefix="/api/github", tags=["github"])

TASK_ID_PATTERN = re.compile(r'(ROE-\d{3,})', re.IGNORECASE)


class GitHubSetup(BaseModel):
    repo_owner: str
    repo_name: str
    access_token: str
    webhook_secret: str = ""


@router.post("/setup")
def setup_github(body: GitHubSetup):
    conn = get_db()
    conn.execute("DELETE FROM github_config")
    conn.execute(
        "INSERT INTO github_config (repo_owner, repo_name, access_token, webhook_secret) VALUES (?, ?, ?, ?)",
        (body.repo_owner, body.repo_name, body.access_token, body.webhook_secret)
    )
    conn.commit()
    conn.close()
    return {"ok": True, "repo": f"{body.repo_owner}/{body.repo_name}"}


@router.get("/config")
def get_github_config():
    conn = get_db()
    row = conn.execute("SELECT id, repo_owner, repo_name, created_at FROM github_config LIMIT 1").fetchone()
    conn.close()
    if not row:
        return {"connected": False}
    return {"connected": True, "repo_owner": row["repo_owner"], "repo_name": row["repo_name"]}


@router.delete("/disconnect")
def disconnect_github():
    conn = get_db()
    conn.execute("DELETE FROM github_config")
    conn.commit()
    conn.close()
    return {"ok": True}


@router.get("/tasks/{task_id}/links")
def get_task_links(task_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM task_links WHERE task_id = ? ORDER BY created_at DESC",
        (task_id.upper(),)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _extract_task_ids(text):
    if not text:
        return []
    return list(set(m.upper() for m in TASK_ID_PATTERN.findall(text)))


@router.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()
    payload = json.loads(body)
    event = request.headers.get("X-GitHub-Event", "")
    conn = get_db()

    if event == "pull_request":
        _handle_pr(conn, payload)
    elif event == "push":
        _handle_push(conn, payload)

    conn.commit()
    conn.close()
    return {"ok": True}


def _handle_pr(conn, payload):
    action = payload.get("action", "")
    pr = payload.get("pull_request", {})
    pr_title = pr.get("title", "")
    pr_body = pr.get("body", "") or ""
    pr_url = pr.get("html_url", "")
    pr_number = str(pr.get("number", 0))
    merged = pr.get("merged", False)

    task_ids = list(set(_extract_task_ids(pr_title) + _extract_task_ids(pr_body)))
    now = datetime.utcnow().isoformat()

    for task_id in task_ids:
        task = conn.execute("SELECT id, status FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            continue

        if action in ("opened", "reopened"):
            existing = conn.execute(
                "SELECT id FROM task_links WHERE task_id = ? AND external_id = ?",
                (task_id, pr_number)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO task_links (task_id, link_type, url, title, status, external_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (task_id, "pr", pr_url, pr_title, "open", pr_number)
                )
            if task["status"] not in ("review", "done"):
                conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", ("review", now, task_id))
                conn.execute(
                    "INSERT INTO activity_log (task_id, action, from_status, to_status, actor) VALUES (?, ?, ?, ?, ?)",
                    (task_id, "moved", task["status"], "review", "github")
                )

        elif action == "closed" and merged:
            conn.execute(
                "UPDATE task_links SET status = ? WHERE task_id = ? AND external_id = ?",
                ("merged", task_id, pr_number)
            )
            if task["status"] != "done":
                conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", ("done", now, task_id))
                conn.execute(
                    "INSERT INTO activity_log (task_id, action, from_status, to_status, actor) VALUES (?, ?, ?, ?, ?)",
                    (task_id, "moved", task["status"], "done", "github")
                )


def _handle_push(conn, payload):
    for commit in payload.get("commits", []):
        message = commit.get("message", "")
        sha = commit.get("id", "")[:8]
        url = commit.get("url", "")
        author = commit.get("author", {}).get("username", "unknown")

        for task_id in _extract_task_ids(message):
            task = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not task:
                continue
            conn.execute(
                "INSERT INTO task_links (task_id, link_type, url, title, status, external_id) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, "commit", url, message[:100], "pushed", sha)
            )
            conn.execute(
                "INSERT INTO activity_log (task_id, action, actor, details) VALUES (?, ?, ?, ?)",
                (task_id, "commit_linked", author, message[:100])
            )
