# TakvenOps — UI Design Specification

## Design Principles

1. **Dark mode by default** — developers work in dark mode
2. **Information dense** — show as much data as possible without clutter
3. **Fast** — everything loads instantly, no spinners
4. **Keyboard-first** — all actions have keyboard shortcuts
5. **Inspired by Linear** — clean, minimal, fast

## Color Palette

```css
/* Dark theme */
--bg-primary: #0d1117;         /* GitHub dark */
--bg-secondary: #161b22;
--bg-tertiary: #21262d;
--bg-card: #1c2128;
--border: #30363d;

--text-primary: #e6edf3;
--text-secondary: #8b949e;
--text-muted: #484f58;

/* Priority colors */
--p0-color: #f85149;           /* Red — critical */
--p1-color: #d29922;           /* Orange — high */
--p2-color: #58a6ff;           /* Blue — medium */
--p3-color: #484f58;           /* Gray — low */

/* Status colors */
--status-backlog: #484f58;
--status-progress: #d29922;
--status-review: #58a6ff;
--status-done: #3fb950;
--status-blocked: #f85149;

/* Type colors */
--type-feature: #a371f7;       /* Purple */
--type-bug: #f85149;           /* Red */
--type-tech-debt: #d29922;     /* Yellow */
--type-research: #58a6ff;      /* Blue */
--type-ops: #8b949e;           /* Gray */

/* Accent */
--accent: #58a6ff;
--accent-hover: #79c0ff;

/* AI Agent indicator */
--ai-glow: rgba(88, 166, 255, 0.15);
--ai-border: #58a6ff;
```

## Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Logo] TakvenOps     Sprint 1 ▾   [Search ⌘K]  [👤]   │
├────────┬────────────────────────────────────────────────┤
│        │                                                │
│ Board  │  ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│ List   │  │ Backlog  │ │Progress  │ │ Review   │      │
│ ──────── │  │          │ │          │ │          │      │
│ Standup │  │ [Card]   │ │ [Card]   │ │ [Card]   │      │
│ Scanner │  │ [Card]   │ │ [Card]   │ │          │      │
│ Metrics │  │ [Card]   │ │          │ │          │      │
│ ──────── │  │ [+ Add]  │ │          │ │          │      │
│ Settings│  └──────────┘ └──────────┘ └──────────┘      │
│        │                                                │
└────────┴────────────────────────────────────────────────┘
```

## Pages

### 1. Board Page (Default)
- **Kanban columns**: Backlog, In Progress, Review, Done, Blocked
- **Drag-and-drop** to move tasks between columns
- **Task cards** show: ID, priority badge, title, assignee avatar, labels
- **AI tasks get a ✨ glow effect** (subtle blue border) to distinguish from human tasks
- **Quick actions**: Click card → open detail panel on right side
- **Top bar**: Sprint selector, filter by type/priority/assignee, search

### 2. Task Card Component
```
┌──────────────────────────────┐
│ P1  ROE-042                  │
│ Fix retention model false    │
│ positives above 90%         │
│                              │
│ [ml] [retention] [production]│
│                              │
│ 🤖 antigravity   📅 Mar 15  │
└──────────────────────────────┘
```
- Priority badge (colored dot or tag)
- Task ID (clickable)
- Title (2 lines max)
- Labels (small colored chips)
- Assignee (avatar or 🤖 for AI)
- Due date if set

### 3. Task Detail Panel
Opens as a right-side panel or modal:
- Full title (editable)
- Status dropdown, priority dropdown, assignee dropdown
- Type selector
- Sprint picker
- Due date picker
- Labels (multi-select)
- **Acceptance Criteria** — checklist style
- **Files Involved** — clickable file paths
- **Dependencies** — which tasks block/are blocked by this
- **Verification** — command, type, AI check description
- **Markdown body** — rich editor with code blocks
- **Completion Notes** — shown when AI fills them in
- **Activity log** — timeline of all changes

### 4. List View Page
Table with sortable columns:
| ID | Priority | Title | Type | Status | Assignee | Sprint | Due | Est. |
- Click column header to sort
- Multi-select rows → bulk assign, bulk move
- Quick inline editing

### 5. Standup Page
- Today's auto-generated standup report
- History of past standups (calendar view)
- Manual standup entry option
- Each section: ✅ Completed, 🔄 In Progress, 🚫 Blocked, 📊 Sprint %

### 6. Scanner Page
- "Run Scan" button
- Results grouped by type (TODOs, Missing Tests, Error Handling)
- Each result shows file, line, description
- "Create Task" button next to each result
- Bulk "Create All" to generate tasks from all findings
- History of past scans with trend chart

### 7. Analytics Page
- **Velocity Chart** — bar chart, tasks/sprint, broken by assignee
- **Burndown** — line chart, sprint progress
- **AI vs Human** — pie chart showing % of work done by AI
- **Cycle Time** — average days from assigned → done
- **Issue Trend** — line chart from scanner (TODOs over time)

### 8. Settings Page
- **Team** — add/edit/remove members (humans + AI agents)
- **Sprint** — configure sprint duration, current sprint
- **Repository** — connect a local repo path for scanning
- **Notifications** — Slack/Discord webhook URLs
- **AI Rules** — max concurrent tasks, auto-assign threshold, require review

## Keyboard Shortcuts

```
⌘K         — Search/command palette
N          — New task
B          — Board view
L          — List view
S          — Standup
1-5        — Move selected task (1=backlog, 2=progress, 3=review, 4=done, 5=blocked)
A          — Assign selected task
P          — Change priority
Esc        — Close panel/modal
↑/↓        — Navigate tasks
Enter      — Open task detail
```

## Responsive Design

- **Desktop** (1200px+): Full sidebar + board + detail panel
- **Tablet** (768-1199px): Collapsible sidebar + board
- **Mobile** (< 768px): Bottom nav + single column list view

## Animations

- Card drag: smooth 200ms transform
- Column drop: subtle spring animation
- Panel slide: 250ms ease-out from right
- Status change: brief color pulse on card
- AI task completion: ✨ sparkle animation on card
