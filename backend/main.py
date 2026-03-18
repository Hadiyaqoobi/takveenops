"""TakvenOps — FastAPI backend entry point."""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from .database import init_db
from .routes import tasks, sprints, team, scanner, standup, analytics, auth, profile, comments, notifications, github
from .routes import templates, time_tracking, myday, recurring, webhooks, websocket, attachments
from .routes import projects, ai_agents, invitations
from .services.task_sync import sync_from_filesystem

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(Path(__file__).parent / "uploads")))

app = FastAPI(title="TakvenOps API", version="1.0.0")

# CORS: allow configured frontend URL + localhost for dev
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")
cors_origins = ["http://localhost:5173", "http://localhost:3000"]
if FRONTEND_URL:
    cors_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(tasks.router)
app.include_router(sprints.router)
app.include_router(team.router)
app.include_router(scanner.router)
app.include_router(standup.router)
app.include_router(analytics.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(comments.router)
app.include_router(notifications.router)
app.include_router(github.router)
app.include_router(templates.router)
app.include_router(time_tracking.router)
app.include_router(myday.router)
app.include_router(recurring.router)
app.include_router(webhooks.router)
app.include_router(websocket.router)
app.include_router(attachments.router)
app.include_router(projects.router)
app.include_router(ai_agents.router)
app.include_router(invitations.router)


@app.on_event("startup")
def startup():
    init_db()
    # Create upload directories
    (UPLOAD_DIR / "tasks").mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)
    # Serve uploaded files at /api/uploads/
    app.mount("/api/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "TakvenOps"}


@app.post("/api/sync/pull")
def sync_pull(body: dict = None):
    """Sync .takvenops/ files into database."""
    ops_dir = (body or {}).get("ops_dir", "")
    if not ops_dir:
        return {"error": "ops_dir is required"}
    result = sync_from_filesystem(ops_dir)
    return result


@app.post("/api/sync/push")
def sync_push():
    """Sync database to file system (placeholder)."""
    return {"message": "Push sync not yet implemented"}
