# Honor Agent

A small prototype for running a task through a chain of agents, built with FastAPI.

![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg) ![License](https://img.shields.io/badge/License-MIT-orange.svg) ![Status](https://img.shields.io/badge/status-prototype-lightgrey.svg)

> **Status: early prototype.** The agents are rule-based Python functions. The app does **not** call any LLM yet.

## What it does

- **FastAPI backend.** Create, list, run and inspect tasks over a REST API. Everything is kept **in memory**, so data is lost when the server restarts.
- **3 rule-based agents** that run one after another and pass context along:
  - `data_analyst`: summarises the task parameters
  - `report_generator`: builds a short report from the previous output
  - `github_intelligence`: summarises a GitHub repository given in the task params
- **Evaluation report.** After each run, `evolution.py` gives every agent a fixed, formula-based score (0–100) and lists suggested improvements. Nothing is learned automatically.
- **GitHub analysis.** Parses a repo URL and, if asked, fetches public metadata from the GitHub API. Setting `GITHUB_TOKEN` is optional.
- **Web dashboard.** A plain HTML/CSS/JS page served at `/`.
- **Python client SDK.** Async, built on httpx.
- **Android wrapper.** A minimal Java app that calls the backend API.

About 850 lines of Python in `src/honor_agent/`, plus pytest tests.

## Project structure

```
src/honor_agent/
  server.py               FastAPI app and endpoints
  orchestrator.py         sequential agent pipeline
  evolution.py            rule-based scoring report
  github_intelligence.py  GitHub URL parsing and metadata
  client.py, models.py    Python SDK and Pydantic models
  static/                 web dashboard
android/                  Android wrapper app (Java)
tests/                    pytest tests
.github/workflows/        CI (ruff + pytest) and Android APK build
Dockerfile, docker-compose.yml
```

## Quick start

```bash
pip install -e ".[dev]"
honor-agent            # starts uvicorn on http://0.0.0.0:8000
```

Open http://localhost:8000/ for the dashboard, or check the server is up:

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"honor-agent"}
```

### Docker

```bash
cp .env.example .env
docker compose up -d   # a single `api` service on port 8000
```

### Tests and lint

```bash
ruff check .
pytest
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/agents` | List agents |
| POST | `/api/v1/tasks` | Create a task |
| GET | `/api/v1/tasks` / `/api/v1/tasks/{id}` | List tasks / get one task |
| POST | `/api/v1/tasks/{id}/run` | Run a task |
| GET | `/api/v1/tasks/{id}/result` | Get the task result |
| GET | `/api/v1/tasks/{id}/evolution` | Get the scoring report |
| POST | `/api/v1/github/analyze` | Analyse a GitHub repository |

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "Demo", "description": "Analyse and report",
       "agents": ["data_analyst", "report_generator", "github_intelligence"],
       "params": {"extra": {"github_url": "https://github.com/Theeffortman/HonorAgent"}}}'

curl -X POST http://localhost:8000/api/v1/github/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/Theeffortman/HonorAgent", "include_remote": true}'
```

The server does not check API keys yet. The SDK sends an `Authorization` header, but the server ignores it.

## Android app

Build the APK with `cd android && gradle :app:assembleDebug`, or download the `honor-agent-debug-apk` artifact from the **Android APK** GitHub Actions workflow. Point the app at `http://10.0.2.2:8000` (emulator) or `http://<computer-lan-ip>:8000` (phone). See [docs/ANDROID.md](docs/ANDROID.md).

## CI

GitHub Actions has two workflows:
- **CI**: runs `ruff check .` and `pytest` on Python 3.11
- **Android APK**: builds a debug APK

## How it was built

This project was developed with help from AI tools (Codex, ChatGPT, Grok Bot, DeepSeek, MiniMax). The app itself does not call any LLM yet.

## Roadmap

- [ ] Real LLM integration so agents can reason over tasks
- [ ] Evaluation based on actual task outcomes instead of fixed rules
- [ ] Persistent storage (a database instead of in-memory dicts)
- [ ] API key authentication on the server
- [ ] More agents, plus parallel execution
- [ ] Bring `docs/` in line with the current code

## License

MIT
