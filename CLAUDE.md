# TakvenOps — AI-Native Project Management

TakvenOps is the project management system for this codebase. All task tracking, assignments, and status updates happen through TakvenOps.

## Task Management CLI

Use the CLI at `ops.py` (in the project root) to manage tasks. The TakvenOps backend must be running on port 8001.

### Quick Reference

```bash
# View the board
python ops.py board

# List all tasks
python ops.py tasks

# List tasks by status or assignee
python ops.py tasks --status in-progress
python ops.py tasks --assignee antigravity

# See your assigned tasks
python ops.py my-tasks antigravity
python ops.py my-tasks claude-code

# Create a new task
python ops.py create "Fix login validation bug" --type bug --priority P1 --assignee admin
python ops.py create "Add dark mode support" --type feature --priority P2 --assignee antigravity --labels "ui,frontend"

# Assign a task to someone
python ops.py assign TOK-001 antigravity
python ops.py assign TOK-002 claude-code
python ops.py assign TOK-003 admin

# Move a task to a new status
python ops.py move TOK-001 in-progress    # Start working on it
python ops.py move TOK-001 review         # Ready for review
python ops.py move TOK-001 done           # Completed

# Mark a task as done
python ops.py complete TOK-001

# View task details
python ops.py detail TOK-001

# List team members
python ops.py team
```

### Statuses
- `backlog` — New, not started
- `in-progress` — Actively being worked on
- `review` — Resolved, needs review
- `done` — Closed / completed
- `blocked` — Blocked by something

### Task Types
- `feature` — New functionality
- `bug` — Bug fix
- `tech-debt` — Technical debt / refactoring
- `research` — Investigation / research
- `ops` — Operations / infrastructure

### Priorities
- `P0` — Critical (fix immediately)
- `P1` — High priority
- `P2` — Normal priority
- `P3` — Low priority

## Workflow for AI Agents

When asked to work on tasks:

1. **Check your tasks**: `python ops.py my-tasks <your-name>`
2. **Start a task**: `python ops.py move <task-id> in-progress`
3. **Do the work**: Implement the changes
4. **Complete it**: `python ops.py complete <task-id>`

When asked to assign tasks:
- `python ops.py assign <task-id> <person-name>`
- Use `python ops.py team` to see available team members

When asked to create tasks:
- `python ops.py create "Title" --type <type> --priority <priority> --assignee <name>`

## Architecture

- **Backend**: FastAPI + SQLite at `backend/` (runs on port 8001)
- **Frontend**: React + Vite at `frontend/` (runs on port 5173)
- **CLI**: `ops.py` in project root (calls the API)
- **Web UI**: http://localhost:5173 (Kanban board, work items, analytics)

### Starting the servers
```bash
# Backend
cd C:\Users\hyaqo\Desktop\TakvenOps && python -m uvicorn backend.main:app --port 8001

# Frontend
cd C:\Users\hyaqo\Desktop\TakvenOps\frontend && npx vite --port 5173
```

## Team Members

Team members are managed in Settings. Default AI agents:
- `antigravity` — Antigravity (Claude Code)
- `claude-code` — Claude Code
