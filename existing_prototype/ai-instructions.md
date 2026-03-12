# TakvenOps — AI Agent Instructions

> This file is read by AI coding agents (Antigravity, Claude Code) to understand
> how to interact with the TakvenOps task management system.

## How Tasks Work

Tasks are **markdown files** in the `.takvenops/` directory, organized by status:

```
.takvenops/
├── backlog/        ← Tasks waiting to be worked on
├── in-progress/    ← Tasks currently being worked on
├── review/         ← Tasks waiting for human review
├── done/           ← Completed tasks
└── blocked/        ← Tasks blocked by dependencies
```

Each task file has **YAML frontmatter** (metadata) and **markdown body** (context).

## Your Workflow as an AI Agent

### 1. Check for assigned tasks
Look in `.takvenops/backlog/` and `.takvenops/in-progress/` for tasks where
`assignee: antigravity` (or `assignee: claude-code`).

### 2. Read the task
- Read the YAML frontmatter for acceptance criteria, files involved, and verification steps
- Read the markdown body for context and background

### 3. Do the work
- Edit the files listed in `files_involved`
- Follow the acceptance criteria exactly
- Write tests if required

### 4. Verify your work
- Run the command in `verification.command` (typically pytest)
- If `verification.ai_check` exists, self-review your diff against it
- If verification passes, move the task file to `.takvenops/review/`
- If it fails, stay in `in-progress/` and note what failed

### 5. Update the task file
Add a `## Completion Notes` section with:
- What you changed (with file paths)
- Test results
- Any side effects or things the human should know

### 6. Move the file
```
# Move from backlog → in-progress (when starting)
Move .takvenops/backlog/ROE-XXX.md → .takvenops/in-progress/ROE-XXX.md

# Move from in-progress → review (when done)
Move .takvenops/in-progress/ROE-XXX.md → .takvenops/review/ROE-XXX.md
```

## Rules
1. **Never move tasks to `done/`** — only humans can close tasks
2. **Never delete task files** — move them between directories
3. **Always run verification** before moving to `review/`
4. **Update `status:` in frontmatter** when you move a file
5. **Don't work on tasks assigned to others** unless reassigned
6. **Max 2 tasks at a time** — finish before picking up new ones

## Creating New Tasks
When you discover bugs, missing tests, or improvements during your work:
1. Copy a template from `.takvenops/templates/`
2. Fill in all frontmatter fields
3. Increment `next_id` in `config.yaml`
4. Save to `.takvenops/backlog/`

## Quick Reference — Task Frontmatter
```yaml
---
id: ROE-XXX
title: Short descriptive title
type: bug | feature | tech-debt | research | ops
priority: P0 | P1 | P2 | P3
status: backlog | assigned | in-progress | review | done | blocked
assignee: antigravity | claude-code | human:you | human:rahima
created: YYYY-MM-DD
due: YYYY-MM-DD (optional)
sprint: 1
labels: [relevant, labels]
estimated_hours: N
files_involved:
  - path/to/file.py
acceptance_criteria:
  - Specific measurable outcome 1
  - Specific measurable outcome 2
verification:
  type: automated | manual | ai-review
  command: "pytest tests/specific_test.py -v"
  ai_check: "Description of what to verify in the diff"
depends_on: []        # list of task IDs this depends on
blocks: []            # list of task IDs this blocks
---
```
