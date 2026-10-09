"""Async Python SDK for Honor Agent."""

from __future__ import annotations

from typing import Any

import httpx

from .models import AgentInfo, EvolutionReport, GitHubRepoInsight, Task, TaskCreate, TaskParams, TaskResult


class TasksClient:
    def __init__(self, client: "HonorAgent") -> None:
        self._client = client

    async def create(
        self,
        *,
        name: str,
        description: str = "",
        agents: list[str] | None = None,
        params: TaskParams | dict[str, Any] | None = None,
        priority: str = "normal",
    ) -> Task:
        payload = TaskCreate(
            name=name,
            description=description,
            agents=agents or [],
            params=params or TaskParams(),
            priority=priority,  # type: ignore[arg-type]
        ).model_dump(mode="json")
        data = await self._client._request("POST", "/api/v1/tasks", json=payload)
        return Task.model_validate(data)

    async def get(self, task_id: str) -> Task:
        data = await self._client._request("GET", f"/api/v1/tasks/{task_id}")
        return Task.model_validate(data)

    async def list(self) -> list[Task]:
        data = await self._client._request("GET", "/api/v1/tasks")
        return [Task.model_validate(item) for item in data]

    async def run(self, task_id: str) -> TaskResult:
        data = await self._client._request("POST", f"/api/v1/tasks/{task_id}/run")
        return TaskResult.model_validate(data)

    async def result(self, task_id: str) -> TaskResult:
        data = await self._client._request("GET", f"/api/v1/tasks/{task_id}/result")
        return TaskResult.model_validate(data)

    async def evolution(self, task_id: str) -> EvolutionReport:
        data = await self._client._request("GET", f"/api/v1/tasks/{task_id}/evolution")
        return EvolutionReport.model_validate(data)


class AgentsClient:
    def __init__(self, client: "HonorAgent") -> None:
        self._client = client

    async def list(self) -> list[AgentInfo]:
        data = await self._client._request("GET", "/api/v1/agents")
        return [AgentInfo.model_validate(item) for item in data]


class GitHubClient:
    def __init__(self, client: "HonorAgent") -> None:
        self._client = client

    async def analyze(self, url: str, *, include_remote: bool = True) -> GitHubRepoInsight:
        data = await self._client._request(
            "POST",
            "/api/v1/github/analyze",
            json={"url": url, "include_remote": include_remote},
        )
        return GitHubRepoInsight.model_validate(data)


class HonorAgent:
    """HTTP client for the Honor Agent API."""

    def __init__(self, api_key: str, base_url: str = "http://localhost:8000") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.tasks = TasksClient(self)
        self.agents = AgentsClient(self)
        self.github = GitHubClient(self)

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.request(method, path, headers=headers, **kwargs)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "success" in payload:
            if not payload["success"]:
                raise RuntimeError(payload.get("message") or "Honor Agent request failed")
            return payload.get("data")
        return payload
