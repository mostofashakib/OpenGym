"""Verification result types for the Software Environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CheckResult:
    """Result of an individual check or predicate assertion."""
    name: str
    passed: bool
    score: float
    max_score: float
    details: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Overall evaluation result across layered verifier checks."""
    success: bool
    score: float
    max_score: float
    checks: List[CheckResult] = field(default_factory=list)
    penalties: float = 0.0
    feedback: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def percentage(self) -> float:
        if self.max_score <= 0:
            return 0.0
        return max(0.0, min(1.0, self.score / self.max_score))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "score": round(self.score, 4),
            "max_score": round(self.max_score, 4),
            "percentage": round(self.percentage, 4),
            "penalties": round(self.penalties, 4),
            "feedback": self.feedback,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "score": round(c.score, 4),
                    "max_score": round(c.max_score, 4),
                    "details": c.details,
                    "evidence": c.evidence,
                }
                for c in self.checks
            ],
            "metadata": self.metadata,
        }
