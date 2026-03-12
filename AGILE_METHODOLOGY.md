# TakvenOps — Agile Methodology Spec

## Overview

TakvenOps follows **Scrum/Agile** methodology, similar to Azure DevOps Agile process. All work is organized in a hierarchy and managed through sprint ceremonies.

---

## Work Item Hierarchy (Like Azure DevOps)

```
Epic                          "Launch ROE Platform"
 └── Feature                  "Refugee Intake System"
      └── User Story          "As a refugee, I can tell my story via chatbot"
           └── Task           "Build Dari voice transcription endpoint"
           └── Task           "Write tests for chatbot flow"
           └── Bug            "Chatbot crashes on long audio files"
```

### Epic
- **Large initiative** spanning multiple sprints (weeks/months)
- Has a business goal and success metric
- Examples: "Launch MVP", "Employer Portal", "WOTC Automation"

### Feature
- **Deliverable capability** within an epic (1-2 sprints)
- Groups related user stories
- Examples: "Chatbot Intake", "Job Matching", "Resume Generation"

### User Story
- **User-facing requirement** written in standard format
- `As a [role], I want [capability] so that [benefit]`
- Has **acceptance criteria** (testable conditions)
- Estimated in **story points** (1, 2, 3, 5, 8, 13, 21)

### Task
- **Individual work item** within a user story (hours)
- Assigned to one person (human or AI)
- Has concrete deliverables

### Bug
- **Defect** found in existing functionality
- Severity: Critical / High / Medium / Low
- Can exist at any level (standalone or under a story)

---

## Story Points (Fibonacci)

| Points | Meaning | Example |
|--------|---------|---------|
| **1** | Trivial — < 1 hour, obvious fix | Fix a typo, update a label |
| **2** | Small — 1-2 hours, well understood | Add a form field, write a test |
| **3** | Medium — half day, some unknowns | New API endpoint with tests |
| **5** | Large — full day, moderate complexity | New page with backend integration |
| **8** | Very large — 2-3 days, significant work | New feature end-to-end |
| **13** | Epic-sized — should be broken down | Multi-component feature |
| **21** | Too large — must be split | Full system redesign |

### AI Estimation
AI can auto-estimate story points based on:
- Number of files involved
- Cyclomatic complexity of affected code
- Number of acceptance criteria
- Historical data (how long similar tasks took)

---

## Sprint Structure

### Sprint Settings
```yaml
sprint:
  duration: 14 days          # 2-week sprints (configurable: 1, 2, 3, 4 weeks)
  capacity_per_person: 20    # story points per person per sprint
  ai_capacity: 40            # AI agents can handle more
  ceremonies:
    planning: "Monday 10:00 AM"
    standup: "Daily 9:00 AM"
    review: "Friday 3:00 PM"     # last Friday of sprint
    retrospective: "Friday 4:00 PM"
```

### Sprint Board Columns
```
Product Backlog → Sprint Backlog → Active → Review → Testing → Done
```

| Column | Who Moves Here | Meaning |
|--------|---------------|---------|
| **Product Backlog** | Product Owner (you) | Prioritized list of all work |
| **Sprint Backlog** | Team (at planning) | Committed work for this sprint |
| **Active** | Assignee | Currently being worked on |
| **Review** | Assignee (when done) | Code review or peer review |
| **Testing** | Reviewer (when approved) | QA verification |
| **Done** | Tester (when verified) | Meets Definition of Done |

---

## Sprint Ceremonies (Auto-Facilitated by AI)

### 1. Sprint Planning (Start of Sprint)

AI auto-generates a planning agenda:
```
# Sprint 2 Planning — March 25, 2026

## Sprint Goal
"Complete employer onboarding and first 30 real matches"

## Velocity
- Last sprint: 42 points completed (team) + 18 points (AI) = 60 total
- This sprint capacity: 64 points

## Suggested Sprint Backlog (from prioritized backlog)
| Story | Points | Suggested Assignee | Reason |
|-------|--------|-------------------|--------|
| US-012: Employer job upload | 5 | Rahima | Backend skill match |
| US-013: Match results page | 8 | Dev 3 | Frontend expertise |
| US-014: WOTC auto-screen | 3 | Antigravity | AI can automate |
| US-015: Profile photo upload | 2 | Claude Code | Simple feature |
| BUG-003: Chatbot timeout | 3 | Antigravity | Knows the codebase |
| Total: 21 points |

## Carry-over from Sprint 1
- US-008: Resume PDF generation (5 pts) — 60% done
```

### 2. Daily Standup (Auto-Generated)

AI creates this every morning from task activity:
```
# Daily Standup — March 26, 2026

## 👤 Rahima
- Yesterday: Completed employer API endpoint (US-012, Task 1)
- Today: Working on employer dashboard view (US-012, Task 2)
- Blockers: None

## 👤 Dev 3
- Yesterday: Started match results page wireframe (US-013)
- Today: Continuing front-end implementation
- Blockers: Needs API endpoint for match data (depends on US-012)

## 🤖 Antigravity
- Yesterday: Fixed chatbot timeout bug (BUG-003 ✅), WOTC screening (US-014, 80%)
- Today: Completing WOTC auto-screen, starting profile photo upload
- Blockers: None

## 📊 Sprint Burndown
Day 2 of 14 | 8/64 points done (12.5%) | On track ✅
```

### 3. Sprint Review (End of Sprint)

AI auto-generates what was delivered:
```
# Sprint 1 Review — March 24, 2026

## Delivered
- ✅ US-001: Chatbot intake (8 pts)
- ✅ US-003: Profile dashboard (5 pts)
- ✅ US-005: Job listing page (5 pts)
- ✅ 4 bugs fixed (8 pts)

## Not Completed
- 🔄 US-008: Resume PDF generation (5 pts) — 60% done, carry to Sprint 2

## Metrics
- Velocity: 26 points (team) + 16 points (AI) = 42 total
- Bug fix rate: 4/5 (80%)
- AI contribution: 38% of total work

## Demo Notes
[Links to deployed features for stakeholder demonstration]
```

### 4. Sprint Retrospective

AI suggests discussion topics based on data:
```
# Sprint 1 Retrospective

## 🟢 What Went Well
- AI completed 16 story points autonomously
- Zero P0 bugs in production
- Team communication was strong (45 comments on tasks)

## 🔴 What Didn't Go Well
- US-008 carried over — estimation was off (estimated 5, actually 8+)
- 3 tasks were blocked for > 2 days (waiting on external data)

## 💡 AI-Suggested Improvements
- Increase buffer for tasks involving external dependencies
- Add "waiting on external" as a blocked sub-status
- Consider splitting stories > 5 points before sprint commitment

## 📊 Data
- Average cycle time: 2.3 days
- Longest blocked: US-007 (4 days, waiting on BLS data)
- Most productive day: Wednesday (12 points completed)
```

---

## Backlog Management

### Product Backlog
- **Ordered by priority** (most important first)
- **Groomed weekly** — AI suggests items that need refinement
- **Epics at top** → broken into features → broken into stories
- **Ready indicator** — story is "ready" when it has:
  - Clear description
  - Acceptance criteria
  - Story point estimate
  - No unresolved questions

### Backlog Grooming (AI-Assisted)
AI flags stories that aren't ready:
```
⚠️ US-020 "Integrate with employer ATS" — needs refinement:
  - No acceptance criteria defined
  - Story too large (13 pts) — consider splitting
  - Missing: which ATS systems to support?
  - Suggestion: Split into "ATS API research" (3 pts) + "ATS integration" (8 pts)
```

---

## Definition of Done (DoD)

A task/story is "Done" when ALL of these are true:

### For Non-Technical Tasks
- [ ] Work is complete as described
- [ ] Reviewed by at least one team member
- [ ] Any documents/files are uploaded and linked
- [ ] Time tracked

### For Technical Tasks (Developer Mode)
- [ ] All acceptance criteria met
- [ ] Code reviewed (by AI or human)
- [ ] Tests pass
- [ ] No new bugs introduced
- [ ] Documentation updated (if applicable)

---

## Roles

| Role | Responsibilities | In TakvenOps |
|------|-----------------|--------------|
| **Product Owner** | Prioritize backlog, define stories, accept/reject | You (Hasib) |
| **Scrum Master** | Facilitate ceremonies, remove blockers | AI (automated) |
| **Development Team** | Execute work, estimate, self-organize | Rahima, Dev 3, Dev 4 |
| **AI Agents** | Execute tasks, review code, generate reports | Antigravity, Claude Code |

> **Key insight**: AI replaces the Scrum Master role. It auto-generates standups, facilitates planning with data, runs retrospectives, and removes blockers by flagging them early.

---

## Database Additions

```sql
-- Epics
CREATE TABLE epics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',    -- active, completed, cancelled
    start_date DATE,
    target_date DATE,
    success_metric TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Features (child of Epic)
CREATE TABLE features (
    id TEXT PRIMARY KEY,
    epic_id TEXT REFERENCES epics(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'new',
    target_sprint INTEGER
);

-- User Stories (child of Feature)
-- Extends the existing 'tasks' table with:
ALTER TABLE tasks ADD COLUMN epic_id TEXT REFERENCES epics(id);
ALTER TABLE tasks ADD COLUMN feature_id TEXT REFERENCES features(id);
ALTER TABLE tasks ADD COLUMN parent_id TEXT REFERENCES tasks(id);  -- for subtasks
ALTER TABLE tasks ADD COLUMN story_points INTEGER;
ALTER TABLE tasks ADD COLUMN work_item_type TEXT DEFAULT 'task';
    -- 'epic', 'feature', 'user_story', 'task', 'bug'
ALTER TABLE tasks ADD COLUMN time_spent_minutes INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN severity TEXT;  -- for bugs: critical, high, medium, low

-- Sprint ceremonies log
CREATE TABLE ceremonies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_id INTEGER REFERENCES sprints(id),
    type TEXT,         -- planning, standup, review, retrospective
    date TIMESTAMP,
    generated_report TEXT,  -- markdown content
    attendees TEXT          -- JSON array
);
```
