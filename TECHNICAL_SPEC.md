# TakvenOps — Technical Specification

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Web Dashboard (React)                  │
│  Board View │ List View │ Analytics │ Scanner │ Standups  │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────┴──────────────────────────────────┐
│                  Backend API (FastAPI)                    │
│  Tasks │ Sprints │ Team │ Scanner │ Verification │ Auth   │
└──────────────┬──────────────────┬───────────────────────┘
               │                  │
┌──────────────┴────┐  ┌─────────┴────────────────────────┐
│   SQLite / Postgres│  │  File System (.takvenops/)        │
│   (metadata, auth) │  │  (task files, synced with DB)     │
└───────────────────┘  └────────────────┬─────────────────┘
                                        │ reads/writes
                           ┌────────────┴──────────────┐
                           │  AI Agents                 │
                           │  (Antigravity, Claude Code) │
                           └───────────────────────────┘
```

## Directory Structure

```
takvenops/
├── frontend/                   # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── Board.jsx       # Kanban board (drag-and-drop)
│   │   │   ├── TaskCard.jsx    # Individual task card
│   │   │   ├── TaskDetail.jsx  # Task detail modal/panel
│   │   │   ├── ListView.jsx    # Table view of tasks
│   │   │   ├── SprintBar.jsx   # Sprint progress bar
│   │   │   ├── Sidebar.jsx     # Navigation sidebar
│   │   │   └── StandupView.jsx # Standup report display
│   │   ├── pages/
│   │   │   ├── BoardPage.jsx   # Main board view
│   │   │   ├── AnalyticsPage.jsx  # Charts and metrics
│   │   │   ├── ScannerPage.jsx    # Codebase scan results
│   │   │   ├── SettingsPage.jsx   # Team, sprint, repo config
│   │   │   └── StandupPage.jsx    # Daily standup reports
│   │   ├── api.js              # API client
│   │   ├── App.jsx             # Router
│   │   └── index.css           # Design system
│   └── package.json
│
├── backend/                    # FastAPI
│   ├── main.py                 # App entry point
│   ├── models.py               # SQLAlchemy models
│   ├── database.py             # DB connection
│   ├── routes/
│   │   ├── tasks.py            # CRUD for tasks
│   │   ├── sprints.py          # Sprint management
│   │   ├── team.py             # Team members
│   │   ├── scanner.py          # Codebase scanning
│   │   ├── standup.py          # Standup generation
│   │   └── analytics.py       # Metrics and charts
│   ├── services/
│   │   ├── task_sync.py        # Sync file system ↔ database
│   │   ├── scanner.py          # Codebase analysis engine
│   │   ├── verification.py     # Task verification runner
│   │   └── standup_generator.py # Daily standup builder
│   └── requirements.txt
│
├── .takvenops/                 # Task file system (lives in TARGET repo)
│   ├── config.yaml
│   ├── ai-instructions.md
│   ├── backlog/
│   ├── in-progress/
│   ├── review/
│   ├── done/
│   ├── blocked/
│   ├── templates/
│   └── reports/
│
└── scripts/
    └── takvenops.py            # CLI tool (already built — see existing_prototype/)
```

## Database Schema

```sql
-- Tasks (synced with .takvenops/ file system)
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,           -- e.g., "ROE-042"
    title TEXT NOT NULL,
    type TEXT DEFAULT 'feature',   -- feature, bug, tech-debt, research, ops
    priority TEXT DEFAULT 'P2',    -- P0, P1, P2, P3
    status TEXT DEFAULT 'backlog', -- backlog, assigned, in-progress, review, done, blocked
    assignee TEXT,                 -- team member ID
    sprint_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE,
    estimated_hours REAL,
    actual_hours REAL,
    labels TEXT,                   -- JSON array
    files_involved TEXT,           -- JSON array
    acceptance_criteria TEXT,      -- JSON array
    verification_type TEXT,
    verification_command TEXT,
    verification_ai_check TEXT,
    depends_on TEXT,               -- JSON array of task IDs
    blocks TEXT,                   -- JSON array of task IDs
    body_markdown TEXT,            -- Full markdown body
    completion_notes TEXT,
    file_path TEXT                 -- Path to .md file on disk
);

-- Sprints
CREATE TABLE sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    goal TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'planning' -- planning, active, completed
);

-- Team Members
CREATE TABLE team_members (
    id TEXT PRIMARY KEY,           -- e.g., "antigravity", "rahima"
    name TEXT NOT NULL,
    type TEXT DEFAULT 'human',     -- human, ai-agent
    role TEXT DEFAULT 'engineer',  -- founder, engineer, ai-agent, reviewer
    capabilities TEXT,             -- JSON array (for AI agents)
    max_concurrent_tasks INTEGER DEFAULT 3,
    avatar_url TEXT
);

-- Activity Log (for analytics)
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    action TEXT,                   -- created, assigned, moved, completed, verified
    from_status TEXT,
    to_status TEXT,
    actor TEXT,                    -- who did it (human or AI)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT                   -- JSON with extra info
);

-- Scan Results
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    repo_path TEXT,
    total_issues INTEGER,
    todo_count INTEGER,
    missing_tests_count INTEGER,
    error_handling_count INTEGER,
    results_json TEXT              -- Full scan results as JSON
);
```

## API Routes

```
# Tasks
GET    /api/tasks                    # List all tasks (filterable)
GET    /api/tasks/:id                # Get task detail
POST   /api/tasks                    # Create task
PUT    /api/tasks/:id                # Update task
DELETE /api/tasks/:id                # Delete task
POST   /api/tasks/:id/move           # Move task to new status
POST   /api/tasks/:id/assign         # Assign task

# Sprints
GET    /api/sprints                  # List sprints
POST   /api/sprints                  # Create sprint
PUT    /api/sprints/:id              # Update sprint
GET    /api/sprints/:id/tasks        # Get tasks in sprint

# Team
GET    /api/team                     # List team members
POST   /api/team                     # Add member
PUT    /api/team/:id                 # Update member

# Scanner
POST   /api/scanner/run              # Run codebase scan
GET    /api/scanner/results          # Get latest scan results

# Standup
GET    /api/standup/today             # Get today's standup
GET    /api/standup/history           # List past standups
POST   /api/standup/generate          # Generate standup report

# Analytics
GET    /api/analytics/velocity        # Tasks/sprint velocity
GET    /api/analytics/burndown        # Burndown chart data
GET    /api/analytics/ai-ratio        # AI vs human completion ratio
GET    /api/analytics/cycle-time      # Average cycle time

# Sync
POST   /api/sync/pull                 # Sync file system → database
POST   /api/sync/push                 # Sync database → file system
```

## File System ↔ Database Sync

The sync service ensures both sources stay in sync:

1. **On startup**: Read all `.takvenops/**/*.md` files → populate DB
2. **On file change**: Watch for file system changes → update DB
3. **On API change**: When task updated via API → write back to `.md` file
4. **Conflict resolution**: File system wins (it's the source of truth for AI agents)

## Codebase Scanner Engine

```python
class CodebaseScanner:
    """Analyzes a repository and generates task suggestions."""
    
    def scan(self, repo_path: str) -> ScanResult:
        issues = []
        issues += self._find_todos(repo_path)          # TODO/FIXME/HACK
        issues += self._find_missing_tests(repo_path)   # Untested files
        issues += self._find_complexity(repo_path)       # High cyclomatic complexity
        issues += self._find_error_handling(repo_path)   # Missing try/except
        issues += self._find_security(repo_path)         # Hardcoded secrets
        return ScanResult(issues=issues)
    
    def generate_tasks(self, scan_result: ScanResult) -> list[Task]:
        """Convert scan issues into task suggestions."""
        ...
```

## Verification Engine

```python
class VerificationEngine:
    """Validates task completion against acceptance criteria."""
    
    async def verify(self, task: Task) -> VerificationResult:
        results = []
        
        # 1. Run command-based verification
        if task.verification_command:
            result = await self._run_command(task.verification_command)
            results.append(result)
        
        # 2. Check acceptance criteria
        for criterion in task.acceptance_criteria:
            # AI-based check (optional)
            pass
        
        return VerificationResult(
            passed=all(r.passed for r in results),
            details=results
        )
```

## Authentication

Simple token-based auth (same as ROE platform):
- JWT tokens
- Roles: admin, member
- No SSO needed for MVP
