"""Layered evaluation engine for browser verifier."""

from __future__ import annotations

from typing import Any
from verifiers.checks import evaluate_browser_checks
from verifiers.results import EvaluationResult


def evaluate_episode(
    client: Any | None = None,
    state_data: dict[str, Any] | None = None,
) -> EvaluationResult:
    eval_dict, checks = evaluate_browser_checks(client=client, state_data=state_data)
    if not eval_dict:
        return EvaluationResult(
            reward=0.0,
            success=0.0,
            valid=0.0,
            base_reward=0.0,
            audit_pass=0.0,
            audit_findings=1,
            findings_detail=["state_unfetchable"],
            layer_milestones=0.0,
            layer_weight_milestones=0.3,
            layer_final_state=0.0,
            layer_weight_final_state=0.4,
            layer_cleanliness=0.0,
            layer_weight_cleanliness=0.3,
            checks=checks,
        )

    return EvaluationResult(
        reward=float(eval_dict.get("reward", 0.0)),
        success=float(eval_dict.get("success", 0.0)),
        valid=float(eval_dict.get("valid", 1.0)),
        base_reward=float(eval_dict.get("base_reward", 0.0)),
        audit_pass=float(eval_dict.get("audit_pass", 1.0)),
        audit_findings=int(eval_dict.get("audit_findings", 0)),
        findings_detail=list(eval_dict.get("findings_detail", [])),
        layer_milestones=float(eval_dict.get("layer_milestones", 0.0)),
        layer_weight_milestones=float(eval_dict.get("layer_weight_milestones", 0.3)),
        layer_final_state=float(eval_dict.get("layer_final_state", 0.0)),
        layer_weight_final_state=float(eval_dict.get("layer_weight_final_state", 0.4)),
        layer_cleanliness=float(eval_dict.get("layer_cleanliness", 1.0)),
        layer_weight_cleanliness=float(eval_dict.get("layer_weight_cleanliness", 0.3)),
        checks=checks,
        milestones_detail=eval_dict.get("milestones_detail", {}),
    )
