"""Turning a verdict into the flat reward stream Harbor stores."""

from __future__ import annotations

from .results import LAYERS, EpisodeEvaluation

HEADLINE_KEYS = (
    "reward",
    "success",
    "valid",
    "base_reward",
    "penalty_total",
    "audit_pass",
    "audit_findings",
)


def layer_keys() -> tuple[str, ...]:
    return tuple(
        key
        for layer in LAYERS
        for key in (f"layer_{layer}", f"layer_weight_{layer}", f"layer_available_{layer}")
    )


def reward_keys() -> tuple[str, ...]:
    return (*HEADLINE_KEYS, *layer_keys())


def blank_reward_dict(valid: float = 0.0) -> dict[str, float]:
    blank = {key: 0.0 for key in reward_keys()}
    blank["valid"] = float(valid)
    blank["audit_pass"] = 1.0
    return blank


def reward_dict(evaluation: EpisodeEvaluation) -> dict[str, float]:
    flat = blank_reward_dict(valid=float(evaluation.valid))
    flat.update({
        "reward": round(float(evaluation.reward), 6),
        "success": float(evaluation.passed),
        "base_reward": round(float(evaluation.breakdown.base), 6),
        "penalty_total": round(float(evaluation.breakdown.penalty_total), 6),
    })
    for layer in evaluation.breakdown.layers:
        flat[f"layer_{layer.layer}"] = round(float(layer.score), 6)
        flat[f"layer_weight_{layer.layer}"] = round(float(layer.weight), 6)
        flat[f"layer_available_{layer.layer}"] = float(layer.available)
    if evaluation.audit is not None:
        flat["audit_pass"] = float(evaluation.audit.get("audited_pass", True))
        flat["audit_findings"] = float(len(evaluation.audit.get("findings", ())))
    return flat


__all__ = ["HEADLINE_KEYS", "blank_reward_dict", "layer_keys", "reward_dict", "reward_keys"]
