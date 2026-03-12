# TakvenOps — AI Supervisor Feature Spec

## Overview

AI agents (Antigravity, Claude Code) act as **tech leads** — they can assign tasks to human teammates, review completed work, and automatically detect all activity in the tool.

---

## Feature 1: AI Task Assignment to Humans

### How It Works
AI analyzes the codebase, team member skills, and current workload, then assigns tasks intelligently.

### Assignment Logic
```
1. AI scans codebase → finds issues (bugs, missing tests, etc.)
2. AI creates task files in .takvenops/backlog/
3. AI checks team members from config.yaml:
   - Skills match (frontend → frontend developer, ML → ML engineer)
   - Current workload (who has fewest in-progress tasks)
   - Timezone (assign urgent tasks to whoever is awake)
4. AI assigns task → sets assignee field + sends notification
5. AI writes assignment rationale in the task body
```

### Example Task Auto-Assigned by AI
```yaml
---
id: ROE-015
title: Add error handling to placements route
type: bug
priority: P1
status: assigned
assignee: human:rahima
assigned_by: antigravity          # NEW FIELD — who assigned this
assignment_reason: >              # NEW FIELD — why this person
  Rahima has backend Python experience and currently has
  2 tasks (lowest on team). This is a P1 bug in her timezone.
created: 2026-03-11
---
```

### Team Skill Mapping (in config.yaml)
```yaml
team:
  - id: rahima
    name: Rahima Khan
    skills: [python, backend, ml, data-collection]
    timezone: America/Toronto
    max_tasks: 5
  - id: dev3
    name: Team Member 3
    skills: [react, frontend, css, testing]
    timezone: Asia/Kabul
    max_tasks: 4
```

---

## Feature 2: AI Code Review of Human Work

### How It Works
When a human moves a task to "Review", AI automatically reviews their work.

### Review Process
```
1. Human completes task → moves to .takvenops/review/
2. AI detects the status change (file watcher or webhook)
3. AI reads the task's acceptance criteria
4. AI checks git diff for files_involved — what changed?
5. AI runs verification command (pytest, lint, etc.)
6. AI writes a review in the task file:

## AI Review — March 12, 2026
**Reviewer**: Antigravity
**Verdict**: ✅ Approved / ⚠️ Changes Requested / ❌ Rejected

### Checklist
- [x] Acceptance criterion 1: Error handling added to all endpoints
- [x] Acceptance criterion 2: Tests pass (12/12)
- [ ] Acceptance criterion 3: Documentation updated ← MISSING

### Code Quality
- Style: ✅ Follows project conventions
- Tests: ✅ All pass, good coverage
- Security: ⚠️ Input validation missing on line 45 of placements.py

### Suggestions
1. Add input validation for `placement_id` parameter
2. Consider adding a rollback on database errors

### Decision
Changes requested — please add input validation before approval.
```

7. If approved → AI moves to done/
8. If changes requested → AI moves back to in-progress/ with feedback

### Review Severity Levels
- **Auto-approve**: P3 tech-debt tasks with passing tests
- **Light review**: P2 features — check tests pass + acceptance criteria
- **Full review**: P0/P1 bugs — check diff, tests, side effects, security

---

## Feature 3: Automatic Activity Detection

### What It Detects

| Activity | Detection Method | Action |
|----------|-----------------|--------|
| **Git commit** | Watch `.git/` for new commits | Log commit, link to related tasks |
| **File changed** | File system watcher on project dir | Check if file is in any task's `files_involved` |
| **Task status change** | Watch `.takvenops/` directories | Log in activity feed, trigger review if moved to review/ |
| **New TODO added** | Periodic codebase scan (background) | Auto-create task or add to existing backlog item |
| **Test failure** | Watch CI/test output | Create P1 bug task, assign to last committer |
| **Long idle task** | Daily check | Alert if task in-progress > 3 days with no file changes |
| **Sprint deadline** | Daily check | Warn if sprint is behind pace |
| **Dependency resolved** | Task moved to done → check `blocks` | Auto-unblock dependent tasks |

### Activity Feed (Database)
```sql
CREATE TABLE activity_feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT,        -- 'commit', 'file_change', 'task_move', 'scan_issue', 'review', 'assign'
    actor TEXT,             -- 'antigravity', 'human:rahima', 'system'
    task_id TEXT,           -- related task (if any)
    summary TEXT,           -- "Rahima committed 3 files related to ROE-015"
    details_json TEXT,      -- full event data
    acknowledged BOOLEAN DEFAULT FALSE
);
```

### Activity Detection Engine
```python
class ActivityDetector:
    """Watches the project for activity and logs events."""
    
    def __init__(self, repo_path, ops_dir):
        self.repo_path = repo_path
        self.ops_dir = ops_dir
    
    def detect_git_activity(self):
        """Check for new commits since last check."""
        # git log --since="last check" --format="%H|%an|%s|%ai"
        # For each commit:
        #   - Find which tasks involve the changed files
        #   - Log activity: "Rahima committed changes to ROE-015 files"
        #   - If commit message contains task ID, link them
    
    def detect_file_changes(self):
        """Watch for file modifications in the task system."""
        # Monitor .takvenops/ for file moves (status changes)
        # Trigger: task moved to review/ → start AI review
        # Trigger: task moved to done/ → update sprint progress
    
    def detect_stale_tasks(self):
        """Find tasks that haven't been updated in 3+ days."""
        # Check modified timestamp of in-progress task files
        # If stale: send alert, suggest reassignment
    
    def detect_sprint_risk(self):
        """Check if sprint is on track."""
        # Days remaining vs tasks remaining
        # If behind: create alert, suggest deprioritization
    
    def run_background_scan(self):
        """Periodic codebase scan for new issues."""
        # Run scanner, compare with last scan
        # New issues → auto-create tasks
        # Resolved issues → close corresponding tasks
```

### Git Commit → Task Linking
When a commit message mentions a task ID, automatically:
1. Add the commit to the task's activity log
2. If all acceptance criteria files were changed → suggest marking as review
3. Track work hours (time between first commit and review)

```
# Example: commit message
git commit -m "ROE-015: Add try/except to placements route"
→ TakvenOps links this commit to ROE-015
→ If all files_involved are in the diff → prompt: "Move ROE-015 to review?"
```

---

## Implementation Priority

1. **Activity Feed** — build the database table + API first
2. **AI Review** — most impactful, saves the founder review time
3. **AI Assignment** — needs team skill mapping in config
4. **Git Integration** — nice-to-have, build after core features
5. **Background Scanner** — periodic cron job, build last
