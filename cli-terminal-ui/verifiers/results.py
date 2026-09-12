"""Result types for terminal verifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    name: str
    passed: bool
    detail: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    reward: float
    success: float
    valid: float
    base_reward: float
    audit_pass: float
    audit_findings: int
    findings_detail: list[str]
    layer_milestones: float
    layer_weight_milestones: float
    layer_final_state: float
    layer_weight_final_state: float
    layer_cleanliness: float
    layer_weight_cleanliness: float
    checks: list[CheckOutcome]
    milestones_detail: dict[str, bool] = field(default_factory=dict)
