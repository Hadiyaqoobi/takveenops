"""File system ↔ Database sync service."""

import json
import re
from pathlib import Path
from datetime import date
from ..database import get_db


STATUSES = ["backlog", "in-progress", "review", "done", "blocked"]


def parse_frontmatter(filepath: Path) -> dict:
    """Parse YAML-like frontmatter from a task markdown file."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}

    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()

    meta = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("  - ") and current_key:
            val = line.strip("- ").strip()
            if current_list is None:
                current_list = []
            current_list.append(val)
            meta[current_key] = current_list
            continue

        m = re.match(r"^(\w[\w_]*)\s*:\s*\[(.+)\]\s*$", line)
        if m:
            current_key = m.group(1)
            current_list = None
            meta[current_key] = [v.strip().strip("'\"") for v in m.group(2).split(",")]
            continue

        m = re.match(r"^(\w[\w_]*)\s*:\s*(.*)", line)
        if m:
            current_key = m.group(1)
            current_list = None
            val = m.group(2).strip().strip('"').strip("'")
            if val == "":
                meta[current_key] = None
            elif val.lower() in ("true", "false"):
                meta[current_key] = val.lower() == "true"
            elif val.isdigit():
                meta[current_key] = int(val)
            else:
                meta[current_key] = val
            continue

    meta["_body"] = body
    return meta


def sync_from_filesystem(ops_dir: str):
    """Read all .takvenops/ files and populate the database."""
    ops_path = Path(ops_dir)
    if not ops_path.exists():
        return {"synced": 0, "errors": []}

    conn = get_db()
    synced = 0
    errors = []

    for status in STATUSES:
        status_dir = ops_path / status
        if not status_dir.exists():
            continue

        for f in status_dir.glob("*.md"):
            try:
                meta = parse_frontmatter(f)
                task_id = meta.get("id")
                if not task_id:
                    continue

                labels = meta.get("labels", [])
                if isinstance(labels, str):
                    labels = [labels]

                files_involved = meta.get("files_involved", [])
                if isinstance(files_involved, str):
                    files_involved = [files_involved]

                acceptance = meta.get("acceptance_criteria", [])
                if isinstance(acceptance, str):
                    acceptance = [acceptance]

                depends = meta.get("depends_on", [])
                if isinstance(depends, str):
                    depends = [depends]

                blocks = meta.get("blocks", [])
                if isinstance(blocks, str):
                    blocks = [blocks]

                conn.execute("""
                    INSERT OR REPLACE INTO tasks
                    (id, title, type, priority, status, assignee, sprint_id, due_date,
                     estimated_hours, labels, files_involved, acceptance_criteria,
                     depends_on, blocks, body_markdown, file_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    meta.get("title", "Untitled"),
                    meta.get("type", "feature"),
                    meta.get("priority", "P2"),
                    status,
                    meta.get("assignee"),
                    meta.get("sprint"),
                    meta.get("due"),
                    meta.get("estimated_hours"),
                    json.dumps(labels),
                    json.dumps(files_involved),
                    json.dumps(acceptance),
                    json.dumps(depends),
                    json.dumps(blocks),
                    meta.get("_body", ""),
                    str(f),
                ))
                synced += 1
            except Exception as e:
                errors.append({"file": str(f), "error": str(e)})

    conn.commit()
    conn.close()
    return {"synced": synced, "errors": errors}


def task_to_markdown(task: dict) -> str:
    """Convert a task dict to frontmatter markdown."""
    lines = ["---"]
    lines.append(f"id: {task['id']}")
    lines.append(f"title: {task['title']}")
    lines.append(f"type: {task.get('type', 'feature')}")
    lines.append(f"priority: {task.get('priority', 'P2')}")
    lines.append(f"status: {task.get('status', 'backlog')}")
    lines.append(f"assignee: {task.get('assignee') or ''}")

    if task.get("sprint_id"):
        lines.append(f"sprint: {task['sprint_id']}")
    if task.get("due_date"):
        lines.append(f"due: {task['due_date']}")
    if task.get("estimated_hours"):
        lines.append(f"estimated_hours: {task['estimated_hours']}")

    labels = task.get("labels", [])
    if isinstance(labels, str):
        labels = json.loads(labels)
    if labels:
        lines.append(f"labels: [{', '.join(labels)}]")

    files = task.get("files_involved", [])
    if isinstance(files, str):
        files = json.loads(files)
    if files:
        lines.append("files_involved:")
        for f in files:
            lines.append(f"  - {f}")

    criteria = task.get("acceptance_criteria", [])
    if isinstance(criteria, str):
        criteria = json.loads(criteria)
    if criteria:
        lines.append("acceptance_criteria:")
        for c in criteria:
            lines.append(f"  - {c}")

    lines.append("---")
    lines.append("")

    if task.get("body_markdown"):
        lines.append(task["body_markdown"])

    return "\n".join(lines)
