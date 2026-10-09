> **Note:** the source code lives on the `codex/android-apk-package` branch (the default branch). This `main` branch contains documentation and examples only.

# Contributing

Thanks for your interest in HonorAgent. This is an early prototype, so small, focused pull requests are easiest to review.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/HonorAgent.git
cd HonorAgent
git remote add upstream https://github.com/Theeffortman/HonorAgent.git
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff check .
pytest
```

These are the same checks the CI workflow runs. If you change the Android app, also run `cd android && gradle :app:assembleDebug`.

## Guidelines

- Keep code under `src/honor_agent/` and tests under `tests/`.
- Add or update tests for behaviour you change.
- Keep the README and `docs/` accurate: only document features that exist in the code.
- Line length is 100 (see `pyproject.toml`).

## Reporting issues

Open an [issue](https://github.com/Theeffortman/HonorAgent/issues) with steps to reproduce and the expected behaviour.
