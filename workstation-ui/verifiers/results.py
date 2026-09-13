"""The verdict shapes for Workstation task verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

LAYERS = ("final_state", "milestones", "trajectory", "negative")


@dataclass(frozen=True, slots=True)
class CheckOutcome:
    name: str
    passed: bool
    detail: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "weight": self.weight,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class Penalty:
    reason: str
    amount: float
    source: str = "auditor"

    def as_dict(self) -> dict[str, Any]:
        return {"reason": self.reason, "amount": round(self.amount, 6), "source": self.source}


@dataclass(frozen=True, slots=True)
class LayerScore:
    layer: str
    score: float
    weight: float
    available: bool = True


@dataclass(frozen=True, slots=True)
class LayerBreakdown:
    base: float
    penalty_total: float
    layers: tuple[LayerScore, ...] = ()


@dataclass(frozen=True, slots=True)
class EpisodeEvaluation:
    reward: float
    passed: bool
    valid: bool
    breakdown: LayerBreakdown
    checks: tuple[CheckOutcome, ...] = ()
    penalties: tuple[Penalty, ...] = ()
    audit: dict[str, Any] | None = None
    is_veto: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "reward": round(self.reward, 6),
            "passed": self.passed,
            "valid": self.valid,
            "is_veto": self.is_veto,
            "base_reward": round(self.breakdown.base, 6),
            "penalty_total": round(self.breakdown.penalty_total, 6),
            "checks": [c.as_dict() for c in self.checks],
            "penalties": [p.as_dict() for p in self.penalties],
            "audit": self.audit or {},
        }
