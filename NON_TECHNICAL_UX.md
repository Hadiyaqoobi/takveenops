# TakvenOps — Non-Technical User Experience Spec

## Principle

TakvenOps must work for **everyone on the team** — not just developers. A caseworker collecting refugee profiles, a partner manager contacting employers, and an operations lead tracking WOTC filings should all find TakvenOps intuitive without seeing a single line of code.

The developer/AI features (codebase scanner, verification engine, git integration) stay available but are **hidden behind a "Developer Mode" toggle**. By default, the tool looks and feels like Jira, Asana, or Monday.com.

---

## Two Modes

### 🟢 Standard Mode (Default — for everyone)
- Clean project board with cards
- Simple task creation via form (no YAML, no markdown frontmatter)
- Drag-and-drop Kanban
- Calendar view for deadlines
- Time tracking
- Comments and @mentions on tasks
- File attachments (documents, screenshots)
- Dashboard with progress charts
- Notifications

### 🔵 Developer Mode (Toggle on — for engineers + AI)
- Everything in Standard Mode, plus:
- Codebase scanner
- Git integration
- AI verification engine
- File-based `.takvenops/` sync
- Acceptance criteria with verification commands
- Terminal/code references

---

## Pages for Non-Technical Users

### 1. 🏠 My Dashboard (Home Page)
```
┌─────────────────────────────────────────────────────┐
│  Good morning, Rahima 👋                            │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 3 Tasks  │ │ 1 Due    │ │ 2 New    │           │
│  │ Assigned │ │ Today    │ │ Comments │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│                                                     │
│  📋 My Tasks                                       │
│  ┌─────────────────────────────────────────┐       │
│  │ ● Collect 10 profiles this week    P1   │       │
│  │ ● Contact Boston Marriott         P2   │       │
│  │ ● Review WOTC filing for Ahmad    P2   │       │
│  └─────────────────────────────────────────┘       │
│                                                     │
│  📊 Team Progress                                  │
│  Sprint 1: ████████░░ 78%                          │
│                                                     │
│  🕐 Recent Activity                                │
│  • Hasib assigned you "Contact Boston Marriott"     │
│  • AI reviewed ROE-015 — ✅ Approved                │
│  • Rahima completed "Upload 5 profiles" — 2h ago   │
└─────────────────────────────────────────────────────┘
```

### 2. 📋 Board View (Kanban — like Trello/Jira)
- **Columns**: To Do, In Progress, Review, Done
- **Simplified labels**: No "P0/P1" jargon — use ❗ Urgent, 🔶 Important, 📌 Normal
- **Avatars** for assignees (real photos, not IDs)
- **Due date badges** (red if overdue, yellow if due today)
- **Drag-and-drop** to move cards between columns
- **"+ Add Task" button** at the top of each column

### 3. 📝 Task Creation Form (No Code Required)
Simple form, not markdown:
```
┌─────────────────────────────────────────────┐
│  Create New Task                            │
│                                             │
│  Title: [________________________]          │
│                                             │
│  Description:                               │
│  [Rich text editor with bold, bullets,      │
│   image upload, @mentions]                  │
│                                             │
│  Category:  [Feature ▾]                     │
│  Priority:  [🔶 Important ▾]               │
│  Assign to: [Rahima Khan ▾]                 │
│  Due date:  [📅 Mar 25, 2026]              │
│  Sprint:    [Sprint 1 ▾]                    │
│  Labels:    [+ Add label]                   │
│                                             │
│  📎 Attach files                            │
│                                             │
│  [Create Task]  [Cancel]                    │
└─────────────────────────────────────────────┘
```

### 4. 📅 Calendar View
- Month/week/day views
- Tasks shown on their due dates
- Color-coded by priority
- Drag tasks to reschedule
- See team member availability

### 5. 💬 Task Comments & Discussion
Each task has a conversation thread:
```
┌─────────────────────────────────────────────┐
│  ROE-012: Contact Boston Marriott           │
│                                             │
│  👤 Hasib — 2h ago                          │
│  "Can you reach out to their HR director?   │
│   Here's the contact: john@marriott.com"    │
│                                             │
│  👤 Rahima — 1h ago                         │
│  "Called them, they want 15 housekeepers.   │
│   Scheduling a meeting for Thursday."       │
│     📎 marriott_jd.pdf                      │
│                                             │
│  🤖 Antigravity — 30m ago                   │
│  "I parsed the JD. 15 positions match 8     │
│   profiles in our system. Shall I generate  │
│   the match report?"                        │
│                                             │
│  [Type a comment...          ] [Send]       │
└─────────────────────────────────────────────┘
```

### 6. ⏱️ Time Tracking
- Start/stop timer on any task
- Manual time entry ("I spent 2h on this")
- Weekly timesheet view
- Total hours by team member for reporting

### 7. 📊 Reports Page (Non-Technical Analytics)
Instead of "velocity" and "burndown" (developer jargon), show:
- **Team Progress**: "12 of 20 tasks done this sprint (60%)"
- **Who's Doing What**: Bar chart of tasks per person
- **Overdue Tasks**: List of tasks past their deadline
- **Completed This Week**: Visual celebration of finished work
- **AI Contribution**: "AI completed 5 tasks and reviewed 8 this week"

### 8. 👥 People Page
- Team directory with photos, roles, timezones
- See each person's current tasks
- Workload heatmap (who's overloaded, who has capacity)

---

## UI Polish Requirements

### Typography
- **Font**: Inter (same as ROE platform)
- **Headings**: 600 weight, -0.02em tracking
- **Body**: 400 weight, 15px
- **Captions**: 13px, muted color

### Cards
- **Rounded corners**: 12px
- **Subtle shadow**: `0 1px 3px rgba(0,0,0,0.12)`
- **Hover**: lift effect with `transform: translateY(-1px)`
- **Priority indicator**: Left border color (red/orange/blue/gray)

### Animations
- **Page transitions**: 250ms crossfade
- **Card drag**: Smooth with opacity:0.9 while dragging
- **Toast notifications**: Slide in from top-right, auto-dismiss 5s
- **Task completion**: Confetti burst 🎉 (subtle, not obnoxious)
- **Loading states**: Skeleton screens, never spinners

### Accessibility
- **Keyboard navigation** for all actions
- **ARIA labels** on interactive elements
- **Color contrast** AA minimum
- **Screen reader** support for task status changes
- **Light mode option** for users who prefer it

### Mobile Responsive
- **< 768px**: Bottom tab navigation, single-column card list
- **768-1024px**: Simplified sidebar, 2-column board
- **1024px+**: Full sidebar + board + detail panel

---

## Notifications System

### In-App Notifications
- Bell icon in header with unread count
- Dropdown shows recent notifications
- Click to jump to related task

### Types
- 📌 **Assigned to you** — "Hasib assigned you ROE-012"
- 💬 **New comment** — "Rahima commented on ROE-012"
- ✅ **Task completed** — "Antigravity completed ROE-015"
- 🤖 **AI review** — "AI review ready for ROE-012"
- ⚠️ **Overdue** — "ROE-010 is 2 days overdue"
- 📊 **Sprint update** — "Sprint 1 is 80% complete"

### External (Optional)
- Email digest (daily summary)
- Slack/Discord webhook
- Browser push notifications

---

## Search & Filters

### Global Search (⌘K / Ctrl+K)
- Search tasks by title, description, comments
- Search team members
- Search labels
- Recent searches

### Board Filters
- By assignee (show only my tasks)
- By priority (show only urgent)
- By type (show only bugs)
- By label
- By due date (overdue, due this week, no date)
- Saved filter presets

---

## Onboarding for New Team Members

When a new user joins:
1. **Welcome screen** with 4-step tour
2. **"Create your first task"** guided walkthrough
3. **Pre-filled board** with sample tasks
4. **Tooltip hints** on first use of each feature
5. **Help button** → in-app help center
