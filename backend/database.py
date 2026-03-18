"""Database connection and initialization for TakvenOps.

Supports PostgreSQL (via DATABASE_URL) for production and SQLite for local dev.
The PG wrapper translates ? → %s so all route code works unchanged.
"""

import hashlib
import secrets
import os
import sqlite3
from pathlib import Path

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = DATABASE_URL.startswith("postgres")

if USE_PG:
    import psycopg2
    import psycopg2.extras

DB_PATH = Path(__file__).parent / "takvenops.db"


# ── PostgreSQL wrappers ──────────────────────────

class PgRow:
    """Makes psycopg2 dict row behave like sqlite3.Row."""
    def __init__(self, data):
        self._data = dict(data) if data else {}

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)


class PgCursorWrapper:
    """Wraps psycopg2 cursor to return PgRow objects."""
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def lastrowid(self):
        # PostgreSQL doesn't have lastrowid; use RETURNING id in your INSERT
        return None

    def fetchone(self):
        row = self._cursor.fetchone()
        return PgRow(row) if row else None

    def fetchall(self):
        return [PgRow(r) for r in self._cursor.fetchall()]


class PgConnWrapper:
    """Wraps psycopg2 connection so conn.execute("... ? ...", params) works."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        sql = sql.replace("?", "%s")
        cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql, params or ())
        return PgCursorWrapper(cursor)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# ── Connection ───────────────────────────────────

def get_db():
    """Get a database connection (SQLite or PostgreSQL)."""
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        return PgConnWrapper(conn)
    else:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn


# ── Schema ───────────────────────────────────────

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', status TEXT DEFAULT 'backlog', assignee TEXT,
    sprint_id INTEGER, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW(),
    due_date DATE, estimated_hours REAL, actual_hours REAL,
    labels TEXT DEFAULT '[]', files_involved TEXT DEFAULT '[]',
    acceptance_criteria TEXT DEFAULT '[]', verification_type TEXT,
    verification_command TEXT, verification_ai_check TEXT,
    depends_on TEXT DEFAULT '[]', blocks TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', completion_notes TEXT DEFAULT '', file_path TEXT,
    parent_task_id TEXT
);
CREATE TABLE IF NOT EXISTS sprints (
    id SERIAL PRIMARY KEY, name TEXT, goal TEXT, start_date DATE, end_date DATE,
    status TEXT DEFAULT 'planning'
);
CREATE TABLE IF NOT EXISTS team_members (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT DEFAULT 'human',
    role TEXT DEFAULT 'engineer', capabilities TEXT DEFAULT '[]',
    max_concurrent_tasks INTEGER DEFAULT 3, avatar_url TEXT
);
CREATE TABLE IF NOT EXISTS activity_log (
    id SERIAL PRIMARY KEY, task_id TEXT, action TEXT, from_status TEXT,
    to_status TEXT, actor TEXT, timestamp TIMESTAMP DEFAULT NOW(), details TEXT
);
CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY, scan_date TIMESTAMP DEFAULT NOW(), repo_path TEXT,
    total_issues INTEGER, todo_count INTEGER, missing_tests_count INTEGER,
    error_handling_count INTEGER, results_json TEXT
);
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, display_name TEXT NOT NULL,
    email TEXT DEFAULT '', password_hash TEXT NOT NULL, salt TEXT NOT NULL,
    role TEXT DEFAULT 'member', created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY, token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(), expires_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY, task_id TEXT NOT NULL,
    user_id INTEGER, username TEXT NOT NULL,
    body TEXT NOT NULL, created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_comments_task_id ON comments(task_id);
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
    type TEXT NOT NULL, task_id TEXT, message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read);
CREATE TABLE IF NOT EXISTS github_config (
    id SERIAL PRIMARY KEY, repo_owner TEXT NOT NULL, repo_name TEXT NOT NULL,
    access_token TEXT NOT NULL, webhook_secret TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS task_links (
    id SERIAL PRIMARY KEY, task_id TEXT NOT NULL,
    link_type TEXT NOT NULL, url TEXT NOT NULL, title TEXT DEFAULT '',
    status TEXT DEFAULT 'open', external_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS task_templates (
    id SERIAL PRIMARY KEY, name TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', labels TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', created_by TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS time_entries (
    id SERIAL PRIMARY KEY, task_id TEXT NOT NULL, user_id INTEGER,
    username TEXT NOT NULL, hours REAL NOT NULL, description TEXT DEFAULT '',
    logged_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id);
CREATE TABLE IF NOT EXISTS recurring_rules (
    id SERIAL PRIMARY KEY, title TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', assignee TEXT, labels TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', frequency TEXT DEFAULT 'weekly',
    next_run DATE NOT NULL, active BOOLEAN DEFAULT TRUE,
    created_by TEXT, created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS webhook_config (
    id SERIAL PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL,
    events TEXT DEFAULT '[]', active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY, filename TEXT NOT NULL, original_name TEXT NOT NULL,
    content_type TEXT, size_bytes INTEGER, entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL, uploaded_by INTEGER, uploaded_by_username TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id);
CREATE TABLE IF NOT EXISTS standup_entries (
    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, username TEXT NOT NULL,
    standup_date DATE NOT NULL, yesterday TEXT DEFAULT '[]', today TEXT DEFAULT '[]',
    blockers TEXT DEFAULT '[]', notes TEXT DEFAULT '', audio_transcript TEXT DEFAULT '',
    submitted_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_standup_entries_date ON standup_entries(standup_date);
CREATE TABLE IF NOT EXISTS standup_meetings (
    id SERIAL PRIMARY KEY, title TEXT NOT NULL, scheduled_time TEXT DEFAULT '09:00',
    frequency TEXT DEFAULT 'daily', participants TEXT DEFAULT '[]',
    notes TEXT DEFAULT '', created_by TEXT,
    active BOOLEAN DEFAULT TRUE, created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
    key TEXT NOT NULL, owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS project_members (
    id SERIAL PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role TEXT DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id);
CREATE TABLE IF NOT EXISTS ai_agent_sessions (
    id SERIAL PRIMARY KEY, task_id TEXT, agent_id TEXT NOT NULL,
    model TEXT NOT NULL, started_at TIMESTAMP DEFAULT NOW(), ended_at TIMESTAMP,
    duration_seconds REAL, input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0, total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0, action TEXT DEFAULT '', status TEXT DEFAULT 'active',
    notes TEXT DEFAULT '', project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_task ON ai_agent_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_agent ON ai_agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_project ON ai_agent_sessions(project_id);
CREATE TABLE IF NOT EXISTS invitations (
    id SERIAL PRIMARY KEY, email TEXT NOT NULL, token TEXT UNIQUE NOT NULL,
    invited_by TEXT NOT NULL, role TEXT DEFAULT 'member',
    project_id TEXT DEFAULT 'default', status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(), expires_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE TABLE IF NOT EXISTS email_preferences (
    id SERIAL PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    on_task_assigned BOOLEAN DEFAULT TRUE,
    on_task_mentioned BOOLEAN DEFAULT TRUE,
    on_task_commented BOOLEAN DEFAULT TRUE,
    on_status_changed BOOLEAN DEFAULT FALSE,
    on_deadline_reminder BOOLEAN DEFAULT TRUE,
    on_escalation BOOLEAN DEFAULT TRUE
);
"""

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', status TEXT DEFAULT 'backlog', assignee TEXT,
    sprint_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, due_date DATE,
    estimated_hours REAL, actual_hours REAL,
    labels TEXT DEFAULT '[]', files_involved TEXT DEFAULT '[]',
    acceptance_criteria TEXT DEFAULT '[]', verification_type TEXT,
    verification_command TEXT, verification_ai_check TEXT,
    depends_on TEXT DEFAULT '[]', blocks TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', completion_notes TEXT DEFAULT '', file_path TEXT,
    parent_task_id TEXT
);
CREATE TABLE IF NOT EXISTS sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, goal TEXT,
    start_date DATE, end_date DATE, status TEXT DEFAULT 'planning'
);
CREATE TABLE IF NOT EXISTS team_members (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT DEFAULT 'human',
    role TEXT DEFAULT 'engineer', capabilities TEXT DEFAULT '[]',
    max_concurrent_tasks INTEGER DEFAULT 3, avatar_url TEXT
);
CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, action TEXT,
    from_status TEXT, to_status TEXT, actor TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, details TEXT
);
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT, scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    repo_path TEXT, total_issues INTEGER, todo_count INTEGER,
    missing_tests_count INTEGER, error_handling_count INTEGER, results_json TEXT
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL, email TEXT DEFAULT '', password_hash TEXT NOT NULL,
    salt TEXT NOT NULL, role TEXT DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
    user_id INTEGER, username TEXT NOT NULL,
    body TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_comments_task_id ON comments(task_id);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    type TEXT NOT NULL, task_id TEXT, message TEXT NOT NULL,
    read INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, read);
CREATE TABLE IF NOT EXISTS github_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT, repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL, access_token TEXT NOT NULL, webhook_secret TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS task_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
    link_type TEXT NOT NULL, url TEXT NOT NULL, title TEXT DEFAULT '',
    status TEXT DEFAULT 'open', external_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS task_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', labels TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL, user_id INTEGER,
    username TEXT NOT NULL, hours REAL NOT NULL, description TEXT DEFAULT '',
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries(task_id);
CREATE TABLE IF NOT EXISTS recurring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, type TEXT DEFAULT 'feature',
    priority TEXT DEFAULT 'P2', assignee TEXT, labels TEXT DEFAULT '[]',
    body_markdown TEXT DEFAULT '', frequency TEXT DEFAULT 'weekly',
    next_run DATE NOT NULL, active INTEGER DEFAULT 1,
    created_by TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS webhook_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT NOT NULL,
    events TEXT DEFAULT '[]', active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, original_name TEXT NOT NULL,
    content_type TEXT, size_bytes INTEGER, entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL, uploaded_by INTEGER, uploaded_by_username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id);
CREATE TABLE IF NOT EXISTS standup_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, username TEXT NOT NULL,
    standup_date DATE NOT NULL, yesterday TEXT DEFAULT '[]', today TEXT DEFAULT '[]',
    blockers TEXT DEFAULT '[]', notes TEXT DEFAULT '', audio_transcript TEXT DEFAULT '',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_standup_entries_date ON standup_entries(standup_date);
CREATE TABLE IF NOT EXISTS standup_meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, scheduled_time TEXT DEFAULT '09:00',
    frequency TEXT DEFAULT 'daily', participants TEXT DEFAULT '[]',
    notes TEXT DEFAULT '', created_by TEXT,
    active INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '',
    key TEXT NOT NULL, owner_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL, user_id INTEGER NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user ON project_members(user_id);
CREATE TABLE IF NOT EXISTS ai_agent_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, agent_id TEXT NOT NULL,
    model TEXT NOT NULL, started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, ended_at TIMESTAMP,
    duration_seconds REAL, input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0, total_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0, action TEXT DEFAULT '', status TEXT DEFAULT 'active',
    notes TEXT DEFAULT '', project_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_task ON ai_agent_sessions(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_agent ON ai_agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_project ON ai_agent_sessions(project_id);
CREATE TABLE IF NOT EXISTS invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, token TEXT UNIQUE NOT NULL,
    invited_by TEXT NOT NULL, role TEXT DEFAULT 'member',
    project_id TEXT DEFAULT 'default', status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, expires_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE TABLE IF NOT EXISTS email_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE NOT NULL,
    on_task_assigned INTEGER DEFAULT 1,
    on_task_mentioned INTEGER DEFAULT 1,
    on_task_commented INTEGER DEFAULT 1,
    on_status_changed INTEGER DEFAULT 0,
    on_deadline_reminder INTEGER DEFAULT 1,
    on_escalation INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""


def init_db():
    """Initialize database tables and seed data."""
    if USE_PG:
        raw = psycopg2.connect(DATABASE_URL)
        raw.cursor().execute(PG_SCHEMA)
        raw.commit()
        raw.close()
    else:
        raw = sqlite3.connect(str(DB_PATH))
        raw.executescript(SQLITE_SCHEMA)
        raw.commit()
        raw.close()

    # Idempotent migration: add avatar_url to users if missing
    mconn = get_db()
    try:
        mconn.execute("SELECT avatar_url FROM users LIMIT 1")
    except Exception:
        mconn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        mconn.commit()
    mconn.close()

    # Migration: add project_id to tasks
    mconn = get_db()
    try:
        mconn.execute("SELECT project_id FROM tasks LIMIT 1")
    except Exception:
        mconn.execute("ALTER TABLE tasks ADD COLUMN project_id TEXT DEFAULT 'default'")
        mconn.commit()
    mconn.close()

    # Migration: add project_id to sprints
    mconn = get_db()
    try:
        mconn.execute("SELECT project_id FROM sprints LIMIT 1")
    except Exception:
        mconn.execute("ALTER TABLE sprints ADD COLUMN project_id TEXT DEFAULT 'default'")
        mconn.commit()
    mconn.close()

    # Migration: add project_id to team_members
    mconn = get_db()
    try:
        mconn.execute("SELECT project_id FROM team_members LIMIT 1")
    except Exception:
        mconn.execute("ALTER TABLE team_members ADD COLUMN project_id TEXT DEFAULT 'default'")
        mconn.commit()
    mconn.close()

    # Migration: add refresh_token to sessions
    mconn = get_db()
    try:
        mconn.execute("SELECT refresh_token FROM sessions LIMIT 1")
    except Exception:
        mconn.execute("ALTER TABLE sessions ADD COLUMN refresh_token TEXT")
        mconn.commit()
    mconn.close()

    # Seed data using the wrapped connection
    conn = get_db()

    # Seed default project
    row = conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()
    if row["c"] == 0:
        conn.execute(
            "INSERT INTO projects (id, name, description, key) VALUES (?, ?, ?, ?)",
            ("default", "TakvenOps", "Default project", "TOK")
        )

    row = conn.execute("SELECT COUNT(*) as c FROM team_members").fetchone()
    if row["c"] == 0:
        for m in [
            ("antigravity", "Antigravity (Claude Code)", "ai-agent", "ai-agent", '["code", "test", "refactor", "debug"]', 5),
            ("claude-code", "Claude Code", "ai-agent", "ai-agent", '["code", "test", "refactor", "debug"]', 5),
        ]:
            conn.execute("INSERT INTO team_members (id, name, type, role, capabilities, max_concurrent_tasks) VALUES (?, ?, ?, ?, ?, ?)", m)

    row = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()
    if row["c"] == 0:
        salt = secrets.token_hex(16)
        pw = hashlib.sha256((salt + "admin123").encode()).hexdigest()
        conn.execute(
            "INSERT INTO users (username, display_name, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "Admin", "admin@takvenops.local", pw, salt, "admin")
        )

    conn.commit()
    conn.close()
