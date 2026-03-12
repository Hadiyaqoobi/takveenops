"""Pydantic models for TakvenOps API."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class TaskCreate(BaseModel):
    title: str
    type: str = "feature"
    priority: str = "P2"
    status: str = "backlog"
    assignee: Optional[str] = None
    sprint_id: Optional[int] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    labels: list[str] = []
    files_involved: list[str] = []
    acceptance_criteria: list[str] = []
    verification_type: Optional[str] = None
    verification_command: Optional[str] = None
    verification_ai_check: Optional[str] = None
    depends_on: list[str] = []
    blocks: list[str] = []
    body_markdown: str = ""


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    sprint_id: Optional[int] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    labels: Optional[list[str]] = None
    files_involved: Optional[list[str]] = None
    acceptance_criteria: Optional[list[str]] = None
    verification_type: Optional[str] = None
    verification_command: Optional[str] = None
    verification_ai_check: Optional[str] = None
    depends_on: Optional[list[str]] = None
    blocks: Optional[list[str]] = None
    body_markdown: Optional[str] = None
    completion_notes: Optional[str] = None


class TaskMove(BaseModel):
    status: str


class TaskAssign(BaseModel):
    assignee: str


class SprintCreate(BaseModel):
    name: str
    goal: str = ""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None


class TeamMemberCreate(BaseModel):
    id: str
    name: str
    type: str = "human"
    role: str = "engineer"
    capabilities: list[str] = []
    max_concurrent_tasks: int = 3
    avatar_url: Optional[str] = None


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    capabilities: Optional[list[str]] = None
    max_concurrent_tasks: Optional[int] = None
    avatar_url: Optional[str] = None


class ScanRequest(BaseModel):
    repo_path: str
