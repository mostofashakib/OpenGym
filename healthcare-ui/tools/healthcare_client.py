"""High-level client for interacting with the Healthcare Simulation Environment."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.service import HealthcareService


class HealthcareClient:
    """Client for evaluating and executing actions in the healthcare environment."""

    def __init__(
        self,
        db_path: Path | str = "/tmp/healthcare_sim.db",
        actor_id: str = "prac-001",
        actor_role: str = "physician",
        context: Optional[HealthcareContext] = None,
        service: Optional[HealthcareService] = None,
    ) -> None:
        if service is not None:
            self._service = service
            self._ctx = HealthcareContext(db_path=service.db_path, actor_id=actor_id, actor_role=actor_role)
        elif context is not None:
            self._ctx = context
            self._service = self._ctx.service
        else:
            self._ctx = HealthcareContext(db_path=db_path, actor_id=actor_id, actor_role=actor_role)
            self._service = self._ctx.service


    @property
    def service(self) -> HealthcareService:
        return self._service

    @property
    def actor_id(self) -> str:
        return self._ctx.actor_id

    @property
    def actor_role(self) -> str:
        return self._ctx.actor_role

    def verify_patient_identity(
        self,
        patient_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        birth_date: Optional[str] = None,
        mrn: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify patient demographic identifiers."""
        return self._service.verify_patient_identity(
            patient_id=patient_id,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            mrn=mrn,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )

    def get_patient_chart(
        self,
        patient_id: str,
        section_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch patient chart records."""
        return self._service.get_patient_chart(
            patient_id=patient_id,
            section_filter=section_filter,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )

    def search_clinical_records(
        self,
        resource_type: str,
        patient_id: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search records across clinical tables."""
        return self._service.search_clinical_records(
            resource_type=resource_type,
            patient_id=patient_id,
            query_params=query_params,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )

    def create_clinical_order(
        self,
        order_type: str,
        patient_id: str,
        details: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Order a medication, lab, or referral."""
        return self._service.create_clinical_order(
            order_type=order_type,
            patient_id=patient_id,
            details=details,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )

    def update_order_or_referral(
        self,
        order_id: str,
        status: str,
        notes: str = "",
    ) -> Dict[str, Any]:
        """Update status or notes on a referral or order."""
        return self._service.update_order_or_referral(
            order_id=order_id,
            status=status,
            notes=notes,
            actor_id=self.actor_id,
            actor_role=self.actor_role,
        )

    def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        facility_id: str,
        slot_iso: str,
        visit_type: str = "consultation",
        notes: str = "",
    ) -> Dict[str, Any]:
        """Book an appointment slot."""
        return self._service.schedule_appointment(
            patient_id=patient_id,
            provider_id=provider_id,
            facility_id=facility_id,
            slot_iso=slot_iso,
            visit_type=visit_type,
            notes=notes,
            actor_id=self.actor_id,
            actor_role="scheduler",
        )

    def send_portal_message(
        self,
        recipient_type: str,
        recipient_id: str,
        patient_id: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Send message via portal."""
        return self._service.send_portal_message(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            patient_id=patient_id,
            subject=subject,
            body=body,
            actor_id=self.actor_id,
            actor_role="nurse",
        )

    def submit_prior_authorization(
        self,
        patient_id: str,
        service_code: str,
        payer_id: str,
        clinical_rationale: str,
    ) -> Dict[str, Any]:
        """Submit prior authorization request."""
        return self._service.submit_prior_authorization(
            patient_id=patient_id,
            service_code=service_code,
            payer_id=payer_id,
            clinical_rationale=clinical_rationale,
            actor_id=self.actor_id,
            actor_role="billing_specialist",
        )

    def escalate_to_human_clinician(
        self,
        patient_id: str,
        urgency: str,
        clinical_summary: str,
        required_action: str,
    ) -> Dict[str, Any]:
        """Handoff case to human clinician when safety threshold is reached."""
        return self._service.escalate_to_human_clinician(
            patient_id=patient_id,
            urgency=urgency,
            clinical_summary=clinical_summary,
            required_action=required_action,
            actor_id=self.actor_id,
            actor_role="nurse",
        )

    def get_audit_log(
        self,
        patient_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit log records."""
        return self._service.get_audit_log(patient_id=patient_id, limit=limit)

    def calculate_state_hash(self) -> str:
        """Calculate database state hash."""
        return self._service.calculate_state_hash()
