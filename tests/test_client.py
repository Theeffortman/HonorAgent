import httpx
import pytest

from honor_agent import HonorAgent
from honor_agent.server import EVOLUTION_REPORTS, TASK_RESULTS, TASKS, app


@pytest.fixture(autouse=True)
def clear_tasks() -> None:
    TASKS.clear()
    TASK_RESULTS.clear()
    EVOLUTION_REPORTS.clear()


@pytest.mark.asyncio
async def test_sdk_create_and_run_task() -> None:
    transport = httpx.ASGITransport(app=app)
    original_async_client = httpx.AsyncClient

    class LocalAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            kwargs["base_url"] = "http://testserver"
            super().__init__(*args, **kwargs)

    httpx.AsyncClient = LocalAsyncClient  # type: ignore[assignment]
    try:
        client = HonorAgent(api_key="test-key", base_url="http://testserver")
        task = await client.tasks.create(name="Example", agents=["data_analyst"])
        result = await client.tasks.run(task.id)
        stored_result = await client.tasks.result(task.id)
        evolution = await client.tasks.evolution(task.id)
        insight = await client.github.analyze(
            "https://github.com/Theeffortman/HonorAgent",
            include_remote=False,
        )
    finally:
        httpx.AsyncClient = original_async_client  # type: ignore[assignment]

    assert task.name == "Example"
    assert result.status == "completed"
    assert stored_result.task_id == task.id
    assert evolution.task_id == task.id
    assert evolution.overall_score >= 0
    assert insight.repo == "HonorAgent"
