"""Granular predicate checks against canonical Workstation database state."""

from __future__ import annotations

import json
from typing import Any

from verifiers.results import CheckOutcome


def evaluate_cancellation_refund_task(state_data: dict[str, Any]) -> list[CheckOutcome]:
    """Verify the multi-step account cancellation and refund reconciliation task."""
    checks: list[CheckOutcome] = []

    # 1. Check refund issued for INV-3817 with pro-rated amount
    refunds = state_data.get("refunds", [])
    acme_refund = next(
        (r for r in refunds if r.get("invoice_id") == "INV-3817" or r.get("customer_id") == "CUST-1042"),
        None,
    )
    # Expected: 902,466 cents ($9,024.66) +/- 100 cents
    expected_amount = 902466
    refund_passed = False
    refund_detail: dict[str, Any] = {"found": bool(acme_refund)}

    if acme_refund:
        amt = acme_refund.get("amount_cents", 0)
        refund_detail["amount_cents"] = amt
        refund_detail["expected_cents"] = expected_amount
        if abs(amt - expected_amount) <= 150:
            refund_passed = True
        else:
            refund_detail["error"] = f"Refund amount {amt} deviates from expected {expected_amount}"

    checks.append(
        CheckOutcome(
            name="refund_issued_with_correct_pro_rata",
            passed=refund_passed,
            weight=0.25,
            detail=refund_detail,
        )
    )

    # 2. Check invoice status updated to 'refunded'
    invoices = state_data.get("invoices", [])
    inv_3817 = next((i for i in invoices if i.get("id") == "INV-3817" or i.get("invoice_number") == "INV-3817"), None)
    inv_passed = False
    inv_detail: dict[str, Any] = {"found": bool(inv_3817)}
    if inv_3817:
        inv_status = str(inv_3817.get("status", "")).lower()
        inv_detail["status"] = inv_status
        inv_passed = inv_status == "refunded"

    checks.append(
        CheckOutcome(
            name="invoice_status_updated_to_refunded",
            passed=inv_passed,
            weight=0.15,
            detail=inv_detail,
        )
    )

    # 3. Check customer CRM account status updated to 'churned'
    customers = state_data.get("customers", [])
    acme_cust = next((c for c in customers if c.get("id") == "CUST-1042"), None)
    crm_status_passed = False
    crm_detail: dict[str, Any] = {"found": bool(acme_cust)}
    if acme_cust:
        status_val = str(acme_cust.get("status", "")).lower()
        crm_detail["status"] = status_val
        crm_status_passed = status_val in ("churned", "cancelled")

    checks.append(
        CheckOutcome(
            name="crm_customer_status_churned",
            passed=crm_status_passed,
            weight=0.15,
            detail=crm_detail,
        )
    )

    # 4. Check CRM activity log recorded
    activity_logs = state_data.get("crm_activity_logs", [])
    acme_logs = [l for l in activity_logs if l.get("customer_id") == "CUST-1042"]
    cancel_log = next(
        (l for l in acme_logs if any(k in str(l.get("body", "")).lower() for k in ("cancel", "refund", "churn"))),
        None,
    )
    checks.append(
        CheckOutcome(
            name="crm_cancellation_activity_logged",
            passed=bool(cancel_log),
            weight=0.10,
            detail={"logged": bool(cancel_log), "entry": cancel_log},
        )
    )

    # 5. Check support ticket resolved
    tickets = state_data.get("tickets", [])
    acme_ticket = next((t for t in tickets if t.get("id") == "TICK-2042" or t.get("customer_id") == "CUST-1042"), None)
    ticket_passed = False
    ticket_detail: dict[str, Any] = {"found": bool(acme_ticket)}
    if acme_ticket:
        t_status = str(acme_ticket.get("status", "")).lower()
        ticket_detail["status"] = t_status
        ticket_passed = t_status in ("resolved", "closed")

    checks.append(
        CheckOutcome(
            name="support_ticket_resolved",
            passed=ticket_passed,
            weight=0.10,
            detail=ticket_detail,
        )
    )

    # 6. Check confirmation email sent to Sarah Jenkins, CC Marcus Vance
    emails = state_data.get("emails", [])
    sent_emails = [e for e in emails if e.get("folder") == "sent" or "sarah.jenkins" in str(e.get("to_addrs", ""))]
    email_passed = False
    email_detail: dict[str, Any] = {"sent_count": len(sent_emails)}

    for em in sent_emails:
        to_field = em.get("to_addrs", "")
        to_list = json.loads(to_field) if isinstance(to_field, str) and to_field.startswith("[") else [to_field]
        cc_field = em.get("cc_addrs", "")
        cc_list = json.loads(cc_field) if isinstance(cc_field, str) and cc_field.startswith("[") else [cc_field]
        body = str(em.get("body", "")).lower()

        is_to_sarah = any("sarah" in addr.lower() for addr in to_list)
        is_cc_marcus = any("marcus" in addr.lower() for addr in cc_list)
        mentions_refund = "refund" in body or "3817" in body or "9,024" in body or "9024" in body

        if is_to_sarah and mentions_refund:
            email_passed = True
            email_detail["matching_email"] = {
                "id": em.get("id"),
                "to": to_list,
                "cc": cc_list,
                "cc_marcus": is_cc_marcus,
            }
            break

    checks.append(
        CheckOutcome(
            name="customer_confirmation_email_sent",
            passed=email_passed,
            weight=0.15,
            detail=email_detail,
        )
    )

    # 7. Check calendar debrief scheduled 3 days out
    calendar_events = state_data.get("calendar_events", [])
    acme_event = next(
        (
            ev for ev in calendar_events
            if any(k in str(ev.get("title", "")).lower() for k in ("acme", "debrief", "post-churn"))
            and ("2026-10-17" in str(ev.get("start_iso", "")) or "2026-10" in str(ev.get("start_iso", "")))
        ),
        None,
    )
    checks.append(
        CheckOutcome(
            name="calendar_followup_debrief_scheduled",
            passed=bool(acme_event),
            weight=0.10,
            detail={"found": bool(acme_event), "event": acme_event},
        )
    )

    return checks
