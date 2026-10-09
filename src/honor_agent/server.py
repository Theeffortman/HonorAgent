"""Minimal Honor Agent API server."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .github_intelligence import build_repo_insight, fetch_github_repo_metadata, parse_github_repo_url
from .models import AgentInfo, ApiResponse, EvolutionReport, GitHubRepoRequest, Task, TaskCreate, TaskResult
from .orchestrator import orchestrate_task

app = FastAPI(
    title="Honor Agent",
    description="Minimal runnable API for multi-agent task orchestration.",
    version="0.1.0",
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

TASKS: dict[str, Task] = {}
TASK_RESULTS: dict[str, TaskResult] = {}
EVOLUTION_REPORTS: dict[str, EvolutionReport] = {}
AGENTS = [
    AgentInfo(
        id="data_analyst",
        name="Data Analyst",
        description="Analyze structured data and summarize insights.",
        capabilities=["analysis", "reporting"],
    ),
    AgentInfo(
        id="report_generator",
        name="Report Generator",
        description="Create concise reports from task results.",
        capabilities=["writing", "summarization"],
    ),
    AgentInfo(
        id="github_intelligence",
        name="GitHub Intelligence",
        description="Analyze GitHub repositories and turn signals into actionable tasks.",
        capabilities=["repository-analysis", "task-planning", "risk-detection"],
    ),
]


def ok(data: Any = None, message: str = "操作成功") -> ApiResponse:
    return ApiResponse(success=True, data=data, message=message)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "honor-agent"}


@app.get("/", include_in_schema=False)
async def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/v1/tasks", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate) -> ApiResponse:
    task = Task(**payload.model_dump())
    TASKS[task.id] = task
    return ok(task.model_dump(mode="json"), "任务创建成功")


@app.get("/api/v1/tasks", response_model=ApiResponse)
async def list_tasks() -> ApiResponse:
    return ok([task.model_dump(mode="json") for task in TASKS.values()])


@app.get("/api/v1/tasks/{task_id}", response_model=ApiResponse)
async def get_task(task_id: str) -> ApiResponse:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ok(task.model_dump(mode="json"))


@app.post("/api/v1/tasks/{task_id}/run", response_model=ApiResponse)
async def run_task(task_id: str) -> ApiResponse:
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.now(timezone.utc)
    task.status = "running"
    task.updated_at = now
    orchestration = orchestrate_task(task, AGENTS)
    task.status = "completed"
    task.updated_at = orchestration.completed_at
    result = TaskResult(
        task_id=task.id,
        status=task.status,
        output=orchestration.model_dump(mode="json"),
    )
    TASK_RESULTS[task.id] = result
    if orchestration.evolution:
        EVOLUTION_REPORTS[task.id] = orchestration.evolution
    return ok(result.model_dump(mode="json"), "任务执行完成")


@app.get("/api/v1/tasks/{task_id}/result", response_model=ApiResponse)
async def get_task_result(task_id: str) -> ApiResponse:
    result = TASK_RESULTS.get(task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task result not found")
    return ok(result.model_dump(mode="json"))


@app.get("/api/v1/tasks/{task_id}/evolution", response_model=ApiResponse)
async def get_task_evolution(task_id: str) -> ApiResponse:
    report = EVOLUTION_REPORTS.get(task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Evolution report not found")
    return ok(report.model_dump(mode="json"))


@app.get("/api/v1/agents", response_model=ApiResponse)
async def list_agents() -> ApiResponse:
    return ok([agent.model_dump(mode="json") for agent in AGENTS])


@app.post("/api/v1/github/analyze", response_model=ApiResponse)
async def analyze_github_repository(payload: GitHubRepoRequest) -> ApiResponse:
    try:
        ref = parse_github_repo_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    metadata: dict[str, Any] = {}
    if payload.include_remote:
        try:
            metadata = await fetch_github_repo_metadata(ref)
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code,
                detail="GitHub repository metadata request failed",
            ) from exc
        except httpx.HTTPError:
            metadata = {}

    insight = build_repo_insight(ref, metadata)
    return ok(insight.model_dump(mode="json"), "GitHub 仓库分析完成")


def main() -> None:
    uvicorn.run("honor_agent.server:app", host="0.0.0.0", port=8000, reload=False)
