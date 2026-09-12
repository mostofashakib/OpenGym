"""Auditor entrypoint for browser verifier."""

from __future__ import annotations

from typing import Any
from verifiers.layered import evaluate_episode


def run_audit(state_data: dict[str, Any] | None = None) -> dict[str, Any]:
    res = evaluate_episode(state_data=state_data)
    return {
        "reward": res.reward,
        "success": res.success,
        "valid": res.valid,
        "findings": res.findings_detail,
        "milestones": res.milestones_detail,
    }
