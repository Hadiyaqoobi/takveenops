# TakvenOps — AI-Native Project Management

TakvenOps is the project management system for this codebase. All task tracking, assignments, and status updates happen through TakvenOps.

## Production API Access

The live TakvenOps platform is deployed at:
- **API**: `https://takvenops-api.onrender.com/api`
- **Frontend**: Vercel (TakvenOps web UI)

### Authentication

To interact with the production API, first login to get a token:

```bash
# Login as Antigravity agent
TOKEN=$(curl -s -X POST "https://takvenops-api.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"antigravity","password":"AGbot2026ops"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")
```

Then use the token in all subsequent requests:
```bash
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" ...
```

### API Quick Reference (Production)

```bash
# List all tasks
curl -s -H "Authorization: Bearer $TOKEN" "https://takvenops-api.onrender.com/api/tasks"

# Create a task
curl -s -X POST "https://takvenops-api.onrender.com/api/tasks" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Task title","type":"feature","priority":"P2","assignee":"username","status":"backlog"}'

# Assign a task
curl -s -X POST "https://takvenops-api.onrender.com/api/tasks/TASK_ID/assign" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"assignee":"username"}'

# Move task status
curl -s -X POST "https://takvenops-api.onrender.com/api/tasks/TASK_ID/move" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"in-progress"}'

# Update a task
curl -s -X PUT "https://takvenops-api.onrender.com/api/tasks/TASK_ID" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"priority":"P1","due_date":"2026-04-01"}'

# Add a comment
curl -s -X POST "https://takvenops-api.onrender.com/api/tasks/TASK_ID/comments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"body":"Comment text here"}'

# List team members
curl -s -H "Authorization: Bearer $TOKEN" "https://takvenops-api.onrender.com/api/team"

# Get sprints
curl -s -H "Authorization: Bearer $TOKEN" "https://takvenops-api.onrender.com/api/sprints"

# Create a sprint
curl -s -X POST "https://takvenops-api.onrender.com/api/sprints" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Sprint 1","goal":"MVP delivery","start_date":"2026-03-18","end_date":"2026-04-01"}'

# Send email to team member
curl -s -X POST "https://takvenops-api.onrender.com/api/send-email" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"to":"email@example.com","subject":"Subject","body_html":"<p>HTML body</p>"}'

# Invite a new user
curl -s -X POST "https://takvenops-api.onrender.com/api/invitations" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","role":"member","project_id":"default"}'
```

## Task Management CLI (Local Dev)

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

- **Backend**: FastAPI + SQLite/PostgreSQL at `backend/` (port 8001 local, Render production)
- **Frontend**: React + Vite at `frontend/` (port 5173 local, Vercel production)
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

| Name | Username | Role | Type |
|------|----------|------|------|
| Hadi Yaqoobi | admin / hadiyaqoobi | Founder / Admin | Human |
| Rahima Paiman | rahimapaiman | Head of Operations & Partnerships / Admin | Human |
| Sahar Nikzad | saharnikzad | AI Data Quality Analyst / Intern | Human |
| Antigravity | antigravity | AI Agent | AI |
| Claude Code | claude-code | AI Agent | AI |
