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
    body_markdown TEXT DEFAULT '', completion_notes TEXT DEFAULT '', file_path TEXT
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
    body_markdown TEXT DEFAULT '', completion_notes TEXT DEFAULT '', file_path TEXT
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

    # Seed data using the wrapped connection
    conn = get_db()

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
