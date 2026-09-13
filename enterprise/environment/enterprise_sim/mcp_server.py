"""FastMCP server exposing cross-system enterprise tools over stdio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .context import EnterpriseContext
from .service import EnterpriseService

mcp = FastMCP("enterprise")


def _get_service() -> EnterpriseService:
    ctx = EnterpriseContext.from_env()
    ctx.ensure_initialized()
    return ctx.service


@mcp.tool()
def search_organization_directory(
    query: Optional[str] = None, department_code: Optional[str] = None
) -> str:
    """Search employees, reporting managers, teams, and departments across the enterprise."""
    svc = _get_service()
    res = svc.search_organization(query=query, department_code=department_code)
    return json.dumps(res, indent=2)


@mcp.tool()
def get_customer_profile(customer_id: str) -> str:
    """Retrieve unified customer 360 profile: account, contacts, active contracts, SLAs, invoices, tickets, and deals."""
    svc = _get_service()
    res = svc.get_customer_profile(customer_id=customer_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def crm_query_records(record_type: str, query: Optional[str] = None) -> str:
    """Query CRM records: 'customers', 'deals', or 'leads'."""
    svc = _get_service()
    res = svc.crm_query_records(record_type=record_type, query=query)
    return json.dumps(res, indent=2)


@mcp.tool()
def crm_update_deal(deal_id: str, stage: str, notes: str = "") -> str:
    """Update CRM deal stage ('discovery', 'proposal', 'negotiation', 'closed_won', 'closed_lost')."""
    svc = _get_service()
    res = svc.crm_update_deal(deal_id=deal_id, stage=stage, notes=notes)
    return json.dumps(res, indent=2)


@mcp.tool()
def support_get_ticket(ticket_id: str) -> str:
    """Fetch customer support ticket description, priority, status, and communication comments."""
    svc = _get_service()
    res = svc.support_get_ticket(ticket_id=ticket_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def support_add_comment(ticket_id: str, content: str, is_internal: bool = False) -> str:
    """Post an internal or customer-visible comment to a support ticket. Automatically audited for DLP."""
    svc = _get_service()
    res = svc.support_add_comment(ticket_id=ticket_id, content=content, is_internal=is_internal)
    return json.dumps(res, indent=2)


@mcp.tool()
def support_update_ticket_status(ticket_id: str, status: str) -> str:
    """Update ticket status ('open', 'in_progress', 'pending_customer', 'pending_approval', 'resolved', 'closed')."""
    svc = _get_service()
    res = svc.support_update_ticket_status(ticket_id=ticket_id, status=status)
    return json.dumps(res, indent=2)


@mcp.tool()
def billing_get_invoices(customer_id: str) -> str:
    """Query all historical and active billing invoices for a customer."""
    svc = _get_service()
    res = svc.billing_get_invoices(customer_id=customer_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def billing_process_refund(
    invoice_id: str,
    customer_id: str,
    amount_usd: float,
    reason: str,
    approved_by_id: Optional[str] = None,
    workflow_instance_id: Optional[str] = None,
) -> str:
    """Issue a billing refund. Policy rules automatically enforce financial authorization limits and contract SLA caps."""
    svc = _get_service()
    res = svc.billing_process_refund(
        invoice_id=invoice_id,
        customer_id=customer_id,
        amount_usd=amount_usd,
        reason=reason,
        approved_by_id=approved_by_id,
        workflow_instance_id=workflow_instance_id,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def email_read_inbox(user_email: str, limit: int = 20) -> str:
    """Read recent emails in an employee inbox."""
    svc = _get_service()
    res = svc.email_read_inbox(user_email=user_email, limit=limit)
    return json.dumps(res, indent=2)


@mcp.tool()
def email_send_message(
    sender_email: str,
    recipient_emails: List[str],
    subject: str,
    body: str,
    cc_emails: Optional[List[str]] = None,
) -> str:
    """Send an email from an employee account. Automatically scanned for data loss prevention (DLP) compliance."""
    svc = _get_service()
    res = svc.email_send_message(
        sender_email=sender_email,
        recipient_emails=recipient_emails,
        subject=subject,
        body=body,
        cc_emails=cc_emails,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def workflow_request_approval(
    request_type: str,
    approver_id: str,
    amount_usd: float,
    reason: str,
    workflow_instance_id: Optional[str] = None,
) -> str:
    """Submit a formal approval request to a designated manager for policy-restricted actions (e.g. refunds > limit)."""
    svc = _get_service()
    res = svc.workflow_request_approval(
        request_type=request_type,
        approver_id=approver_id,
        amount_usd=amount_usd,
        reason=reason,
        workflow_instance_id=workflow_instance_id,
    )
    return json.dumps(res, indent=2)


@mcp.tool()
def workflow_get_approval_status(request_id: str) -> str:
    """Check decision status ('pending', 'approved', 'rejected') and manager notes for an approval request."""
    svc = _get_service()
    res = svc.workflow_get_approval_status(request_id=request_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def document_read(document_id: str) -> str:
    """Read company policies, standard operating procedures, and contract documents."""
    svc = _get_service()
    res = svc.document_read(document_id=document_id)
    return json.dumps(res, indent=2)


@mcp.tool()
def get_audit_trail(limit: int = 50) -> str:
    """Retrieve the recent enterprise compliance audit log."""
    svc = _get_service()
    res = svc.get_audit_log()[-limit:]
    return json.dumps(res, indent=2)


@mcp.tool()
def step_simulation(minutes: int = 15) -> str:
    """Advance the enterprise virtual clock and process background events (manager approvals, customer replies)."""
    svc = _get_service()
    res = svc.step_simulation(minutes=minutes)
    return json.dumps(res, indent=2)


@mcp.tool()
def submit_task(summary: str, affected_ids: str = "") -> str:
    """Submit formal completion report for the enterprise operational task."""
    svc = _get_service()
    res = svc.submit_task(summary=summary, affected_ids=affected_ids)
    return json.dumps(res, indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
