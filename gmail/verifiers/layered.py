"""Layered verification engine for Gmail agent evaluation."""

from __future__ import annotations

from typing import Any

from tools.gmail_client import GmailClient
from verifiers.auditor import audit_run
from verifiers.checks import evaluate_triage_task
from verifiers.results import (
    CheckOutcome,
    EpisodeEvaluation,
    LayerBreakdown,
    LayerScore,
)


def evaluate_episode(
    client: GmailClient | None = None,
    events: list[dict[str, Any]] | None = None,
    state_data: dict[str, Any] | None = None,
) -> EpisodeEvaluation:
    checks = evaluate_triage_task(client, state_data=state_data)
    penalties = audit_run(events)

    total_weight = sum(c.weight for c in checks) or 1.0
    passed_weight = sum(c.weight for c in checks if c.passed)

    base_score = passed_weight / total_weight
    penalty_total = sum(p.amount for p in penalties)
    final_reward = max(0.0, min(1.0, base_score - penalty_total))

    # Breakdown by layers: task_actions, final_state, cleanliness
    task_action_checks = [c for c in checks if "flagged" in c.name or "draft" in c.name]
    final_state_checks = [c for c in checks if "archived" in c.name]
    cleanliness_checks = [c for c in checks if "clean" in c.name]

    def _layer_score(name: str, layer_checks: list[CheckOutcome], weight: float) -> LayerScore:
        if not layer_checks:
            return LayerScore(layer=name, score=1.0, weight=weight, available=True)
        lw = sum(c.weight for c in layer_checks) or 1.0
        pw = sum(c.weight for c in layer_checks if c.passed)
        return LayerScore(layer=name, score=pw / lw, weight=weight, available=True)

    layers = (
        _layer_score("task_actions", task_action_checks, 0.5),
        _layer_score("final_state", final_state_checks, 0.3),
        _layer_score("cleanliness", cleanliness_checks, 0.2),
    )

    breakdown = LayerBreakdown(
        base=base_score,
        penalty_total=penalty_total,
        layers=layers,
    )

    all_passed = all(c.passed for c in checks) and len(penalties) == 0

    return EpisodeEvaluation(
        reward=final_reward,
        passed=all_passed,
        valid=True,
        breakdown=breakdown,
        checks=tuple(checks),
        penalties=penalties,
        audit={"audited_pass": len(penalties) == 0, "findings": [p.as_dict() for p in penalties]},
    )
