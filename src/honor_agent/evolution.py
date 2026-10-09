"""Post-run evaluation and improvement planning for agent orchestration."""

from __future__ import annotations

from .models import AgentEvolution, AgentRun, EvolutionReport, OrchestrationResult


def _score_agent_run(run: AgentRun) -> int:
    score = 50
    if run.status == "completed":
        score += 25
    if run.output.get("summary"):
        score += 10
    if run.output.get("handoff"):
        score += 10
    if run.input_summary:
        score += 5
    if run.status == "skipped":
        score -= 35
    return max(0, min(100, score))


def _agent_report(run: AgentRun) -> AgentEvolution:
    strengths: list[str] = []
    risks: list[str] = []
    actions: list[str] = []

    if run.status == "completed":
        strengths.append("Agent completed its assigned step.")
    else:
        risks.append("Agent did not execute successfully.")
        actions.append(f"Register or repair agent '{run.agent_id}' before using this workflow.")

    if run.output.get("summary"):
        strengths.append("Agent produced a concise summary.")
    else:
        risks.append("Agent output is missing a summary.")
        actions.append("Require every agent to return a summary field.")

    if run.output.get("handoff"):
        strengths.append("Agent provided a handoff instruction for downstream context.")
    else:
        risks.append("Agent output is missing handoff guidance.")
        actions.append("Add explicit handoff guidance to the agent output contract.")

    return AgentEvolution(
        agent_id=run.agent_id,
        score=_score_agent_run(run),
        strengths=strengths,
        risks=risks,
        improvement_actions=actions,
    )


def build_evolution_report(result: OrchestrationResult) -> EvolutionReport:
    """Create a deterministic self-improvement report from a completed run."""

    agent_reports = [_agent_report(run) for run in result.runs]
    if agent_reports:
        overall_score = round(sum(report.score for report in agent_reports) / len(agent_reports))
    else:
        overall_score = 0

    strengths: list[str] = []
    risks: list[str] = []
    actions: list[str] = []

    completed_count = len([run for run in result.runs if run.status == "completed"])
    skipped_count = len([run for run in result.runs if run.status == "skipped"])
    handoff_count = len(result.final_output.get("handoffs", []))

    if completed_count:
        strengths.append(f"{completed_count} agent step(s) completed.")
    if handoff_count >= max(0, len(result.runs) - 1):
        strengths.append("Context handoff trace is available for the workflow.")
    if result.final_output.get("latest_output"):
        strengths.append("Final agent output is captured for downstream use.")

    if skipped_count:
        risks.append(f"{skipped_count} agent step(s) were skipped.")
        actions.append("Review task agent IDs and keep them aligned with the registered agent list.")
    if not result.runs:
        risks.append("No agent runs were recorded.")
        actions.append("Create tasks with at least one registered agent.")
    if handoff_count < len(result.runs):
        risks.append("Handoff trace is incomplete.")
        actions.append("Preserve every agent input and output in the orchestration result.")

    actions.extend(
        [
            "Promote frequently successful agent sequences into reusable workflow templates.",
            "Add real tool or LLM execution behind each deterministic agent function.",
            "Persist task runs and evolution reports before enabling production workloads.",
        ]
    )

    if overall_score >= 85:
        readiness = "strong"
    elif overall_score >= 65:
        readiness = "usable"
    else:
        readiness = "needs_attention"

    return EvolutionReport(
        task_id=result.task_id,
        overall_score=overall_score,
        readiness=readiness,
        strengths=strengths,
        risks=risks,
        recommended_next_actions=actions,
        agent_reports=agent_reports,
    )
