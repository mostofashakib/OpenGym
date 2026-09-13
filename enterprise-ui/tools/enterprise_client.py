"""High-level client for interacting with the Enterprise Simulation Environment."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from enterprise.environment.enterprise_sim.actor_simulator import ActorSimulator
from enterprise.environment.enterprise_sim.context import EnterpriseContext
from enterprise.environment.enterprise_sim.service import EnterpriseService


class EnterpriseClient:
    """Client for evaluating and executing actions in the enterprise environment."""

    def __init__(
        self,
        db_path: Path | str = "/tmp/enterprise_company.db",
        actor_id: str = "emp-003",
        actor_role_id: str = "role-mgr-supp",
        context: Optional[EnterpriseContext] = None,
        service: Optional[EnterpriseService] = None,
    ) -> None:
        if service is not None:
            self._service = service
            self._ctx = EnterpriseContext(db_path=service.db_path, actor_id=actor_id, actor_role_id=actor_role_id)
        elif context is not None:
            self._ctx = context
            self._service = self._ctx.service
        else:
            self._ctx = EnterpriseContext(db_path=db_path, actor_id=actor_id, actor_role_id=actor_role_id)
            self._service = self._ctx.service

    @property
    def service(self) -> EnterpriseService:
        return self._service

    @property
    def db_path(self) -> Path:
        return Path(self._ctx.db_path)

    @property
    def actor_id(self) -> str:
        return self._ctx.actor_id

    @property
    def actor_role_id(self) -> str:
        return self._ctx.actor_role_id

    def search_organization_directory(
        self, query: Optional[str] = None, department_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self._service.search_organization(query=query, department_code=department_code)

    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        return self._service.get_customer_profile(customer_id=customer_id)

    def crm_query_records(self, record_type: str, query: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._service.crm_query_records(record_type=record_type, query=query)

    def crm_update_deal(self, deal_id: str, stage: str, notes: str = "") -> Dict[str, Any]:
        return self._service.crm_update_deal(deal_id=deal_id, stage=stage, notes=notes)

    def support_get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        return self._service.support_get_ticket(ticket_id=ticket_id)

    def support_add_comment(self, ticket_id: str, content: str, is_internal: bool = False) -> Dict[str, Any]:
        return self._service.support_add_comment(ticket_id=ticket_id, content=content, is_internal=is_internal)

    def support_update_ticket_status(self, ticket_id: str, status: str) -> Dict[str, Any]:
        return self._service.support_update_ticket_status(ticket_id=ticket_id, status=status)

    def billing_get_invoices(self, customer_id: str) -> List[Dict[str, Any]]:
        return self._service.billing_get_invoices(customer_id=customer_id)

    def billing_process_refund(
        self,
        invoice_id: str,
        customer_id: str,
        amount_usd: float,
        reason: str,
        approved_by_id: Optional[str] = None,
        workflow_instance_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._service.billing_process_refund(
            invoice_id=invoice_id,
            customer_id=customer_id,
            amount_usd=amount_usd,
            reason=reason,
            approved_by_id=approved_by_id,
            workflow_instance_id=workflow_instance_id,
        )

    def email_read_inbox(self, user_email: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._service.email_read_inbox(user_email=user_email, limit=limit)

    def email_send_message(
        self,
        sender_email: str,
        recipient_emails: List[str],
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self._service.email_send_message(
            sender_email=sender_email,
            recipient_emails=recipient_emails,
            subject=subject,
            body=body,
            cc_emails=cc_emails,
        )

    def workflow_request_approval(
        self,
        request_type: str,
        approver_id: str,
        amount_usd: float,
        reason: str,
        workflow_instance_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._service.workflow_request_approval(
            request_type=request_type,
            approver_id=approver_id,
            amount_usd=amount_usd,
            reason=reason,
            workflow_instance_id=workflow_instance_id,
        )

    def workflow_get_approval_status(self, request_id: str) -> Dict[str, Any]:
        return self._service.workflow_get_approval_status(request_id=request_id)

    def document_read(self, document_id: str) -> Dict[str, Any]:
        return self._service.document_read(document_id=document_id)

    def simulate_manager_approval(self, approver_id: str = "emp-002") -> List[Dict[str, Any]]:
        """Simulate manager reviewing and approving pending requests."""
        with sqlite3.connect(str(self.db_path)) as conn:
            simulator = ActorSimulator()
            return simulator.process_pending_manager_approvals(conn, manager_id=approver_id)

    def calculate_state_hash(self) -> str:
        return self._service.calculate_state_hash()

    def get_audit_log(
        self, actor_id: Optional[str] = None, action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self._service.get_audit_log(actor_id=actor_id, action=action)

    def get_audit_events(
        self, actor_id: Optional[str] = None, action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.get_audit_log(actor_id=actor_id, action=action)

    def step_simulation(self, minutes: int = 15) -> Dict[str, Any]:
        return self._service.step_simulation(minutes=minutes)

    def submit_task(self, summary: str, affected_ids: str = "") -> Dict[str, Any]:
        return self._service.submit_task(summary=summary, affected_ids=affected_ids)
