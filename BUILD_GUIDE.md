# TakvenOps — Build Guide for Claude Code

## Instructions

You are building TakvenOps, an AI-native project management platform. Read ALL docs in this folder before starting.

## Build Order

### Step 1: Initialize the Project
```bash
# Create a Vite + React frontend
npx -y create-vite@latest frontend -- --template react
cd frontend && npm install

# Install additional frontend deps
npm install react-router-dom lucide-react @dnd-kit/core @dnd-kit/sortable recharts

# Create backend
cd ..
mkdir backend
pip install fastapi uvicorn sqlalchemy aiosqlite pyyaml python-multipart
```

### Step 2: Build Backend First
1. Create `backend/database.py` — SQLite connection with async support
2. Create `backend/models.py` — SQLAlchemy models (see TECHNICAL_SPEC.md schema)
3. Create `backend/main.py` — FastAPI app with CORS
4. Create `backend/routes/tasks.py` — Full CRUD for tasks
5. Create `backend/routes/sprints.py` — Sprint management
6. Create `backend/routes/team.py` — Team member management
7. Create `backend/routes/scanner.py` — Codebase scan endpoint
8. Create `backend/routes/standup.py` — Standup generation
9. Create `backend/routes/analytics.py` — Metrics queries
10. Create `backend/services/task_sync.py` — File system ↔ DB sync
11. Create `backend/services/scanner.py` — Adapt from `existing_prototype/takvenops_cli.py` scan logic

### Step 3: Build Frontend
1. Create design system in `frontend/src/index.css` (see UI_DESIGN.md)
2. Create `frontend/src/App.jsx` with routing
3. Create `frontend/src/api.js` — API client
4. Create `frontend/src/components/Sidebar.jsx`
5. Create `frontend/src/pages/BoardPage.jsx` — Kanban with drag-and-drop
6. Create `frontend/src/components/TaskCard.jsx`
7. Create `frontend/src/components/TaskDetail.jsx` — Side panel
8. Create `frontend/src/pages/ListView.jsx` — Table view
9. Create `frontend/src/pages/StandupPage.jsx`
10. Create `frontend/src/pages/ScannerPage.jsx`
11. Create `frontend/src/pages/AnalyticsPage.jsx`
12. Create `frontend/src/pages/SettingsPage.jsx`

### Step 4: Test
1. Start backend: `cd backend && uvicorn main:app --reload --port 8001`
2. Start frontend: `cd frontend && npm run dev`
3. Verify all pages load
4. Create a task, move it, verify it shows on board

## Key Design Decisions

1. **SQLite** for database — no setup, single file, good for solo/small team
2. **File sync is bidirectional** — DB and `.takvenops/` files stay in sync
3. **File system is source of truth** — if there's a conflict, file system wins
4. **Dark theme** — this is a developer tool, dark mode is expected
5. **No external auth for MVP** — simple token auth or no auth (local tool)
6. **Kanban drag-and-drop** — use @dnd-kit for smooth animations

## Existing Code to Reuse

The `existing_prototype/` folder contains:
- `takvenops_cli.py` — Working CLI with frontmatter parser, codebase scanner, standup generator
- `config.yaml` — Team config format
- `ai-instructions.md` — AI agent integration instructions
- `backlog/*.md` — Sample task files showing the frontmatter format
- `templates/*.md` — Task creation templates

The **frontmatter parser** in `takvenops_cli.py` (function `parse_frontmatter`) and the **codebase scanner** (function `cmd_scan`) can be directly adapted for the backend.

## Quality Bar

- The UI must look as polished as Linear (linear.app)
- Dark mode only for MVP
- All interactions should feel instant (< 200ms)
- Board drag-and-drop must be smooth
- Task cards must show priority, assignee, labels at a glance
- AI-assigned tasks should have a subtle ✨ indicator
