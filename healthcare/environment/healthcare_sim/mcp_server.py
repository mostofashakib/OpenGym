"""FastMCP server exposing healthcare simulation tools over stdio."""

from __future__ import annotations

import json
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .context import HealthcareContext

mcp = FastMCP("healthcare-environment")

_DB_PATH = os.environ.get("HEALTHCARE_DB", "/tmp/healthcare_sim.db")
_context = HealthcareContext(db_path=_DB_PATH)


@mcp.tool()
def verify_patient_identity(
    patient_id: str,
    first_name: str = "",
    last_name: str = "",
    birth_date: str = "",
    mrn: str = "",
) -> str:
    """Verify patient demographic identifiers before accessing sensitive chart data or issuing orders."""
    res = _context.service.verify_patient_identity(
        patient_id=patient_id,
        first_name=first_name if first_name else None,
        last_name=last_name if last_name else None,
        birth_date=birth_date if birth_date else None,
        mrn=mrn if mrn else None,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def get_patient_chart(patient_id: str, section_filter: str = "") -> str:
    """Retrieve longitudinal patient chart records (conditions, medications, allergies, observations, etc.)."""
    res = _context.service.get_patient_chart(
        patient_id=patient_id,
        section_filter=section_filter if section_filter else None,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def search_clinical_records(resource_type: str, patient_id: str = "", query_json: str = "{}") -> str:
    """Query records across clinical tables."""
    try:
        query_params = json.loads(query_json) if query_json else None
    except Exception as exc:
        return json.dumps({"error": f"Invalid query_json: {exc}"})

    res = _context.service.search_clinical_records(
        resource_type=resource_type,
        patient_id=patient_id if patient_id else None,
        query_params=query_params,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def create_clinical_order(order_type: str, patient_id: str, details_json: str) -> str:
    """Create a medication prescription, lab diagnostic order, or specialty referral."""
    try:
        details = json.loads(details_json)
    except Exception as exc:
        return json.dumps({"error": f"Invalid details_json: {exc}"})

    res = _context.service.create_clinical_order(
        order_type=order_type,
        patient_id=patient_id,
        details=details,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def update_order_or_referral(order_id: str, status: str, notes: str = "") -> str:
    """Update status or clinical notes on an existing service request or referral."""
    res = _context.service.update_order_or_referral(
        order_id=order_id,
        status=status,
        notes=notes,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def schedule_appointment(
    patient_id: str,
    provider_id: str,
    facility_id: str,
    slot_iso: str,
    visit_type: str = "consultation",
    notes: str = "",
) -> str:
    """Book a clinic appointment slot with a provider."""
    res = _context.service.schedule_appointment(
        patient_id=patient_id,
        provider_id=provider_id,
        facility_id=facility_id,
        slot_iso=slot_iso,
        visit_type=visit_type,
        notes=notes,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def send_portal_message(
    recipient_type: str,
    recipient_id: str,
    patient_id: str,
    subject: str,
    body: str,
) -> str:
    """Send secure message via patient portal or staff messaging."""
    res = _context.service.send_portal_message(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        patient_id=patient_id,
        subject=subject,
        body=body,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def submit_prior_authorization(
    patient_id: str,
    service_code: str,
    payer_id: str,
    clinical_rationale: str,
) -> str:
    """Submit prior authorization request to insurance payer."""
    res = _context.service.submit_prior_authorization(
        patient_id=patient_id,
        service_code=service_code,
        payer_id=payer_id,
        clinical_rationale=clinical_rationale,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def escalate_to_human_clinician(
    patient_id: str,
    urgency: str,
    clinical_summary: str,
    required_action: str,
) -> str:
    """Legitimately hand off a case to an attending physician when clinical safety thresholds are crossed."""
    res = _context.service.escalate_to_human_clinician(
        patient_id=patient_id,
        urgency=urgency,
        clinical_summary=clinical_summary,
        required_action=required_action,
        actor_id=_context.actor_id,
        actor_role=_context.actor_role,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def get_audit_log(patient_id: str = "", limit: int = 50) -> str:
    """Retrieve audit log events."""
    res = _context.service.get_audit_log(
        patient_id=patient_id if patient_id else None,
        limit=limit,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def submit_task(summary: str, patient_id: str = "") -> str:
    """Submit completion report for the clinical coordination episode."""
    return json.dumps({
        "submitted": True,
        "summary": summary,
        "patient_id": patient_id,
        "status": "completed",
    }, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
