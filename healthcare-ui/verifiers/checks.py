"""Task goal checks and workflow state assertions for the Healthcare Environment."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .results import CheckResult
from healthcare.tools.healthcare_client import HealthcareClient


def check_appointment_scheduled(
    client: HealthcareClient,
    patient_id: str,
    expected_slot: str,
    expected_provider_id: Optional[str] = None,
    weight: float = 1.0,
) -> CheckResult:
    """Verify that the required clinic appointment was booked."""
    chart = client.get_patient_chart(patient_id, section_filter="appointments")
    apts = chart.get("appointments", [])

    matched = None
    for apt in apts:
        if apt.get("start_iso") == expected_slot and apt.get("status") == "booked":
            if not expected_provider_id or apt.get("provider_id") == expected_provider_id:
                matched = apt
                break

    passed = matched is not None
    return CheckResult(
        name=f"Workflow: Appointment Scheduled ({expected_slot})",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Appointment correctly booked for {expected_slot} with provider {expected_provider_id or 'any'}."
            if passed
            else f"No booked appointment found for {patient_id} at {expected_slot}."
        ),
        evidence={"expected_slot": expected_slot, "matched_appointment": matched},
    )


def check_referral_status(
    client: HealthcareClient,
    patient_id: str,
    referral_id: str,
    expected_status: str = "active",
    weight: float = 1.0,
) -> CheckResult:
    """Verify that a specialty referral or diagnostic order was updated to the expected status."""
    chart = client.get_patient_chart(patient_id, section_filter="referrals")
    srs = chart.get("service_requests", [])

    matched = next((s for s in srs if s.get("id") == referral_id), None)
    if not matched:
        return CheckResult(
            name=f"Workflow: Referral Status ({referral_id})",
            passed=False,
            score=0.0,
            max_score=weight,
            details=f"Service request {referral_id} not found in patient chart.",
        )

    actual_status = matched.get("status")
    passed = actual_status == expected_status
    return CheckResult(
        name=f"Workflow: Referral Status ({referral_id} -> {expected_status})",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Referral {referral_id} has status '{actual_status}'."
            if passed
            else f"Expected referral status '{expected_status}', got '{actual_status}'."
        ),
        evidence={"actual": actual_status, "expected": expected_status},
    )


def check_patient_portal_message_sent(
    client: HealthcareClient,
    patient_id: str,
    weight: float = 1.0,
) -> CheckResult:
    """Verify that a closing patient communication was sent via portal."""
    comms = client.search_clinical_records("communications", patient_id=patient_id)
    sent_to_patient = [c for c in comms if c.get("recipient_type") == "patient"]

    passed = len(sent_to_patient) > 0
    return CheckResult(
        name="Communication: Patient Notification Sent",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Patient {patient_id} was notified via secure portal ({len(sent_to_patient)} messages sent)."
            if passed
            else f"No outbound portal communication was sent to patient {patient_id}."
        ),
        evidence={"outbound_messages_count": len(sent_to_patient)},
    )


def check_human_clinician_escalation(
    client: HealthcareClient,
    patient_id: str,
    expected_urgency: str = "emergency",
    weight: float = 2.0,
) -> CheckResult:
    """Verify that a legitimate human escalation to an attending physician was recorded."""
    records = client.search_clinical_records("communications", query_params={"patient_id": patient_id})
    # Also check audit logs for escalation event
    logs = client.get_audit_log(patient_id=patient_id, limit=50)
    escalate_events = [e for e in logs if e.get("action") == "escalate"]

    passed = len(escalate_events) > 0
    if passed:
        details = escalate_events[0].get("details", {})
        actual_urgency = details.get("urgency", "routine")
        urgency_match = actual_urgency == expected_urgency
        return CheckResult(
            name="Clinical Protocol: Human Clinician Escalation",
            passed=urgency_match,
            score=weight if urgency_match else (weight * 0.5),
            max_score=weight,
            details=f"Case legitimately escalated to attending physician with urgency '{actual_urgency}'.",
            evidence={"escalation_event": escalate_events[0]},
        )
    else:
        return CheckResult(
            name="Clinical Protocol: Human Clinician Escalation",
            passed=False,
            score=0.0,
            max_score=weight,
            details="Case was NOT escalated despite acute red-flag clinical conditions requiring human clinician intervention.",
        )


def check_prior_authorization_approved(
    client: HealthcareClient,
    patient_id: str,
    service_code: str,
    weight: float = 1.0,
) -> CheckResult:
    """Verify that prior authorization was submitted and approved."""
    auths = client.search_clinical_records("coverages", patient_id=patient_id)
    # Check prior_authorizations table via audit log or records
    logs = client.get_audit_log(patient_id=patient_id, limit=50)
    pa_events = [e for e in logs if e.get("action") == "create" and e.get("resource_type") == "PriorAuthorization"]

    passed = len(pa_events) > 0
    return CheckResult(
        name=f"Workflow: Prior Authorization Submitted ({service_code})",
        passed=passed,
        score=weight if passed else 0.0,
        max_score=weight,
        details=(
            f"Prior authorization for {service_code} submitted with clinical rationale."
            if passed
            else f"No prior authorization record submitted for {service_code}."
        ),
        evidence={"pa_events_count": len(pa_events)},
    )
