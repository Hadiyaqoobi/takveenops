"""Codebase scanner service — adapted from existing_prototype/takvenops_cli.py."""

import os
import re
from pathlib import Path


SKIP_DIRS = {"node_modules", "__pycache__", ".takvenops", "venv", ".venv", ".git", "dist", "build"}
SCAN_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}


class CodebaseScanner:
    def scan(self, repo_path: str) -> dict:
        root = Path(repo_path)
        if not root.exists():
            return {"total": 0, "issues": [], "todo_count": 0, "missing_tests_count": 0, "error_handling_count": 0}

        issues = []
        issues += self._find_todos(root)
        issues += self._find_missing_tests(root)
        issues += self._find_error_handling(root)

        return {
            "total": len(issues),
            "issues": issues,
            "todo_count": sum(1 for i in issues if i["type"] == "todo"),
            "missing_tests_count": sum(1 for i in issues if i["type"] == "missing_test"),
            "error_handling_count": sum(1 for i in issues if i["type"] == "error_handling"),
        }

    def _should_skip(self, path: Path) -> bool:
        parts = set(path.parts)
        return bool(parts & SKIP_DIRS)

    def _find_todos(self, root: Path) -> list:
        issues = []
        for ext in SCAN_EXTENSIONS:
            for f in root.rglob(f"*{ext}"):
                if self._should_skip(f.relative_to(root)):
                    continue
                try:
                    lines = f.read_text(encoding="utf-8", errors="ignore").split("\n")
                    for i, line in enumerate(lines, 1):
                        for tag in ["TODO", "FIXME", "HACK", "XXX"]:
                            if tag in line and not line.strip().startswith("#!"):
                                issues.append({
                                    "type": "todo",
                                    "severity": "P2" if tag in ("TODO", "XXX") else "P1",
                                    "file": str(f.relative_to(root)),
                                    "line": i,
                                    "tag": tag,
                                    "text": line.strip()[:120],
                                })
                except Exception:
                    continue
        return issues

    def _find_missing_tests(self, root: Path) -> list:
        issues = []
        src_dirs = [root / "api", root / "src", root / "backend"]
        test_dirs = [root / "tests", root / "test", root / "__tests__"]

        existing_tests = set()
        for td in test_dirs:
            if td.exists():
                for f in td.rglob("*"):
                    existing_tests.add(f.stem.lower())

        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            for f in src_dir.rglob("*.py"):
                if self._should_skip(f.relative_to(root)):
                    continue
                if f.name.startswith("__"):
                    continue
                test_name = f"test_{f.stem}".lower()
                if test_name not in existing_tests:
                    issues.append({
                        "type": "missing_test",
                        "severity": "P2",
                        "file": str(f.relative_to(root)),
                        "line": 0,
                        "tag": "NO TEST",
                        "text": f"No test file found for {f.name}",
                    })
        return issues

    def _find_error_handling(self, root: Path) -> list:
        issues = []
        route_dirs = [root / "api" / "routes", root / "backend" / "routes"]

        for route_dir in route_dirs:
            if not route_dir.exists():
                continue
            for f in route_dir.glob("*.py"):
                try:
                    content = f.read_text(encoding="utf-8")
                    funcs = re.findall(r"(?:async\s+)?def\s+(\w+)\(", content)
                    has_try = "try:" in content
                    if funcs and not has_try:
                        issues.append({
                            "type": "error_handling",
                            "severity": "P1",
                            "file": str(f.relative_to(root)),
                            "line": 0,
                            "tag": "NO TRY/EXCEPT",
                            "text": f"Route file has {len(funcs)} endpoints but no error handling",
                        })
                except Exception:
                    continue
        return issues
