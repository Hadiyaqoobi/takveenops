"""Codebase scanner routes."""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from ..database import get_db
from ..services.scanner import CodebaseScanner

router = APIRouter(prefix="/api/scanner", tags=["scanner"])


@router.post("/run")
def run_scan(body: dict):
    repo_path = body.get("repo_path", "")
    if not repo_path:
        raise HTTPException(status_code=400, detail="repo_path is required")

    scanner = CodebaseScanner()
    results = scanner.scan(repo_path)

    conn = get_db()
    conn.execute(
        "INSERT INTO scan_results (repo_path, total_issues, todo_count, missing_tests_count, error_handling_count, results_json) VALUES (?, ?, ?, ?, ?, ?)",
        (repo_path, results["total"], results["todo_count"], results["missing_tests_count"],
         results["error_handling_count"], json.dumps(results["issues"]))
    )
    conn.commit()
    conn.close()

    return results


@router.get("/results")
def get_results():
    conn = get_db()
    rows = conn.execute("SELECT * FROM scan_results ORDER BY scan_date DESC LIMIT 20").fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d.get("results_json"):
            try:
                d["issues"] = json.loads(d["results_json"])
            except (json.JSONDecodeError, TypeError):
                d["issues"] = []
        del d["results_json"]
        results.append(d)

    return results
