> **Note:** the source code lives on the `codex/android-apk-package` branch (the default branch). This `main` branch contains documentation and examples only.

# Changelog

## [Unreleased]
- Documentation rewritten to describe only what the code currently does.

## [0.1.0] - prototype
### Added
- FastAPI server with task CRUD, task run, result and scoring-report endpoints, agent list and GitHub repository analysis.
- Three rule-based agents: `data_analyst`, `report_generator`, `github_intelligence`.
- Sequential orchestrator that records each agent hand-off.
- Rule-based scoring ("evolution") report for each run.
- In-memory storage for tasks, results and reports.
- Static web UI, async Python client and native Android client.
- Dockerfile and API-only docker-compose.
- GitHub Actions: ruff lint + pytest, and debug APK build.

### Not yet implemented
- LLM or external tool calls inside agents.
- Persistent storage and authentication.

Development was assisted by AI tools (Codex, ChatGPT, Grok Bot, DeepSeek and MiniMax).
