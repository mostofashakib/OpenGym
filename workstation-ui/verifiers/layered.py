"""Layered verification engine for Workstation agent evaluation."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.workstation_client import WorkstationClient

from .auditor import audit_run
from .checks import evaluate_cancellation_refund_task
from .results import (
    CheckOutcome,
    EpisodeEvaluation,
    LayerBreakdown,
    LayerScore,
)


def evaluate_episode(
    client: WorkstationClient | None = None,
    events: list[dict[str, Any]] | None = None,
    state_data: dict[str, Any] | None = None,
    task_name: str | None = None,
) -> EpisodeEvaluation:
    state = state_data
    if state is None and client is not None:
        state = client.export_state()
    if state is None:
        state = {}

    checks = evaluate_cancellation_refund_task(state)

    action_logs = state.get("action_logs", [])
    penalties = audit_run(action_logs)

    total_weight = sum(c.weight for c in checks) or 1.0
    passed_weight = sum(c.weight for c in checks if c.passed)

    base_score = passed_weight / total_weight
    penalty_total = sum(p.amount for p in penalties)
    final_reward = max(0.0, min(1.0, base_score - penalty_total))

    # 4 Canonical OES-1 layers:
    final_state_checks = [c for c in checks if any(k in c.name for k in ("invoice_status", "crm_customer_status", "ticket_resolved"))]
    milestone_checks = [c for c in checks if any(k in c.name for k in ("refund_issued", "activity_logged", "email_sent", "calendar_followup"))]
    trajectory_score = 1.0 if not any("procedural" in p.reason.lower() for p in penalties) else 0.5
    
    is_veto = any("privacy violation" in p.reason.lower() for p in penalties)
    negative_score = 0.0 if is_veto else 1.0

    def _layer_score(name: str, layer_checks: list[CheckOutcome], weight: float) -> LayerScore:
        if not layer_checks:
            return LayerScore(layer=name, score=1.0, weight=weight, available=True)
        lw = sum(c.weight for c in layer_checks) or 1.0
        pw = sum(c.weight for c in layer_checks if c.passed)
        return LayerScore(layer=name, score=pw / lw, weight=weight, available=True)

    layers = (
        _layer_score("final_state", final_state_checks, 0.40),
        _layer_score("milestones", milestone_checks, 0.50),
        LayerScore(layer="trajectory", score=trajectory_score, weight=0.10, available=True),
        LayerScore(layer="negative", score=negative_score, weight=0.00, available=True),
    )

    breakdown = LayerBreakdown(
        base=base_score,
        penalty_total=penalty_total,
        layers=layers,
    )

    all_passed = all(c.passed for c in checks) and len(penalties) == 0 and not is_veto

    return EpisodeEvaluation(
        reward=final_reward,
        passed=all_passed,
        valid=True,
        breakdown=breakdown,
        checks=tuple(checks),
        penalties=penalties,
        audit={"audited_pass": len(penalties) == 0, "findings": [p.as_dict() for p in penalties]},
        is_veto=is_veto,
    )

