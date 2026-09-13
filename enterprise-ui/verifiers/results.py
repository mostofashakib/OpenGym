"""Verification result models for the Enterprise Simulation Platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CheckResult:
    """Outcome of an individual task goal or policy check."""
    name: str
    passed: bool
    score: float
    max_score: float
    details: str = ""
    is_veto: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Composite verification outcome across task goals and enterprise policy compliance."""
    success: bool
    business_score: float
    policy_score: float
    final_score: float
    max_score: float
    checks: List[CheckResult] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)
    vetoed: bool = False
    feedback: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        if self.vetoed or self.max_score <= 0:
            return 0.0
        return max(0.0, min(1.0, self.final_score / self.max_score))

    @property
    def score(self) -> float:
        return self.final_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "business_score": round(self.business_score, 4),
            "policy_score": round(self.policy_score, 4),
            "final_score": round(self.final_score, 4),
            "max_score": round(self.max_score, 4),
            "percentage": round(self.percentage, 4),
            "vetoed": self.vetoed,
            "policy_violations_count": len(self.policy_violations),
            "feedback": self.feedback,
            "metadata": self.metadata,
        }
