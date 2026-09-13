"""Audit trail verifier for the Software Environment.

Examines the audit log to verify the sequence of actions and state transitions,
ensuring legitimate execution according to domain lifecycle rules.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .results import CheckResult
from software.tools.software_client import SoftwareClient


def audit_transition_history(
    client: SoftwareClient,
    entity_id: str,
    expected_transitions: Optional[List[str]] = None,
    weight: float = 1.0,
) -> CheckResult:
    """Audit the action log for a given entity to verify correct transition history."""
    logs = client.get_audit_trail(entity_id=entity_id, limit=50)

    # Filter for successful transitions
    transitions = [
        entry for entry in logs
        if entry.get("entity_id") == entity_id and entry.get("to_state") is not None
    ]

    if not transitions:
        return CheckResult(
            name=f"Audit Trail: {entity_id}",
            passed=False,
            score=0.0,
            max_score=weight,
            details=f"No transition logs found for entity {entity_id}.",
            evidence={"logs_count": len(logs)},
        )

    # If expected sequence was specified, verify it
    if expected_transitions:
        actual_actions = [t.get("action") for t in transitions]
        # Check if expected actions occurred in order
        curr_idx = 0
        for act in actual_actions:
            if curr_idx < len(expected_transitions) and act == expected_transitions[curr_idx]:
                curr_idx += 1

        passed = curr_idx == len(expected_transitions)
        return CheckResult(
            name=f"Audit Sequence: {entity_id}",
            passed=passed,
            score=weight if passed else 0.5,
            max_score=weight,
            details=(
                f"Action sequence matched: {expected_transitions}"
                if passed
                else f"Expected action sequence {expected_transitions}, but observed {actual_actions}."
            ),
            evidence={"actual_actions": actual_actions, "expected": expected_transitions},
        )

    return CheckResult(
        name=f"Audit Trail: {entity_id}",
        passed=True,
        score=weight,
        max_score=weight,
        details=f"Verified {len(transitions)} transitions recorded in system audit trail.",
        evidence={"transition_count": len(transitions)},
    )


def audit_no_prohibited_actions(
    client: SoftwareClient,
    prohibited_actions: List[str],
    weight: float = 0.5,
) -> CheckResult:
    """Ensure no prohibited or illegal actions were recorded in the audit log."""
    logs = client.get_audit_trail(limit=200)
    violations = [
        entry for entry in logs
        if entry.get("action") in prohibited_actions
    ]

    passed = len(violations) == 0
    return CheckResult(
        name="Audit: Prohibited Actions Check",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            "No prohibited actions detected in audit log."
            if passed
            else f"Prohibited actions detected: {[v.get('action') for v in violations]}"
        ),
        evidence={"violation_count": len(violations)},
    )
