"""Shared SDK and API models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


TaskStatus = Literal["created", "running", "completed", "failed"]


class TaskParams(BaseModel):
    """Flexible task parameters passed to agents."""

    data_source: str | None = None
    date_range: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class TaskCreate(BaseModel):
    """Request body for creating a task."""

    name: str = Field(min_length=1)
    description: str = ""
    agents: list[str] = Field(default_factory=list)
    params: TaskParams | dict[str, Any] = Field(default_factory=TaskParams)
    priority: Literal["low", "normal", "high", "critical"] = "normal"


class Task(BaseModel):
    """Persisted task record."""

    id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:12]}")
    name: str
    description: str = ""
    agents: list[str] = Field(default_factory=list)
    params: TaskParams | dict[str, Any] = Field(default_factory=TaskParams)
    priority: str = "normal"
    status: TaskStatus = "created"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskResult(BaseModel):
    """Task execution result."""

    task_id: str
    status: TaskStatus
    output: dict[str, Any] | str | None = None


class AgentRun(BaseModel):
    """One agent's contribution during a task run."""

    agent_id: str
    agent_name: str
    status: Literal["completed", "skipped", "failed"] = "completed"
    input_summary: str
    output: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentEvolution(BaseModel):
    """Quality review and improvement plan for one agent run."""

    agent_id: str
    score: int
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    improvement_actions: list[str] = Field(default_factory=list)


class EvolutionReport(BaseModel):
    """Post-run self-improvement report generated from an orchestration trace."""

    task_id: str
    overall_score: int
    readiness: Literal["needs_attention", "usable", "strong"]
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
    agent_reports: list[AgentEvolution] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestrationResult(BaseModel):
    """Full multi-agent execution trace for a task."""

    task_id: str
    status: TaskStatus
    strategy: Literal["sequential"] = "sequential"
    agent_count: int
    runs: list[AgentRun] = Field(default_factory=list)
    final_output: dict[str, Any] = Field(default_factory=dict)
    evolution: EvolutionReport | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentInfo(BaseModel):
    """Available agent metadata."""

    id: str
    name: str
    description: str
    capabilities: list[str] = Field(default_factory=list)


class GitHubRepoRequest(BaseModel):
    """Request for GitHub repository analysis."""

    url: str = Field(min_length=1)
    include_remote: bool = True


class GitHubRepoInsight(BaseModel):
    """Repository intelligence summary generated from GitHub metadata."""

    owner: str
    repo: str
    url: str
    health_score: int
    signals: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    suggested_tasks: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    """Consistent response envelope used by the REST API."""

    success: bool
    data: Any = None
    message: str = ""
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
