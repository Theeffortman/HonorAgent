"""Deterministic multi-agent orchestration for the MVP server."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .evolution import build_evolution_report
from .models import AgentInfo, AgentRun, OrchestrationResult, Task


def _params_to_dict(params: Any) -> dict[str, Any]:
    if hasattr(params, "model_dump"):
        return params.model_dump(mode="json")
    if isinstance(params, dict):
        return params
    return {}


def _summarize_context(context: dict[str, Any]) -> str:
    latest = context.get("latest_output")
    if not latest:
        return "No previous agent output; using original task context."
    agent_id = latest.get("agent_id", "previous_agent")
    summary = latest.get("summary") or latest.get("recommendation") or latest.get("report")
    return f"Received context from {agent_id}: {summary}"


def _data_analyst(task: Task, context: dict[str, Any]) -> dict[str, Any]:
    params = _params_to_dict(task.params)
    data_source = params.get("data_source") or "unspecified source"
    date_range = params.get("date_range") or "unspecified range"
    findings = [
        f"Source '{data_source}' is ready for analysis.",
        f"Range '{date_range}' is scoped for the task.",
        f"Priority '{task.priority}' requires focused execution.",
    ]
    return {
        "summary": f"Analyzed {data_source} for {date_range}.",
        "findings": findings,
        "handoff": "Send findings to the report generator for a concise executive summary.",
        "context_seen": _summarize_context(context),
    }


def _report_generator(task: Task, context: dict[str, Any]) -> dict[str, Any]:
    latest = context.get("latest_output", {})
    findings = latest.get("findings", [])
    bullets = findings or [task.description or f"Task {task.name} has no detailed findings yet."]
    return {
        "summary": f"Generated report for '{task.name}'.",
        "report": {
            "title": task.name,
            "executive_summary": f"{len(bullets)} point(s) prepared for review.",
            "bullets": bullets,
        },
        "handoff": "Send the report to downstream planning or repository intelligence agents.",
        "context_seen": _summarize_context(context),
    }


def _github_intelligence(task: Task, context: dict[str, Any]) -> dict[str, Any]:
    params = _params_to_dict(task.params)
    repo_url = (
        params.get("github_url")
        or params.get("repo_url")
        or params.get("repository")
        or params.get("extra", {}).get("github_url")
        if isinstance(params.get("extra"), dict)
        else None
    )
    recommendations = [
        "Keep README, API docs, Android guide, and CI status aligned.",
        "Use GitHub Actions output as the release signal for APK readiness.",
        "Convert repeated maintenance suggestions into tracked issues.",
    ]
    return {
        "summary": "Prepared repository maintenance plan.",
        "repository": repo_url or "not provided",
        "recommendations": recommendations,
        "handoff": "Aggregate all agent outputs into the final task result.",
        "context_seen": _summarize_context(context),
    }


def _generic_agent(agent: AgentInfo, task: Task, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "summary": f"{agent.name} processed '{task.name}'.",
        "capabilities_used": agent.capabilities,
        "handoff": "Continue to the next agent.",
        "context_seen": _summarize_context(context),
    }


def _run_agent(agent: AgentInfo, task: Task, context: dict[str, Any]) -> dict[str, Any]:
    if agent.id == "data_analyst":
        return _data_analyst(task, context)
    if agent.id == "report_generator":
        return _report_generator(task, context)
    if agent.id == "github_intelligence":
        return _github_intelligence(task, context)
    return _generic_agent(agent, task, context)


def orchestrate_task(task: Task, available_agents: list[AgentInfo]) -> OrchestrationResult:
    """Run selected agents sequentially and preserve each handoff."""

    started_at = datetime.now(timezone.utc)
    agent_lookup = {agent.id: agent for agent in available_agents}
    selected_ids = task.agents or [available_agents[0].id]
    context: dict[str, Any] = {
        "task": {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "params": _params_to_dict(task.params),
        },
        "latest_output": None,
        "history": [],
    }
    runs: list[AgentRun] = []

    for agent_id in selected_ids:
        agent_started_at = datetime.now(timezone.utc)
        agent = agent_lookup.get(agent_id)
        if not agent:
            run = AgentRun(
                agent_id=agent_id,
                agent_name=agent_id,
                status="skipped",
                input_summary=_summarize_context(context),
                output={"summary": f"Agent '{agent_id}' is not registered."},
                started_at=agent_started_at,
                completed_at=datetime.now(timezone.utc),
            )
        else:
            output = _run_agent(agent, task, context)
            run = AgentRun(
                agent_id=agent.id,
                agent_name=agent.name,
                status="completed",
                input_summary=_summarize_context(context),
                output=output,
                started_at=agent_started_at,
                completed_at=datetime.now(timezone.utc),
            )

        runs.append(run)
        context["latest_output"] = {"agent_id": run.agent_id, **run.output}
        context["history"].append(run.model_dump(mode="json"))

    completed_runs = [run for run in runs if run.status == "completed"]
    skipped_runs = [run for run in runs if run.status == "skipped"]
    final_output = {
        "summary": (
            f"Task '{task.name}' completed by {len(completed_runs)} agent(s)"
            f" with {len(skipped_runs)} skipped agent(s)."
        ),
        "agent_sequence": [run.agent_id for run in runs],
        "handoffs": [
            {
                "from": runs[index - 1].agent_id if index > 0 else "task",
                "to": run.agent_id,
                "input_summary": run.input_summary,
                "output_summary": run.output.get("summary", ""),
            }
            for index, run in enumerate(runs)
        ],
        "latest_output": context["latest_output"],
    }

    result = OrchestrationResult(
        task_id=task.id,
        status="completed",
        agent_count=len(runs),
        runs=runs,
        final_output=final_output,
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
    )
    result.evolution = build_evolution_report(result)
    return result
