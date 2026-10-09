import pytest

from honor_agent.github_intelligence import build_repo_insight, parse_github_repo_url


def test_parse_github_repo_url_variants() -> None:
    assert parse_github_repo_url("https://github.com/owner/repo").owner == "owner"
    assert parse_github_repo_url("git@github.com:owner/repo.git").repo == "repo"


def test_parse_github_repo_url_rejects_non_github() -> None:
    with pytest.raises(ValueError):
        parse_github_repo_url("https://example.com/owner/repo")


def test_build_repo_insight_scores_metadata() -> None:
    ref = parse_github_repo_url("https://github.com/owner/repo")
    insight = build_repo_insight(
        ref,
        {
            "description": "A useful project",
            "license": "MIT",
            "stars": 100,
            "forks": 8,
            "topics": ["ai-agent"],
            "open_issues": 2,
        },
    )

    assert insight.health_score > 80
    assert any("License" in signal for signal in insight.signals)
