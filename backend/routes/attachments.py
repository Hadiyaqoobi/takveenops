"""File attachment routes for TakvenOps."""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["attachments"])

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", str(Path(__file__).parent.parent / "uploads")))
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".pptx",
    ".txt", ".md", ".csv", ".json", ".zip", ".gz",
}


def _validate_file(file: UploadFile, max_size: int = MAX_FILE_SIZE, allowed: set = ALLOWED_EXTENSIONS):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"File type {ext} not allowed")
    return ext


@router.post("/{task_id}/attachments")
async def upload_attachment(task_id: str, request: Request, file: UploadFile = File(...)):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    # Verify task exists
    conn = get_db()
    task = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id.upper(),)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")

    ext = _validate_file(file)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        conn.close()
        raise HTTPException(400, f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)")

    # Save file
    filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = UPLOAD_DIR / "tasks"
    save_dir.mkdir(parents=True, exist_ok=True)
    (save_dir / filename).write_bytes(content)

    # Insert DB record
    conn.execute(
        """INSERT INTO attachments (filename, original_name, content_type, size_bytes,
           entity_type, entity_id, uploaded_by, uploaded_by_username)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (filename, file.filename, file.content_type, len(content),
         "task", task_id.upper(), user["id"], user["username"]),
    )
    conn.commit()
    conn.close()

    return {
        "filename": filename,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "url": f"/api/uploads/tasks/{filename}",
    }


@router.get("/{task_id}/attachments")
def list_attachments(task_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    rows = conn.execute(
        """SELECT id, filename, original_name, content_type, size_bytes,
           uploaded_by_username, created_at
           FROM attachments WHERE entity_type = 'task' AND entity_id = ?
           ORDER BY created_at DESC""",
        (task_id.upper(),),
    ).fetchall()
    conn.close()

    return [
        {
            **dict(r),
            "url": f"/api/uploads/tasks/{r['filename']}",
        }
        for r in rows
    ]


@router.delete("/{task_id}/attachments/{attachment_id}")
def delete_attachment(task_id: str, attachment_id: int, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Not authenticated")

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM attachments WHERE id = ? AND entity_type = 'task' AND entity_id = ?",
        (attachment_id, task_id.upper()),
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Attachment not found")

    # Delete file
    fpath = UPLOAD_DIR / "tasks" / row["filename"]
    if fpath.exists():
        fpath.unlink()

    conn.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
    conn.commit()
    conn.close()

    return {"ok": True}
