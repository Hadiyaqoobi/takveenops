#!/usr/bin/env python3
"""TakvenOps — AI-native project management CLI.

Commands:
  status    Show board overview (task counts by status)
  board     Show full board with task details
  standup   Generate daily standup report
  scan      Scan codebase for issues → create task suggestions
  assign    Assign a task to a team member
  move      Move a task to a new status
  create    Create a new task from template
  verify    Run verification checks on a task
"""

import argparse
import os
import re
import sys
import glob
import shutil
from datetime import datetime, date
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
OPS_DIR = ROOT / ".takvenops"
STATUSES = ["backlog", "in-progress", "review", "done", "blocked"]
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

# ── ANSI colors ────────────────────────────────────────────
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

PRIORITY_COLORS = {
    "P0": C_RED + C_BOLD,
    "P1": C_YELLOW,
    "P2": C_BLUE,
    "P3": C_DIM,
}


def parse_frontmatter(filepath):
    """Parse YAML-like frontmatter from a task markdown file."""
    text = Path(filepath).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.index("---", 3)
    fm_text = text[3:end].strip()

    meta = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue

        # List item
        if line.startswith("  - ") and current_key:
            val = line.strip("- ").strip()
            if current_list is None:
                current_list = []
            current_list.append(val)
            meta[current_key] = current_list
            continue

        # Inline list [a, b, c]
        m = re.match(r"^(\w[\w_]*)\s*:\s*\[(.+)\]\s*$", line)
        if m:
            current_key = m.group(1)
            current_list = None
            meta[current_key] = [v.strip().strip("'\"") for v in m.group(2).split(",")]
            continue

        # Key: value
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

    return meta


def get_tasks_by_status():
    """Return dict of {status: [task_meta_dict, ...]}."""
    result = {s: [] for s in STATUSES}
    for status in STATUSES:
        status_dir = OPS_DIR / status
        if not status_dir.exists():
            continue
        for f in sorted(status_dir.glob("ROE-*.md")):
            meta = parse_frontmatter(f)
            meta["_file"] = str(f)
            meta["_status_dir"] = status
            result[status].append(meta)
    return result


def get_all_tasks():
    """Return flat list of all tasks."""
    tasks = get_tasks_by_status()
    return [t for ts in tasks.values() for t in ts]


# ── Commands ───────────────────────────────────────────────

def cmd_status(_args):
    """Show board overview."""
    tasks = get_tasks_by_status()
    total = sum(len(ts) for ts in tasks.values())
    done_count = len(tasks["done"])

    print(f"\n{C_BOLD}╔══════════════════════════════════════╗{C_RESET}")
    print(f"{C_BOLD}║         TakvenOps — Sprint Board      ║{C_RESET}")
    print(f"{C_BOLD}╚══════════════════════════════════════╝{C_RESET}\n")

    for status in STATUSES:
        count = len(tasks[status])
        color = STATUS_COLORS.get(status, "")
        bar = "█" * count + "░" * (10 - min(count, 10))
        print(f"  {color}{status:15}{C_RESET}  {bar}  {C_BOLD}{count}{C_RESET}")

    print(f"\n  {C_DIM}{'─' * 40}{C_RESET}")
    pct = int(done_count / total * 100) if total else 0
    print(f"  Total: {C_BOLD}{total}{C_RESET}  |  Done: {C_GREEN}{done_count}{C_RESET}  |  Progress: {C_BOLD}{pct}%{C_RESET}\n")


def cmd_board(_args):
    """Show full board with task details."""
    tasks = get_tasks_by_status()

    print(f"\n{C_BOLD}{'ID':<10} {'P':>3}  {'Status':<14} {'Assignee':<15} Title{C_RESET}")
    print(f"  {C_DIM}{'─' * 75}{C_RESET}")

    for status in STATUSES:
        for t in tasks[status]:
            tid = t.get("id", "?")
            priority = t.get("priority", "?")
            assignee = t.get("assignee", "unassigned") or "unassigned"
            title = t.get("title", "Untitled")
            p_color = PRIORITY_COLORS.get(priority, "")
            s_color = STATUS_COLORS.get(status, "")

            # Truncate title
            if len(title) > 40:
                title = title[:37] + "..."

            print(f"  {C_CYAN}{tid:<10}{C_RESET} {p_color}{priority:>3}{C_RESET}  {s_color}{status:<14}{C_RESET} {C_DIM}{assignee:<15}{C_RESET} {title}")

    print()


def cmd_standup(_args):
    """Generate daily standup report."""
    tasks = get_tasks_by_status()
    today = date.today().isoformat()

    report = []
    report.append(f"# Daily Standup — {datetime.now().strftime('%B %d, %Y')}\n")

    # Done
    done = tasks.get("done", [])
    if done:
        report.append("## ✅ Completed")
        for t in done:
            report.append(f"- {t.get('id')}: {t.get('title')} ({t.get('assignee', '?')})")
        report.append("")

    # In Progress
    wip = tasks.get("in-progress", [])
    if wip:
        report.append("## 🔄 In Progress")
        for t in wip:
            report.append(f"- {t.get('id')}: {t.get('title')} ({t.get('assignee', '?')})")
        report.append("")

    # Review
    review = tasks.get("review", [])
    if review:
        report.append("## 👀 Awaiting Review")
        for t in review:
            report.append(f"- {t.get('id')}: {t.get('title')} ({t.get('assignee', '?')})")
        report.append("")

    # Blocked
    blocked = tasks.get("blocked", [])
    if blocked:
        report.append("## 🚫 Blocked")
        for t in blocked:
            report.append(f"- {t.get('id')}: {t.get('title')} ({t.get('assignee', '?')})")
        report.append("")

    # Backlog
    backlog = tasks.get("backlog", [])
    p0_p1 = [t for t in backlog if t.get("priority") in ("P0", "P1")]
    if p0_p1:
        report.append("## 🔴 High Priority Backlog")
        for t in p0_p1:
            assignee = t.get("assignee", "unassigned") or "unassigned"
            report.append(f"- [{t.get('priority')}] {t.get('id')}: {t.get('title')} → {assignee}")
        report.append("")

    # Sprint Progress
    total = sum(len(ts) for ts in tasks.values())
    done_count = len(done)
    pct = int(done_count / total * 100) if total else 0
    report.append(f"## 📊 Sprint Progress: {done_count}/{total} tasks ({pct}%)\n")

    report_text = "\n".join(report)

    # Save report
    report_file = OPS_DIR / "reports" / f"standup-{today}.md"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"{C_DIM}Saved to: {report_file.relative_to(ROOT)}{C_RESET}\n")


def cmd_assign(args):
    """Assign a task to a team member."""
    task_id = args.task_id.upper()
    assignee = args.assignee

    # Find the task file
    for status in STATUSES:
        for f in (OPS_DIR / status).glob("*.md"):
            meta = parse_frontmatter(f)
            if meta.get("id") == task_id:
                text = f.read_text(encoding="utf-8")
                old_assignee = meta.get("assignee") or ""
                if old_assignee:
                    text = text.replace(f"assignee: {old_assignee}", f"assignee: {assignee}")
                else:
                    text = text.replace("assignee: ", f"assignee: {assignee}")
                f.write_text(text, encoding="utf-8")
                print(f"{C_GREEN}✓{C_RESET} Assigned {C_CYAN}{task_id}{C_RESET} to {C_BOLD}{assignee}{C_RESET}")
                return

    print(f"{C_RED}✗ Task {task_id} not found{C_RESET}")


def cmd_move(args):
    """Move a task to a new status."""
    task_id = args.task_id.upper()
    target_status = args.status

    if target_status not in STATUSES:
        print(f"{C_RED}✗ Invalid status: {target_status}. Use: {', '.join(STATUSES)}{C_RESET}")
        return

    for status in STATUSES:
        for f in (OPS_DIR / status).glob("*.md"):
            meta = parse_frontmatter(f)
            if meta.get("id") == task_id:
                target_dir = OPS_DIR / target_status
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file = target_dir / f.name

                # Update status in frontmatter
                text = f.read_text(encoding="utf-8")
                text = re.sub(r"status:\s*\S+", f"status: {target_status}", text)
                target_file.write_text(text, encoding="utf-8")

                # Remove from old location
                if f != target_file:
                    f.unlink()

                print(f"{C_GREEN}✓{C_RESET} Moved {C_CYAN}{task_id}{C_RESET} from {status} → {C_BOLD}{target_status}{C_RESET}")
                return

    print(f"{C_RED}✗ Task {task_id} not found{C_RESET}")


def cmd_create(args):
    """Create a new task from template."""
    task_type = args.type
    title = " ".join(args.title)

    template_file = OPS_DIR / "templates" / f"{task_type}.md"
    if not template_file.exists():
        print(f"{C_RED}✗ Template not found: {task_type}.md{C_RESET}")
        print(f"  Available: {', '.join(t.stem for t in (OPS_DIR / 'templates').glob('*.md'))}")
        return

    # Get next ID
    all_tasks = get_all_tasks()
    max_id = max((int(t.get("id", "ROE-0").split("-")[1]) for t in all_tasks), default=0)
    next_id = max_id + 1
    task_id = f"ROE-{next_id:03d}"

    template = template_file.read_text(encoding="utf-8")
    template = template.replace("ROE-XXX", task_id)
    template = template.replace("title: ", f"title: {title}")
    template = template.replace("YYYY-MM-DD", date.today().isoformat())

    target = OPS_DIR / "backlog" / f"{task_id}.md"
    target.write_text(template, encoding="utf-8")

    print(f"{C_GREEN}✓{C_RESET} Created {C_CYAN}{task_id}{C_RESET}: {title}")
    print(f"  {C_DIM}File: {target.relative_to(ROOT)}{C_RESET}")
    print(f"  {C_DIM}Edit the file to fill in details.{C_RESET}\n")


def cmd_scan(_args):
    """Scan codebase for issues and suggest tasks."""
    print(f"\n{C_BOLD}🔍 Scanning codebase...{C_RESET}\n")

    issues = []

    # 1. Find TODO/FIXME/HACK comments
    for ext in ["*.py", "*.jsx", "*.js"]:
        for f in ROOT.rglob(ext):
            rel = f.relative_to(ROOT)
            if any(skip in str(rel) for skip in ["node_modules", "__pycache__", ".takvenops", "venv"]):
                continue
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").split("\n"), 1):
                    for tag in ["TODO", "FIXME", "HACK", "XXX"]:
                        if tag in line and not line.strip().startswith("#!"):
                            issues.append({
                                "type": "todo",
                                "file": str(rel),
                                "line": i,
                                "tag": tag,
                                "text": line.strip()[:80],
                            })
            except Exception:
                continue

    # 2. Find Python files without corresponding tests
    api_files = list((ROOT / "api").rglob("*.py"))
    test_dir = ROOT / "tests"
    for f in api_files:
        rel = f.relative_to(ROOT)
        if "__pycache__" in str(rel) or "__init__" in f.name:
            continue
        test_name = f"test_{f.name}"
        if test_dir.exists() and not list(test_dir.rglob(test_name)):
            issues.append({
                "type": "missing_test",
                "file": str(rel),
                "line": 0,
                "tag": "NO TEST",
                "text": f"No test file found for {f.name}",
            })

    # 3. Find API routes without error handling
    for f in (ROOT / "api" / "routes").glob("*.py"):
        try:
            content = f.read_text(encoding="utf-8")
            # Check for route functions without try/except
            funcs = re.findall(r"async def (\w+)\(", content)
            has_try = "try:" in content
            if funcs and not has_try:
                issues.append({
                    "type": "error_handling",
                    "file": str(f.relative_to(ROOT)),
                    "line": 0,
                    "tag": "NO TRY/EXCEPT",
                    "text": f"Route file has {len(funcs)} endpoints but no try/except blocks",
                })
        except Exception:
            continue

    # Print results
    if not issues:
        print(f"  {C_GREEN}✓ No issues found!{C_RESET}\n")
        return

    # Group by type
    by_type = {}
    for issue in issues:
        by_type.setdefault(issue["type"], []).append(issue)

    for itype, items in by_type.items():
        type_labels = {
            "todo": "📝 TODO/FIXME Comments",
            "missing_test": "🧪 Missing Tests",
            "error_handling": "⚠️  Missing Error Handling",
        }
        print(f"  {C_BOLD}{type_labels.get(itype, itype)}{C_RESET} ({len(items)} found)")
        for item in items[:10]:  # cap display at 10 per type
            print(f"    {C_DIM}{item['file']}:{item['line']}{C_RESET}  {item['text']}")
        if len(items) > 10:
            print(f"    {C_DIM}... and {len(items) - 10} more{C_RESET}")
        print()

    print(f"  {C_BOLD}Total: {len(issues)} issues found.{C_RESET}")
    print(f"  {C_DIM}Run 'python scripts/takvenops.py create <type> <title>' to create tasks.{C_RESET}\n")


def cmd_verify(args):
    """Run verification checks for a task."""
    task_id = args.task_id.upper()

    for status in STATUSES:
        for f in (OPS_DIR / status).glob("*.md"):
            meta = parse_frontmatter(f)
            if meta.get("id") == task_id:
                verification = meta.get("verification", {})
                if not verification:
                    print(f"{C_YELLOW}⚠ No verification defined for {task_id}{C_RESET}")
                    return

                v_type = verification if isinstance(verification, str) else "see file"
                print(f"\n{C_BOLD}Verifying {task_id}...{C_RESET}")
                print(f"  Type: {v_type}")

                # Read full file for verification block
                text = f.read_text(encoding="utf-8")
                cmd_match = re.search(r'command:\s*"(.+)"', text)
                if cmd_match:
                    cmd = cmd_match.group(1)
                    print(f"  Command: {C_CYAN}{cmd}{C_RESET}")
                    print(f"\n  {C_DIM}Run this command manually to verify:{C_RESET}")
                    print(f"  {C_BOLD}{cmd}{C_RESET}\n")
                else:
                    print(f"  {C_YELLOW}Manual verification required — check acceptance criteria in the task file.{C_RESET}\n")
                return

    print(f"{C_RED}✗ Task {task_id} not found{C_RESET}")


# ── Main ───────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="takvenops",
        description="TakvenOps — AI-native project management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show board overview")
    sub.add_parser("board", help="Show full board with details")
    sub.add_parser("standup", help="Generate daily standup report")
    sub.add_parser("scan", help="Scan codebase for issues")

    p_assign = sub.add_parser("assign", help="Assign a task")
    p_assign.add_argument("task_id", help="Task ID (e.g., ROE-001)")
    p_assign.add_argument("assignee", help="Assignee (e.g., antigravity, human:rahima)")

    p_move = sub.add_parser("move", help="Move a task to a new status")
    p_move.add_argument("task_id", help="Task ID")
    p_move.add_argument("status", help="Target status", choices=STATUSES)

    p_create = sub.add_parser("create", help="Create a new task")
    p_create.add_argument("type", help="Task type (bug, feature, tech-debt)")
    p_create.add_argument("title", nargs="+", help="Task title")

    p_verify = sub.add_parser("verify", help="Verify a task")
    p_verify.add_argument("task_id", help="Task ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "status": cmd_status,
        "board": cmd_board,
        "standup": cmd_standup,
        "scan": cmd_scan,
        "assign": cmd_assign,
        "move": cmd_move,
        "create": cmd_create,
        "verify": cmd_verify,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
