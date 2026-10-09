from fastapi.testclient import TestClient

from honor_agent.server import EVOLUTION_REPORTS, TASK_RESULTS, TASKS, app


def setup_function() -> None:
    TASKS.clear()
    TASK_RESULTS.clear()
    EVOLUTION_REPORTS.clear()


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_serves_static_console() -> None:
    client = TestClient(app)

    response = client.get("/")
    css_response = client.get("/static/app.css")

    assert response.status_code == 200
    assert "Honor Agent 控制台" in response.text
    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]


def test_create_get_and_run_task() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "name": "数据分析任务",
            "description": "分析销售数据并生成周报",
            "agents": ["data_analyst"],
            "params": {"data_source": "sales_db", "date_range": "last_week"},
        },
    )

    assert create_response.status_code == 201
    task = create_response.json()["data"]
    assert task["status"] == "created"

    get_response = client.get(f"/api/v1/tasks/{task['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == task["id"]

    run_response = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert run_response.status_code == 200
    result = run_response.json()["data"]
    assert result["status"] == "completed"
    assert result["task_id"] == task["id"]
    assert result["output"]["agent_count"] == 1
    assert result["output"]["runs"][0]["agent_id"] == "data_analyst"


def test_run_task_orchestrates_multiple_agents_with_handoffs() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/tasks",
        json={
            "name": "多智能体交互验证",
            "description": "分析数据，生成报告，并规划仓库维护动作",
            "agents": ["data_analyst", "report_generator", "github_intelligence"],
            "params": {
                "data_source": "sales_db",
                "date_range": "last_week",
                "extra": {"github_url": "https://github.com/Theeffortman/HonorAgent"},
            },
        },
    )
    task = create_response.json()["data"]

    run_response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert run_response.status_code == 200
    output = run_response.json()["data"]["output"]
    assert output["status"] == "completed"
    assert output["agent_count"] == 3
    assert [run["agent_id"] for run in output["runs"]] == [
        "data_analyst",
        "report_generator",
        "github_intelligence",
    ]
    assert output["runs"][1]["input_summary"].startswith("Received context from data_analyst")
    assert output["runs"][2]["input_summary"].startswith("Received context from report_generator")
    assert len(output["final_output"]["handoffs"]) == 3
    assert output["evolution"]["overall_score"] >= 65
    assert output["evolution"]["readiness"] in {"usable", "strong"}

    result_response = client.get(f"/api/v1/tasks/{task['id']}/result")
    evolution_response = client.get(f"/api/v1/tasks/{task['id']}/evolution")

    assert result_response.status_code == 200
    assert result_response.json()["data"]["task_id"] == task["id"]
    assert evolution_response.status_code == 200
    assert evolution_response.json()["data"]["agent_reports"][0]["agent_id"] == "data_analyst"


def test_run_task_skips_unknown_agents_in_trace() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/tasks",
        json={"name": "Unknown agent task", "agents": ["missing_agent", "data_analyst"]},
    )
    task = create_response.json()["data"]

    run_response = client.post(f"/api/v1/tasks/{task['id']}/run")

    assert run_response.status_code == 200
    output = run_response.json()["data"]["output"]
    assert output["agent_count"] == 2
    assert output["runs"][0]["status"] == "skipped"
    assert output["runs"][1]["status"] == "completed"
    assert output["evolution"]["risks"]


def test_task_result_and_evolution_return_404_before_run() -> None:
    client = TestClient(app)
    create_response = client.post("/api/v1/tasks", json={"name": "Not run yet"})
    task = create_response.json()["data"]

    result_response = client.get(f"/api/v1/tasks/{task['id']}/result")
    evolution_response = client.get(f"/api/v1/tasks/{task['id']}/evolution")

    assert result_response.status_code == 404
    assert evolution_response.status_code == 404


def test_list_agents() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/agents")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "data_analyst"


def test_analyze_github_repository_without_remote_metadata() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/github/analyze",
        json={"url": "https://github.com/Theeffortman/HonorAgent", "include_remote": False},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["owner"] == "Theeffortman"
    assert data["repo"] == "HonorAgent"
    assert data["health_score"] >= 0
    assert data["suggested_tasks"]


def test_analyze_github_repository_rejects_invalid_url() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/github/analyze",
        json={"url": "https://example.com/not-github", "include_remote": False},
    )

    assert response.status_code == 400
