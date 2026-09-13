"""Verification result dataclasses for the Healthcare Environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CheckResult:
    """Outcome of an individual evaluation check."""
    name: str
    passed: bool
    score: float
    max_score: float
    details: str = ""
    is_veto: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Composite verification outcome across all safety and task layers."""
    success: bool
    score: float
    max_score: float
    checks: List[CheckResult] = field(default_factory=list)
    penalties: float = 0.0
    vetoed: bool = False
    feedback: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        if self.vetoed or self.max_score <= 0:
            return 0.0
        return max(0.0, min(1.0, self.score / self.max_score))

    @property
    def final_score(self) -> float:
        return self.score


    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "score": round(self.score, 4),
            "max_score": round(self.max_score, 4),
            "percentage": round(self.percentage, 4),
            "vetoed": self.vetoed,
            "penalties": round(self.penalties, 4),
            "feedback": self.feedback,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "score": round(c.score, 4),
                    "max_score": round(c.max_score, 4),
                    "is_veto": c.is_veto,
                    "details": c.details,
                    "evidence": c.evidence,
                }
                for c in self.checks
            ],
            "metadata": self.metadata,
        }
