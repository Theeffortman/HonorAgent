> **Note:** the source code lives on the `codex/android-apk-package` branch (the default branch). This `main` branch contains documentation and examples only.

# Running and Deployment

HonorAgent is a prototype intended for local use and demos. It has no database, so all tasks and results are lost when the process stops, and it does not enforce authentication. Do not expose it publicly as-is.

## Local (Python 3.10+)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
honor-agent            # serves on http://0.0.0.0:8000
curl http://localhost:8000/health
```

Open `http://localhost:8000/` for the web UI and `/docs` for the API docs.

## Docker

The `Dockerfile` uses `python:3.11-slim`, installs the package and runs `honor-agent` on port 8000.

```bash
docker build -t honor-agent .
docker run -p 8000:8000 honor-agent
```

## Docker Compose

`docker-compose.yml` defines a single `api` service (no database or cache services). It reads environment variables from `.env`, so create it first:

```bash
cp .env.example .env
docker compose up --build
```

## Environment variables

| Variable | Used by | Purpose |
|----------|---------|---------|
| `GITHUB_TOKEN` | server | Optional; sent to the GitHub API by `/api/v1/github/analyze` |
| `HONOR_API_KEY`, `HONOR_BASE_URL` | examples / client | Values for the Python client examples |

`.env.example` also contains `OPENAI_API_KEY`, `SECRET_KEY` and `JWT_SECRET` placeholders; the current code does not read them.

## Continuous integration

`.github/workflows/` contains two GitHub Actions workflows, both triggered on push and pull request:

- **CI** (`ci.yml`): Python 3.11, `pip install -e ".[dev]"`, `ruff check .`, `pytest`.
- **Android APK** (`android.yml`, also manual dispatch): JDK 17 + Gradle 8.10.2, `gradle :app:assembleDebug`, uploads the `honor-agent-debug-apk` artifact.

## Android

See [ANDROID.md](ANDROID.md). The APK is a client only; run the API separately and point the app at its URL.
