# Architecture

HonorAgent is an **early prototype**: a small FastAPI service (about 850 lines of Python in `src/honor_agent/`) that runs a sequence of rule-based agents over a task and returns a trace plus a rule-based scoring report. It does not call any large language model, and it has no database.

## Components

```
src/honor_agent/
├── server.py               FastAPI app, REST endpoints, in-memory stores, static UI
├── models.py               Pydantic models (tasks, results, agent runs, reports)
├── orchestrator.py         Runs the selected agents one after another
├── evolution.py            Rule-based scoring report ("evolution report")
├── github_intelligence.py  GitHub URL parsing, metadata fetch, health score
├── client.py               Async Python client (httpx) for the API
└── static/                 index.html, app.js, app.css (browser UI)
android/                    Native Android (Java) client for the API
```

### API server (`server.py`)
- FastAPI app, served by uvicorn on `0.0.0.0:8000` via the `honor-agent` console script.
- Serves the static web UI at `/` and `/static`.
- Keeps all state in three Python dictionaries (`TASKS`, `TASK_RESULTS`, `EVOLUTION_REPORTS`). Data is lost when the process restarts.
- Responses use a common envelope: `{success, data, message, request_id}`.
- No authentication is enforced. The Python client sends an `Authorization: Bearer` header, but the server does not check it.

### Agents
Three agents are registered in a fixed list. Each is a plain Python function with deterministic, rule-based output:

| ID | What it does |
|----|--------------|
| `data_analyst` | Builds a summary and three findings from `params.data_source`, `params.date_range` and the task priority. |
| `report_generator` | Turns the previous agent's findings (or the task description) into a short report. |
| `github_intelligence` | Returns a fixed list of repository-maintenance recommendations and echoes any repo URL given in params. |

An agent ID that is not registered is recorded as `skipped`.

### Orchestrator (`orchestrator.py`)
- Strategy is always `sequential`. If a task lists no agents, the first registered agent (`data_analyst`) runs.
- Each agent receives a context containing the task and the previous agent's output; every hand-off is recorded.
- Produces an `OrchestrationResult` with per-agent runs, a final output (summary, agent sequence, handoffs) and an evolution report.

### Scoring report (`evolution.py`)
- Each agent run starts at 50 points: +25 if completed, +10 if it has a `summary`, +10 if it has a `handoff`, +5 if it has an input summary, −35 if skipped (clamped to 0–100).
- The overall score is the average. Readiness is `strong` (≥85), `usable` (≥65) or `needs_attention`.
- Strengths, risks and next actions are fixed strings chosen by simple rules.

### GitHub analysis (`github_intelligence.py`)
- Parses `https://github.com/owner/repo` or `git@github.com:owner/repo` URLs.
- Optionally calls the public GitHub REST API (repo and branches endpoints); uses `GITHUB_TOKEN` if set.
- Computes a rule-based health score (description, license, stars, forks, topics, open issues, archived) and suggested tasks.

### Clients
- **Web UI** (`static/`): a single page that calls the API.
- **Python client** (`client.py`): `HonorAgent(api_key, base_url)` with `tasks`, `agents` and `github` helpers.
- **Android app** (`android/`): see [ANDROID.md](ANDROID.md). It calls `/health`, `/api/v1/github/analyze` and `/api/v1/tasks`; it does not bundle the server.

## Request flow

```
POST /api/v1/tasks          -> Task stored in memory (status "created")
POST /api/v1/tasks/{id}/run -> orchestrator runs agents sequentially
                            -> evolution report built
                            -> result + report stored in memory (status "completed")
GET  /api/v1/tasks/{id}/result | /evolution
```

## Not implemented
There is no LLM integration, no persistent storage, no authentication, no background job queue and no retrieval/knowledge features. Possible next steps: put a real tool or LLM call behind each agent, persist tasks and reports, and add authentication.
