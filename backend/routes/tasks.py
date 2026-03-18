"""Task CRUD routes."""

import re
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from ..database import get_db
from ..models import TaskCreate, TaskUpdate, TaskMove, TaskAssign
from ..services.notifications import notify_task_assigned, notify_status_changed

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def row_to_dict(row):
    """Convert a sqlite3.Row to a dict with parsed JSON fields."""
    d = dict(row)
    for field in ("labels", "files_involved", "acceptance_criteria", "depends_on", "blocks"):
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = []
        else:
            d[field] = []
    return d


def _next_task_id(conn):
    """Generate next task ID like ROE-001."""
    row = conn.execute("SELECT id FROM tasks ORDER BY created_at DESC LIMIT 1").fetchone()
    if row:
        num = int(row["id"].split("-")[1]) + 1
    else:
        num = 1
    return f"ROE-{num:03d}"


def _log_activity(conn, task_id, action, from_status=None, to_status=None, actor="system", details=None):
    conn.execute(
        "INSERT INTO activity_log (task_id, action, from_status, to_status, actor, details) VALUES (?, ?, ?, ?, ?, ?)",
        (task_id, action, from_status, to_status, actor, json.dumps(details) if details else None)
    )


class AutoAssignRequest(BaseModel):
    task_ids: list[str] = []


@router.post("/auto-assign")
def auto_assign(body: AutoAssignRequest):
    from ..services.auto_assign import auto_assign_tasks
    results = auto_assign_tasks(body.task_ids or None)
    return {"assignments": results}


@router.post("/check-escalation")
def check_escalation_endpoint():
    from ..services.escalation import check_escalation
    results = check_escalation()
    return {"escalated": results}


class BulkAction(BaseModel):
    action: str
    task_ids: list[str]
    params: dict = {}


@router.post("/bulk")
def bulk_operations(body: BulkAction):
    if not body.task_ids:
        raise HTTPException(400, "task_ids required")
    conn = get_db()
    results = []
    now = datetime.utcnow().isoformat()
    for tid in body.task_ids:
        task = conn.execute("SELECT * FROM tasks WHERE id = ?", (tid.upper(),)).fetchone()
        if not task:
            results.append({"id": tid, "error": "not found"})
            continue
        if body.action == "assign":
            conn.execute("UPDATE tasks SET assignee = ?, updated_at = ? WHERE id = ?", (body.params.get("assignee", ""), now, tid.upper()))
        elif body.action == "move":
            old = task["status"]
            new_status = body.params.get("status", "backlog")
            conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, tid.upper()))
            _log_activity(conn, tid.upper(), "moved", old, new_status, actor="bulk")
        elif body.action == "add_labels":
            existing = json.loads(task["labels"]) if task["labels"] else []
            merged = list(set(existing + body.params.get("labels", [])))
            conn.execute("UPDATE tasks SET labels = ?, updated_at = ? WHERE id = ?", (json.dumps(merged), now, tid.upper()))
        elif body.action == "delete":
            conn.execute("DELETE FROM tasks WHERE id = ?", (tid.upper(),))
            _log_activity(conn, tid.upper(), "deleted", actor="bulk")
        results.append({"id": tid, "ok": True})
    conn.commit()
    conn.close()
    return {"results": results}


@router.get("/calendar")
def calendar_view(month: str = None):
    conn = get_db()
    if month:
        year, m = month.split("-")
        start = f"{year}-{m}-01"
        end = f"{int(year) + (1 if int(m) == 12 else 0)}-{(int(m) % 12) + 1:02d}-01"
        rows = conn.execute(
            "SELECT * FROM tasks WHERE due_date >= ? AND due_date < ? ORDER BY due_date",
            (start, end)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks WHERE due_date IS NOT NULL ORDER BY due_date").fetchall()
    conn.close()
    grouped = {}
    for r in rows:
        d = row_to_dict(r)
        date_key = d.get("due_date") or "none"
        grouped.setdefault(date_key, []).append(d)
    return {"tasks_by_date": grouped}


@router.get("")
def list_tasks(status: str = None, sprint_id: int = None, assignee: str = None,
               priority: str = None, type: str = None, project_id: str = None):
    conn = get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if project_id:
        query += " AND project_id = ?"
        params.append(project_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    if sprint_id:
        query += " AND sprint_id = ?"
        params.append(sprint_id)
    if assignee:
        query += " AND assignee = ?"
        params.append(assignee)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    if type:
        query += " AND type = ?"
        params.append(type)

    query += " ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 END, created_at DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@router.get("/search")
def search_tasks(q: str = "", project_id: str = None, limit: int = 25):
    """Full-text search across tasks and comments."""
    if not q or len(q.strip()) < 2:
        raise HTTPException(400, "Query must be at least 2 characters")
    conn = get_db()
    term = f"%{q.strip()}%"
    params = [term, term, term]
    base_filter = ""
    if project_id:
        base_filter = " AND t.project_id = ?"
        params.append(project_id)
    params.append(limit)

    rows = conn.execute(
        f"""SELECT DISTINCT t.* FROM tasks t
            LEFT JOIN comments c ON c.task_id = t.id
            WHERE (t.title LIKE ? OR t.body_markdown LIKE ? OR c.body LIKE ?)
            {base_filter}
            ORDER BY t.updated_at DESC
            LIMIT ?""",
        params
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


class DecomposeRequest(BaseModel):
    title: str
    description: str = ""
    type: str = "feature"
    estimated_hours: float = None
    assignee: str = None
    project_id: str = "default"


DECOMPOSITION_RULES = {
    "feature": [
        {"title": "Design & spec", "type": "research", "estimated_hours": 2},
        {"title": "Backend implementation", "type": "feature", "estimated_hours": 4},
        {"title": "Frontend implementation", "type": "feature", "estimated_hours": 4},
        {"title": "Write tests", "type": "tech-debt", "estimated_hours": 2},
        {"title": "Documentation & review", "type": "tech-debt", "estimated_hours": 1},
    ],
    "bug": [
        {"title": "Reproduce & identify root cause", "type": "research", "estimated_hours": 1},
        {"title": "Implement fix", "type": "bug", "estimated_hours": 2},
        {"title": "Add regression test", "type": "tech-debt", "estimated_hours": 1},
        {"title": "Verify fix in staging", "type": "ops", "estimated_hours": 0.5},
    ],
    "research": [
        {"title": "Literature & prior art review", "type": "research", "estimated_hours": 2},
        {"title": "Prototype / proof of concept", "type": "research", "estimated_hours": 4},
        {"title": "Write findings report", "type": "tech-debt", "estimated_hours": 2},
    ],
    "tech-debt": [
        {"title": "Audit current state", "type": "research", "estimated_hours": 1},
        {"title": "Implement refactoring", "type": "tech-debt", "estimated_hours": 4},
        {"title": "Update tests", "type": "tech-debt", "estimated_hours": 2},
    ],
    "ops": [
        {"title": "Infrastructure planning", "type": "research", "estimated_hours": 1},
        {"title": "Implementation", "type": "ops", "estimated_hours": 3},
        {"title": "Testing & validation", "type": "ops", "estimated_hours": 1},
        {"title": "Runbook / documentation", "type": "tech-debt", "estimated_hours": 1},
    ],
}

KEYWORD_ADDITIONS = [
    (r'\b(api|endpoint|rest)\b', {"title": "API contract / OpenAPI spec", "type": "research", "estimated_hours": 1}),
    (r'\b(auth|login|permission|rbac)\b', {"title": "Security review", "type": "research", "estimated_hours": 1}),
    (r'\b(database|migration|schema)\b', {"title": "Database migration script", "type": "ops", "estimated_hours": 1}),
    (r'\b(ui|frontend|component|page)\b', {"title": "Accessibility & responsive check", "type": "tech-debt", "estimated_hours": 0.5}),
    (r'\b(deploy|release|ship|prod)\b', {"title": "Deployment checklist", "type": "ops", "estimated_hours": 0.5}),
]


@router.post("/decompose")
def decompose_epic(body: DecomposeRequest):
    """Rule-based task decomposition: takes an epic, returns suggested subtasks."""
    task_type = body.type if body.type in DECOMPOSITION_RULES else "feature"
    subtasks = [dict(s) for s in DECOMPOSITION_RULES[task_type]]

    combined_text = f"{body.title} {body.description}".lower()
    added_titles = {s["title"] for s in subtasks}
    for pattern, addition in KEYWORD_ADDITIONS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            if addition["title"] not in added_titles:
                subtasks.append(dict(addition))
                added_titles.add(addition["title"])

    if body.estimated_hours and body.estimated_hours > 0:
        total_suggested = sum(s.get("estimated_hours", 0) for s in subtasks)
        if total_suggested > 0:
            scale = body.estimated_hours / total_suggested
            for s in subtasks:
                s["estimated_hours"] = round(s.get("estimated_hours", 0) * scale, 1)

    result = []
    for i, s in enumerate(subtasks):
        result.append({
            "title": f"{body.title} — {s['title']}",
            "type": s["type"],
            "priority": "P2",
            "estimated_hours": s.get("estimated_hours"),
            "assignee": body.assignee,
            "project_id": body.project_id,
            "labels": [],
            "ordinal": i + 1,
        })

    return {
        "epic_title": body.title,
        "epic_type": task_type,
        "suggested_subtasks": result,
        "total_estimated_hours": sum(s.get("estimated_hours") or 0 for s in result),
        "decomposition_method": "rule_based",
    }


@router.get("/{task_id}")
def get_task(task_id: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return row_to_dict(row)


@router.post("")
def create_task(task: TaskCreate):
    conn = get_db()
    task_id = _next_task_id(conn)
    now = datetime.utcnow().isoformat()

    conn.execute(
        """INSERT INTO tasks (id, title, type, priority, status, assignee, sprint_id, created_at, updated_at,
           due_date, estimated_hours, labels, files_involved, acceptance_criteria,
           verification_type, verification_command, verification_ai_check,
           depends_on, blocks, body_markdown, project_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (task_id, task.title, task.type, task.priority, task.status, task.assignee, task.sprint_id,
         now, now, task.due_date, task.estimated_hours,
         json.dumps(task.labels), json.dumps(task.files_involved), json.dumps(task.acceptance_criteria),
         task.verification_type, task.verification_command, task.verification_ai_check,
         json.dumps(task.depends_on), json.dumps(task.blocks), task.body_markdown, task.project_id)
    )
    _log_activity(conn, task_id, "created", to_status=task.status)
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.put("/{task_id}")
def update_task(task_id: str, task: TaskUpdate):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    updates = {}
    for field, value in task.model_dump(exclude_unset=True).items():
        if field in ("labels", "files_involved", "acceptance_criteria", "depends_on", "blocks"):
            updates[field] = json.dumps(value)
        else:
            updates[field] = value

    if not updates:
        conn.close()
        return row_to_dict(existing)

    updates["updated_at"] = datetime.utcnow().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id.upper()]
    conn.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)

    if "status" in updates:
        _log_activity(conn, task_id.upper(), "moved", existing["status"], updates["status"])

    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()
    return row_to_dict(row)


@router.delete("/{task_id}")
def delete_task(task_id: str):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id.upper(),))
    _log_activity(conn, task_id.upper(), "deleted")
    conn.commit()
    conn.close()
    return {"message": f"Task {task_id.upper()} deleted"}


@router.post("/{task_id}/move")
def move_task(task_id: str, body: TaskMove):
    valid = ["backlog", "assigned", "in-progress", "review", "done", "blocked"]
    if body.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Use: {', '.join(valid)}")

    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = existing["status"]
    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (body.status, now, task_id.upper()))
    _log_activity(conn, task_id.upper(), "moved", old_status, body.status)
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()

    notify_status_changed(task_id.upper(), existing["title"], existing["assignee"], "user", body.status)

    return row_to_dict(row)


@router.post("/{task_id}/assign")
def assign_task(task_id: str, body: TaskAssign):
    conn = get_db()
    existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.utcnow().isoformat()
    conn.execute("UPDATE tasks SET assignee = ?, updated_at = ? WHERE id = ?", (body.assignee, now, task_id.upper()))
    _log_activity(conn, task_id.upper(), "assigned", actor=body.assignee, details={"assignee": body.assignee})
    conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    conn.close()

    notify_task_assigned(body.assignee, task_id.upper(), existing["title"], "user")

    return row_to_dict(row)


class NLParseRequest(BaseModel):
    text: str


@router.post("/parse")
def parse_natural_language(body: NLParseRequest):
    """Parse natural language into task fields."""
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Text is required")

    result = {"title": text, "type": "feature", "priority": "P2", "assignee": None, "labels": []}
    confidence = {"title": 1.0, "type": 0.3, "priority": 0.3, "assignee": 0.0, "labels": 0.0}

    # Extract type
    type_patterns = {
        "bug": r'\b(bug|fix|broken|crash|error|issue|defect)\b',
        "feature": r'\b(feature|add|implement|create|build|new)\b',
        "tech-debt": r'\b(refactor|cleanup|debt|optimize|improve|perf)\b',
        "research": r'\b(research|investigate|explore|spike|poc|prototype)\b',
        "ops": r'\b(ops|deploy|ci|cd|infra|pipeline|devops|config)\b',
    }
    for task_type, pattern in type_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            result["type"] = task_type
            confidence["type"] = 0.8
            break

    # Extract priority
    p_match = re.search(r'\b(P[0-3])\b', text, re.IGNORECASE)
    if p_match:
        result["priority"] = p_match.group(1).upper()
        confidence["priority"] = 1.0
    elif re.search(r'\b(critical|urgent|asap|blocker)\b', text, re.IGNORECASE):
        result["priority"] = "P0"
        confidence["priority"] = 0.7
    elif re.search(r'\b(important|high)\b', text, re.IGNORECASE):
        result["priority"] = "P1"
        confidence["priority"] = 0.6

    # Extract assignee — match "assign to X" or "for X"
    conn = get_db()
    members = conn.execute("SELECT id, name FROM team_members").fetchall()
    conn.close()
    member_map = {m["id"].lower(): m["id"] for m in members}
    member_map.update({m["name"].lower(): m["id"] for m in members})

    assign_match = re.search(r'(?:assign(?:ed)?\s+to|for)\s+(\S+)', text, re.IGNORECASE)
    if assign_match:
        candidate = assign_match.group(1).lower().strip('.,;:')
        if candidate in member_map:
            result["assignee"] = member_map[candidate]
            confidence["assignee"] = 0.9
    else:
        for key, member_id in member_map.items():
            if re.search(r'\b' + re.escape(key) + r'\b', text, re.IGNORECASE):
                result["assignee"] = member_id
                confidence["assignee"] = 0.5
                break

    # Clean title — remove parsed tokens
    title = text
    title = re.sub(r'\b(P[0-3])\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'(?:assign(?:ed)?\s+to|for)\s+\S+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip(' .,;:-')
    if title:
        result["title"] = title

    return {"parsed": result, "confidence": confidence}


@router.get("/{task_id}/subtasks")
def get_subtasks(task_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at ASC",
        (task_id.upper(),)
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@router.get("/{task_id}/dependencies")
def get_dependencies(task_id: str):
    conn = get_db()
    task = conn.execute("SELECT depends_on, blocks FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")

    depends_on_ids = json.loads(task["depends_on"]) if task["depends_on"] else []
    blocks_ids = json.loads(task["blocks"]) if task["blocks"] else []

    depends_on = []
    for dep_id in depends_on_ids:
        dep = conn.execute("SELECT id, title, status FROM tasks WHERE id = ?", (dep_id,)).fetchone()
        if dep:
            depends_on.append(dict(dep))

    blocks = []
    for blk_id in blocks_ids:
        blk = conn.execute("SELECT id, title, status FROM tasks WHERE id = ?", (blk_id,)).fetchone()
        if blk:
            blocks.append(dict(blk))

    conn.close()
    return {"depends_on": depends_on, "blocks": blocks}
