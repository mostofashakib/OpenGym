"""Layered verifier orchestrator for the Software Environment."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auditor import audit_transition_history
from .checks import check_field_values, check_target_entity_state
from .results import CheckResult, VerificationResult
from software.tools.software_client import SoftwareClient


class LayeredVerifier:
    """Orchestrates multi-layer verification of software application tasks."""

    def __init__(self, client: SoftwareClient) -> None:
        self.client = client

    def verify(self, task_spec: Dict[str, Any]) -> VerificationResult:
        """Run all verification layers for the given task specification."""
        checks: List[CheckResult] = []
        penalties: float = 0.0

        assertions = task_spec.get("assertions", {})
        entity_name = assertions.get("entity_name") or task_spec.get("target_entity")
        entity_id = assertions.get("entity_id") or task_spec.get("target_entity_id")
        expected_state = assertions.get("expected_state") or task_spec.get("target_state")

        # Layer 1: Core Target State Check (Weight 2.0)
        if entity_name and entity_id and expected_state:
            state_check = check_target_entity_state(
                client=self.client,
                entity_name=entity_name,
                entity_id=entity_id,
                expected_state=expected_state,
                weight=2.0,
            )
            checks.append(state_check)

        # Layer 2: Field Assertions Check (Weight 1.0)
        expected_fields = assertions.get("expected_fields")
        if entity_name and entity_id and expected_fields:
            field_check = check_field_values(
                client=self.client,
                entity_name=entity_name,
                entity_id=entity_id,
                expected_fields=expected_fields,
                weight=1.0,
            )
            checks.append(field_check)

        # Layer 3: Audit Trail Verification (Weight 1.0)
        oracle_traj = task_spec.get("oracle_trajectory", [])
        expected_actions = [
            step.get("action") for step in oracle_traj
            if "action" in step and (step.get("id") == entity_id or not step.get("id"))
        ]
        if entity_id:
            audit_check = audit_transition_history(
                client=self.client,
                entity_id=entity_id,
                expected_transitions=expected_actions if expected_actions else None,
                weight=1.0,
            )
            checks.append(audit_check)

        # Calculate total score
        total_score = sum(c.score for c in checks) - penalties
        total_max_score = sum(c.max_score for c in checks)
        success = all(c.passed for c in checks) if checks else False

        feedback_parts = [
            f"[{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.details}"
            for c in checks
        ]
        feedback = "\n".join(feedback_parts)

        return VerificationResult(
            success=success,
            score=max(0.0, total_score),
            max_score=max(1.0, total_max_score),
            checks=checks,
            penalties=penalties,
            feedback=feedback,
            metadata={
                "task_id": task_spec.get("task_id"),
                "task_type": task_spec.get("task_type"),
                "domain": self.client.app_spec.domain,
                "current_state_hash": self.client.calculate_state_hash(),
            },
        )
