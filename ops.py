#!/usr/bin/env python3
"""TakvenOps CLI — Manage tasks from the command line.

Used by AI agents (Claude Code, Antigravity) and humans to interact
with the TakvenOps board via the API.

Usage:
  python ops.py tasks                          List all tasks
  python ops.py tasks --status in-progress     List tasks by status
  python ops.py tasks --assignee antigravity   List tasks by assignee
  python ops.py my-tasks <name>                Show tasks assigned to <name>
  python ops.py create "Fix login bug" --type bug --priority P1 --assignee admin
  python ops.py assign <task-id> <assignee>    Assign a task
  python ops.py move <task-id> <status>        Move task to new status
  python ops.py complete <task-id>             Mark task as done
  python ops.py detail <task-id>               Show task details
  python ops.py board                          Show board overview
  python ops.py team                           List team members
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_BASE = os.environ.get("TAKVENOPS_API_URL", "http://localhost:8001") + "/api"

# ── ANSI colors ──
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"

STATUS_COLORS = {
    "backlog": C_DIM,
    "in-progress": C_YELLOW,
    "review": C_CYAN,
    "done": C_GREEN,
    "blocked": C_RED,
}

STATUS_LABELS = {
    "backlog": "New",
    "in-progress": "Active",
    "review": "Resolved",
    "done": "Closed",
    "blocked": "Blocked",
}

PRIORITY_COLORS = {
    "P0": C_RED,
    "P1": C_YELLOW,
    "P2": C_BLUE,
    "P3": C_DIM,
}


def api(path, method="GET", data=None):
    """Make an API request and return JSON."""
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode()) if e.read else {}
        print(f"{C_RED}Error: {err.get('detail', e.reason)}{C_RESET}")
        sys.exit(1)
    except urllib.error.URLError:
        print(f"{C_RED}Error: Cannot connect to TakvenOps API at {API_BASE}{C_RESET}")
        print(f"Make sure the backend is running: python -m uvicorn backend.main:app --port 8001")
        sys.exit(1)


def print_task_row(t):
    """Print a single task as a formatted row."""
    status_c = STATUS_COLORS.get(t["status"], "")
    prio_c = PRIORITY_COLORS.get(t.get("priority", ""), "")
    assignee = t.get("assignee") or "Unassigned"
    status_label = STATUS_LABELS.get(t["status"], t["status"])
    print(
        f"  {C_BOLD}{t['id']:10}{C_RESET}  "
        f"{prio_c}{t.get('priority', '??'):3}{C_RESET}  "
        f"{status_c}{status_label:10}{C_RESET}  "
        f"{assignee:16}  "
        f"{t['title']}"
    )


# ── Commands ──

def cmd_tasks(args):
    """List tasks with optional filters."""
    tasks = api("/tasks")
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.assignee:
        tasks = [t for t in tasks if t.get("assignee") == args.assignee]
    if args.type:
        tasks = [t for t in tasks if t.get("type") == args.type]

    if not tasks:
        print(f"{C_DIM}No tasks found.{C_RESET}")
        return

    print(f"\n{C_BOLD}  {'ID':10}  {'PRI':3}  {'STATUS':10}  {'ASSIGNEE':16}  TITLE{C_RESET}")
    print(f"  {'─'*10}  {'─'*3}  {'─'*10}  {'─'*16}  {'─'*30}")
    for t in tasks:
        print_task_row(t)
    print(f"\n  {C_DIM}{len(tasks)} task(s){C_RESET}\n")


def cmd_my_tasks(args):
    """Show tasks assigned to a specific person/agent."""
    tasks = api("/tasks")
    mine = [t for t in tasks if t.get("assignee") == args.name]

    if not mine:
        print(f"{C_DIM}No tasks assigned to '{args.name}'.{C_RESET}")
        return

    print(f"\n{C_BOLD}Tasks assigned to {args.name}:{C_RESET}")
    print(f"  {'ID':10}  {'PRI':3}  {'STATUS':10}  TITLE")
    print(f"  {'─'*10}  {'─'*3}  {'─'*10}  {'─'*30}")
    for t in mine:
        status_c = STATUS_COLORS.get(t["status"], "")
        prio_c = PRIORITY_COLORS.get(t.get("priority", ""), "")
        status_label = STATUS_LABELS.get(t["status"], t["status"])
        print(
            f"  {C_BOLD}{t['id']:10}{C_RESET}  "
            f"{prio_c}{t.get('priority', '??'):3}{C_RESET}  "
            f"{status_c}{status_label:10}{C_RESET}  "
            f"{t['title']}"
        )
    print(f"\n  {C_DIM}{len(mine)} task(s){C_RESET}\n")


def cmd_create(args):
    """Create a new task."""
    data = {
        "title": args.title,
        "type": args.type or "feature",
        "priority": args.priority or "P2",
        "assignee": args.assignee or None,
        "labels": [l.strip() for l in args.labels.split(",")] if args.labels else [],
        "body_markdown": args.description or "",
    }
    result = api("/tasks", method="POST", data=data)
    print(f"{C_GREEN}Created task: {C_BOLD}{result['id']}{C_RESET}")
    print(f"  Title:    {result['title']}")
    print(f"  Type:     {result.get('type', 'feature')}")
    print(f"  Priority: {result.get('priority', 'P2')}")
    print(f"  Assignee: {result.get('assignee') or 'Unassigned'}")
    if data["labels"]:
        print(f"  Labels:   {', '.join(data['labels'])}")


def cmd_assign(args):
    """Assign a task to someone."""
    result = api(f"/tasks/{args.task_id}/assign", method="POST", data={"assignee": args.assignee})
    print(f"{C_GREEN}Assigned {C_BOLD}{args.task_id}{C_RESET}{C_GREEN} to {C_BOLD}{args.assignee}{C_RESET}")


def cmd_move(args):
    """Move a task to a new status."""
    valid = ["backlog", "in-progress", "review", "done", "blocked"]
    if args.status not in valid:
        print(f"{C_RED}Invalid status. Choose from: {', '.join(valid)}{C_RESET}")
        sys.exit(1)
    api(f"/tasks/{args.task_id}/move", method="POST", data={"status": args.status})
    label = STATUS_LABELS.get(args.status, args.status)
    print(f"{C_GREEN}Moved {C_BOLD}{args.task_id}{C_RESET}{C_GREEN} → {label}{C_RESET}")


def cmd_complete(args):
    """Mark a task as done."""
    api(f"/tasks/{args.task_id}/move", method="POST", data={"status": "done"})
    print(f"{C_GREEN}Completed {C_BOLD}{args.task_id}{C_RESET} ✓")


def cmd_detail(args):
    """Show detailed info about a task."""
    t = api(f"/tasks/{args.task_id}")
    status_c = STATUS_COLORS.get(t["status"], "")
    prio_c = PRIORITY_COLORS.get(t.get("priority", ""), "")
    status_label = STATUS_LABELS.get(t["status"], t["status"])

    print(f"\n{C_BOLD}{'─'*50}{C_RESET}")
    print(f"  {C_BOLD}{t['id']}{C_RESET}  {t['title']}")
    print(f"  {C_DIM}{'─'*48}{C_RESET}")
    print(f"  Type:     {t.get('type', '?')}")
    print(f"  Priority: {prio_c}{t.get('priority', '?')}{C_RESET}")
    print(f"  Status:   {status_c}{status_label}{C_RESET}")
    print(f"  Assignee: {t.get('assignee') or 'Unassigned'}")
    if t.get("due_date"):
        print(f"  Due:      {t['due_date']}")
    if t.get("labels"):
        labels = t["labels"] if isinstance(t["labels"], list) else json.loads(t["labels"])
        if labels:
            print(f"  Labels:   {', '.join(labels)}")
    if t.get("body_markdown"):
        print(f"\n  {C_DIM}Description:{C_RESET}")
        for line in t["body_markdown"].split("\n"):
            print(f"    {line}")
    print(f"{C_BOLD}{'─'*50}{C_RESET}\n")


def cmd_board(args):
    """Show board overview with task counts."""
    tasks = api("/tasks")
    by_status = {}
    for s in ["backlog", "in-progress", "review", "done", "blocked"]:
        by_status[s] = [t for t in tasks if t["status"] == s]

    print(f"\n{C_BOLD}  TakvenOps Board{C_RESET}")
    print(f"  {'─'*40}")
    for status, items in by_status.items():
        c = STATUS_COLORS.get(status, "")
        label = STATUS_LABELS.get(status, status)
        bar = "█" * len(items) + C_DIM + "░" * (20 - min(len(items), 20)) + C_RESET
        print(f"  {c}{label:10}{C_RESET}  {bar}  {len(items)}")
    print(f"\n  {C_DIM}Total: {len(tasks)} task(s){C_RESET}\n")


def cmd_team(args):
    """List team members."""
    members = api("/team")
    if not members:
        print(f"{C_DIM}No team members found.{C_RESET}")
        return

    print(f"\n{C_BOLD}  {'ID':16}  {'NAME':24}  {'TYPE':10}  ROLE{C_RESET}")
    print(f"  {'─'*16}  {'─'*24}  {'─'*10}  {'─'*12}")
    for m in members:
        type_c = C_CYAN if m.get("type") == "ai-agent" else ""
        print(
            f"  {m['id']:16}  {m['name']:24}  "
            f"{type_c}{m.get('type', 'human'):10}{C_RESET}  "
            f"{m.get('role', '?')}"
        )
    print()


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        prog="ops",
        description="TakvenOps CLI — Manage tasks from the command line",
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # tasks
    p_tasks = sub.add_parser("tasks", help="List tasks")
    p_tasks.add_argument("--status", "-s", help="Filter by status")
    p_tasks.add_argument("--assignee", "-a", help="Filter by assignee")
    p_tasks.add_argument("--type", "-t", help="Filter by type")

    # my-tasks
    p_mine = sub.add_parser("my-tasks", help="Show tasks assigned to someone")
    p_mine.add_argument("name", help="Assignee name (e.g. antigravity, claude-code, admin)")

    # create
    p_create = sub.add_parser("create", help="Create a new task")
    p_create.add_argument("title", help="Task title")
    p_create.add_argument("--type", "-t", help="Type: feature, bug, tech-debt, research, ops")
    p_create.add_argument("--priority", "-p", help="Priority: P0, P1, P2, P3")
    p_create.add_argument("--assignee", "-a", help="Assign to someone")
    p_create.add_argument("--labels", "-l", help="Comma-separated labels")
    p_create.add_argument("--description", "-d", help="Task description")

    # assign
    p_assign = sub.add_parser("assign", help="Assign a task")
    p_assign.add_argument("task_id", help="Task ID")
    p_assign.add_argument("assignee", help="Assignee name")

    # move
    p_move = sub.add_parser("move", help="Move task to new status")
    p_move.add_argument("task_id", help="Task ID")
    p_move.add_argument("status", help="New status: backlog, in-progress, review, done, blocked")

    # complete
    p_done = sub.add_parser("complete", help="Mark task as done")
    p_done.add_argument("task_id", help="Task ID")

    # detail
    p_detail = sub.add_parser("detail", help="Show task details")
    p_detail.add_argument("task_id", help="Task ID")

    # board
    sub.add_parser("board", help="Show board overview")

    # team
    sub.add_parser("team", help="List team members")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "tasks": cmd_tasks,
        "my-tasks": cmd_my_tasks,
        "create": cmd_create,
        "assign": cmd_assign,
        "move": cmd_move,
        "complete": cmd_complete,
        "detail": cmd_detail,
        "board": cmd_board,
        "team": cmd_team,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
