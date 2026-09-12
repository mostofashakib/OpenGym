"""Harbor reward format serializer for terminal verifier."""

from __future__ import annotations

from typing import Any
from verifiers.results import EvaluationResult


def reward_dict(eval_res: EvaluationResult) -> dict[str, Any]:
    return {
        "reward": eval_res.reward,
        "success": eval_res.success,
        "valid": eval_res.valid,
        "base_reward": eval_res.base_reward,
        "penalty_total": 0.0,
        "audit_pass": eval_res.audit_pass,
        "audit_findings": float(eval_res.audit_findings),
        "findings_detail": eval_res.findings_detail,
        "layer_milestones": eval_res.layer_milestones,
        "layer_weight_milestones": eval_res.layer_weight_milestones,
        "layer_final_state": eval_res.layer_final_state,
        "layer_weight_final_state": eval_res.layer_weight_final_state,
        "layer_cleanliness": eval_res.layer_cleanliness,
        "layer_weight_cleanliness": eval_res.layer_weight_cleanliness,
        "milestones_detail": eval_res.milestones_detail,
    }


def blank_reward_dict(valid: float = 0.0) -> dict[str, Any]:
    return {
        "reward": 0.0,
        "success": 0.0,
        "valid": valid,
        "base_reward": 0.0,
        "penalty_total": 0.0,
        "audit_pass": 1.0 if valid > 0 else 0.0,
        "audit_findings": 0.0,
    }
