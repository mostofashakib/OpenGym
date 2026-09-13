"""State checks and assertions for the Software Environment verifier."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .results import CheckResult
from software.tools.software_client import SoftwareClient


def check_target_entity_state(
    client: SoftwareClient,
    entity_name: str,
    entity_id: str,
    expected_state: str,
    weight: float = 1.0,
) -> CheckResult:
    """Verify that the specified entity transitioned to the expected workflow status."""
    record = client.get(entity_name=entity_name, entity_id=entity_id)
    if record is None:
        return CheckResult(
            name=f"Entity Existence: {entity_name}[{entity_id}]",
            passed=False,
            score=0.0,
            max_score=weight,
            details=f"Entity record {entity_id} was not found in table for {entity_name}.",
            evidence={"entity_name": entity_name, "entity_id": entity_id},
        )

    current_state = record.get("status")
    passed = current_state == expected_state
    return CheckResult(
        name=f"Entity State: {entity_name}[{entity_id}] -> {expected_state}",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Entity {entity_id} status is '{current_state}'."
            if passed
            else f"Expected status '{expected_state}', but got '{current_state}'."
        ),
        evidence={
            "entity_name": entity_name,
            "entity_id": entity_id,
            "actual_state": current_state,
            "expected_state": expected_state,
        },
    )


def check_field_values(
    client: SoftwareClient,
    entity_name: str,
    entity_id: str,
    expected_fields: Dict[str, Any],
    weight: float = 1.0,
) -> CheckResult:
    """Verify specific field values on an entity record."""
    record = client.get(entity_name=entity_name, entity_id=entity_id)
    if record is None:
        return CheckResult(
            name=f"Fields Check: {entity_name}[{entity_id}]",
            passed=False,
            score=0.0,
            max_score=weight,
            details=f"Entity {entity_id} not found.",
        )

    mismatches: List[str] = []
    for k, v in expected_fields.items():
        actual = record.get(k)
        if actual != v:
            mismatches.append(f"{k}: expected {v!r}, got {actual!r}")

    passed = len(mismatches) == 0
    return CheckResult(
        name=f"Field Values: {entity_name}[{entity_id}]",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details="All fields matched." if passed else f"Mismatches: {'; '.join(mismatches)}",
        evidence={"expected": expected_fields, "record": record},
    )


def check_created_entity(
    client: SoftwareClient,
    entity_name: str,
    required_field_matches: Dict[str, Any],
    weight: float = 1.0,
) -> CheckResult:
    """Verify that a new record was created matching specified criteria."""
    records = client.search(entity_name=entity_name, limit=200)
    matched_id = None
    for r in records:
        match = True
        for k, v in required_field_matches.items():
            if r.get(k) != v:
                match = False
                break
        if match:
            matched_id = r.get("id")
            break

    passed = matched_id is not None
    return CheckResult(
        name=f"Entity Creation: {entity_name}",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Found matching created entity with ID {matched_id}."
            if passed
            else "No record matching criteria found in database."
        ),
        evidence={"criteria": required_field_matches, "matched_id": matched_id},
    )
