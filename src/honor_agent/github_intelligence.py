"""GitHub repository intelligence utilities."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import httpx

from .models import GitHubRepoInsight

GITHUB_REPO_RE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)?"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


@dataclass(frozen=True)
class GitHubRepoRef:
    owner: str
    repo: str

    @property
    def url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}"


def parse_github_repo_url(value: str) -> GitHubRepoRef:
    """Parse common GitHub repository URL formats."""
    match = GITHUB_REPO_RE.match(value.strip())
    if not match:
        raise ValueError("Expected a GitHub repository URL, for example https://github.com/owner/repo")
    return GitHubRepoRef(owner=match.group("owner"), repo=match.group("repo"))


async def fetch_github_repo_metadata(ref: GitHubRepoRef) -> dict[str, Any]:
    """Fetch public or token-authorized repository metadata from the GitHub API."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "honor-agent/0.1",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        repo_response = await client.get(f"https://api.github.com/repos/{ref.owner}/{ref.repo}")
        repo_response.raise_for_status()
        repo_data = repo_response.json()

        branches_response = await client.get(
            f"https://api.github.com/repos/{ref.owner}/{ref.repo}/branches",
            params={"per_page": 100},
        )
        branches = branches_response.json() if branches_response.status_code == 200 else []

    return {
        "full_name": repo_data.get("full_name"),
        "description": repo_data.get("description"),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "default_branch": repo_data.get("default_branch"),
        "license": (repo_data.get("license") or {}).get("spdx_id"),
        "topics": repo_data.get("topics") or [],
        "archived": repo_data.get("archived", False),
        "pushed_at": repo_data.get("pushed_at"),
        "branch_count": len(branches) if isinstance(branches, list) else None,
    }


def build_repo_insight(ref: GitHubRepoRef, metadata: dict[str, Any] | None = None) -> GitHubRepoInsight:
    """Create a repo health score and task suggestions from available metadata."""
    metadata = metadata or {}
    score = 50
    signals: list[str] = []
    risks: list[str] = []
    tasks: list[str] = []

    if metadata.get("description"):
        score += 8
        signals.append("Repository has a project description.")
    else:
        risks.append("Missing GitHub repository description.")
        tasks.append("Add a concise repository description and topic tags.")

    if metadata.get("license"):
        score += 10
        signals.append(f"License detected: {metadata['license']}.")
    else:
        risks.append("No license detected from GitHub metadata.")
        tasks.append("Add a LICENSE file and verify GitHub detects it.")

    stars = int(metadata.get("stars") or 0)
    forks = int(metadata.get("forks") or 0)
    if stars >= 50:
        score += 10
        signals.append("Repository has visible community traction.")
    elif stars > 0:
        score += 4
        signals.append("Repository has early community interest.")
    else:
        tasks.append("Create a demo, screenshots, or quickstart to improve discoverability.")

    if forks:
        score += 4

    if metadata.get("topics"):
        score += 6
        signals.append("Repository has GitHub topics for discovery.")
    else:
        tasks.append("Add GitHub topics such as ai-agent, automation, fastapi, multi-agent.")

    open_issues = int(metadata.get("open_issues") or 0)
    if open_issues > 25:
        risks.append("High open issue count may indicate maintenance backlog.")
        tasks.append("Triage open issues into bug, enhancement, and good-first-issue labels.")
    elif open_issues:
        signals.append("Open issues exist and can be converted into agent tasks.")

    if metadata.get("archived"):
        score -= 40
        risks.append("Repository is archived.")

    if not metadata:
        risks.append("Remote metadata was not fetched; score is based on URL only.")
        tasks.append("Run analysis with include_remote=true and GITHUB_TOKEN for private repositories.")

    tasks.extend(
        [
            "Generate a repository health report before each release.",
            "Convert high-value GitHub issues into HonorAgent tasks.",
            "Run CI, lint, and tests before opening a pull request.",
        ]
    )

    return GitHubRepoInsight(
        owner=ref.owner,
        repo=ref.repo,
        url=ref.url,
        health_score=max(0, min(score, 100)),
        signals=signals,
        risks=risks,
        suggested_tasks=tasks,
        metadata=metadata,
    )
