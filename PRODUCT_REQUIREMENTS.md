# TakvenOps — Product Requirements Document

## Vision

The first project management tool where AI coding agents are autonomous team members — not assistants, but contributors that read tasks, execute work, verify results, and report back.

**Target user**: Solo founders and small teams (2-5 people) who use AI coding tools (Claude Code, Cursor, Copilot, Antigravity) daily and want to delegate real work to AI, not just get suggestions.

---

## Problem Statement

Existing PM tools (Jira, Linear, Asana, Azure DevOps) treat AI as a suggestion engine:
- AI can summarize tasks but can't execute them
- AI can't see the task board or pick up work
- No way for AI to verify its own work against acceptance criteria
- No codebase awareness — tasks aren't linked to actual code

**Result**: Solo founders spend 40% of time on project management overhead instead of building.

---

## Market Research

| Tool | AI Features | What's Missing |
|------|------------|----------------|
| **Linear** ($82M raised) | Auto-triage, backlog generation | No AI agent execution loop |
| **Asana AI Studio** | Automated workflows | No codebase awareness |
| **ClickUp** | Natural language queries | No task execution by AI |
| **Motion** | Calendar scheduling | No developer focus |
| **GitHub Projects** | Copilot suggestions | No autonomous task completion |
| **SelfManager.ai** | Project plan generation | No code integration |

**Gap**: No tool closes the loop — AI reads task → does work → verifies → reports back.

---

## Core Features

### 1. 📋 Task Board (Like Jira)
- **Kanban board** with columns: Backlog, In Progress, Review, Done, Blocked
- **List view** with sortable columns (priority, assignee, due date, type)
- **Sprint planning** — group tasks into time-boxed sprints
- **Task types**: Feature, Bug, Tech Debt, Research, Ops
- **Priorities**: P0 (critical), P1 (high), P2 (medium), P3 (low)
- **Labels/tags** for categorization
- **Dependencies** — task A blocks task B
- **Subtasks** — break large tasks into steps

### 2. 🤖 AI Agent Integration (Revolutionary Feature)
- **AI as assignee** — tasks can be assigned to `antigravity` or `claude-code`
- **AI reads tasks** — structured frontmatter that AI agents parse natively
- **AI executes tasks** — agent reads acceptance criteria, edits files, runs tests
- **AI verifies** — runs verification commands, checks diff against criteria
- **AI reports** — adds completion notes to the task with what changed
- **AI creates tasks** — codebase scan detects issues and auto-creates tasks
- **Bidirectional sync** — file system ↔ web dashboard ↔ AI agent

### 3. 🔍 Codebase Scanner
Analyzes any connected repository and auto-generates tasks:
- **TODO/FIXME/HACK** comments → bug tasks
- **Missing test coverage** → tech-debt tasks
- **High-complexity functions** (cyclomatic > 10) → refactor tasks
- **API routes without error handling** → bug tasks
- **Outdated dependencies** → tech-debt tasks
- **Security issues** (hardcoded secrets, SQL injection patterns) → P0 bugs
- **Dead code** → cleanup tasks

### 4. 📊 Auto-Generated Standups
Daily report generated automatically from task state:
- What was completed yesterday
- What's in progress today
- What's blocked (with reasons)
- Auto-detected new issues from codebase scan
- Sprint progress percentage + burndown

### 5. ✅ Verification Engine
When a task is marked complete, automatically:
1. Run the verification command (e.g., `pytest tests/test_foo.py`)
2. AI-review the diff against acceptance criteria
3. Check for side effects (did anything else break?)
4. Pass → move to "Review" for human approval
5. Fail → move back to "In Progress" with feedback

### 6. 📈 Analytics Dashboard
- **Velocity** — tasks completed per sprint (by assignee, including AI)
- **AI vs Human** ratio — how much work AI is doing
- **Burndown chart** — sprint progress over time
- **Cycle time** — average time from "assigned" to "done"
- **Blocker heatmap** — what causes the most blocks
- **Code quality trends** — TODO count, test coverage over time

### 7. 🔔 Notifications
- Slack/Discord webhooks for task updates
- Daily standup email digest
- Alert when AI verification fails 3+ times
- Alert when sprint is behind schedule

### 8. 👥 Team Management
- **Team members** — humans and AI agents
- **Roles**: Founder, Engineer, AI Agent, Reviewer
- **Capacity tracking** — who has bandwidth
- **AI agent rules**: max concurrent tasks, require human review, auto-assign threshold

---

## User Stories

### Solo Founder
1. I open TakvenOps and see my sprint board with 20 tasks
2. I assign 5 tasks to Antigravity (Claude Code)
3. I go to sleep — AI works on 2 tasks overnight
4. Next morning: 2 tasks in "Review" with completion notes
5. I review, approve, and they move to "Done"
6. The standup report is auto-generated showing progress

### Team Member (Remote)
1. I log in from Canada and see tasks assigned to me
2. I pick up a task, move it to "In Progress"
3. I complete it, run verification, and move to "Review"
4. The founder reviews and closes the task
5. Sprint analytics show my contribution

### AI Agent (Antigravity/Claude Code)
1. I read `.takvenops/ai-instructions.md` for system rules
2. I check `.takvenops/backlog/` for assigned tasks
3. I read task frontmatter: acceptance criteria, files, verification
4. I edit code, write tests, run verification
5. I move task to `review/` with completion notes
6. I never move tasks to `done/` — only humans can close

---

## Task Data Model

```yaml
---
id: ROE-042                  # Unique identifier
title: Fix retention model   # Short title
type: bug                    # feature | bug | tech-debt | research | ops
priority: P1                 # P0 | P1 | P2 | P3
status: backlog              # backlog | assigned | in-progress | review | done | blocked
assignee: antigravity        # team member ID
created: 2026-03-11          # ISO date
due: 2026-03-15              # optional deadline
sprint: 1                    # sprint number
labels: [ml, retention]      # tags
estimated_hours: 4           # effort estimate
actual_hours:                # filled when done
files_involved:              # files to edit
  - api/services/retention_service.py
acceptance_criteria:         # measurable outcomes
  - False positive rate below 15%
  - All tests pass
verification:
  type: automated
  command: "pytest tests/test_retention.py -v"
  ai_check: "Review diff and confirm logic fix"
depends_on: [ROE-039]       # blocking dependencies
blocks: [ROE-045]           # tasks this unblocks
---

## Context
Markdown body with background, technical details, screenshots, etc.

## Completion Notes
[AI fills this in when done]
- Changed X in file Y
- Test results: 12/12 passing
- Side effects: None detected
```

---

## Non-Functional Requirements

- **No external API keys needed** — works locally with file system
- **Zero-config** — drop `.takvenops/` into any repo and it works
- **Fast** — board loads in < 500ms even with 1000 tasks
- **Offline capable** — file system works without internet
- **Git-friendly** — task changes show in git diffs alongside code changes
- **Cross-platform** — Windows, Mac, Linux
