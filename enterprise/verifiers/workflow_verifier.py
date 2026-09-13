"""Task goal and business outcome checks for enterprise workflows."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional

from .results import CheckResult
from enterprise.tools.enterprise_client import EnterpriseClient


def check_refund_processed(
    client: EnterpriseClient,
    customer_id: str,
    expected_amount: float,
    expected_invoice_id: str,
    required_approver_id: Optional[str] = None,
    weight: float = 3.0,
) -> CheckResult:
    """Verify that the required refund was accurately processed with proper manager authorization."""
    with sqlite3.connect(str(client.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """SELECT * FROM refund_records
               WHERE customer_id = ? AND invoice_id = ? AND status = 'processed'
               ORDER BY rowid DESC LIMIT 1""",
            (customer_id, expected_invoice_id),
        ).fetchone()

        if not row:
            return CheckResult(
                name="Workflow: Refund Transaction Execution",
                passed=False,
                score=0.0,
                max_score=weight,
                details=f"No processed refund found for customer {customer_id} on invoice {expected_invoice_id}.",
            )

        amount = float(row["amount_usd"])
        appr_id = row["approved_by_id"]

        if abs(amount - expected_amount) > 0.01:
            return CheckResult(
                name="Workflow: Refund Transaction Execution",
                passed=False,
                score=0.0,
                max_score=weight,
                details=f"Refund amount ${amount:,.2f} does not match expected amount ${expected_amount:,.2f}.",
            )

        if required_approver_id and appr_id != required_approver_id:
            return CheckResult(
                name="Workflow: Refund Transaction Execution",
                passed=False,
                score=1.0,
                max_score=weight,
                details=f"Refund processed with approver '{appr_id}', expected required manager '{required_approver_id}'.",
            )

        return CheckResult(
            name="Workflow: Refund Transaction Execution",
            passed=True,
            score=weight,
            max_score=weight,
            details=f"Refund of ${amount:,.2f} successfully processed against {expected_invoice_id} with manager approval from {appr_id}.",
            evidence={"refund_id": row["id"], "amount": amount, "approver": appr_id},
        )


def check_ticket_status(
    client: EnterpriseClient,
    ticket_id: str,
    expected_status: str = "resolved",
    weight: float = 2.0,
) -> CheckResult:
    """Verify that support ticket was updated to the expected lifecycle state."""
    with sqlite3.connect(str(client.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT status, resolved_iso FROM support_tickets WHERE id = ?", (ticket_id,)).fetchone()

        if not row:
            return CheckResult(
                name="Workflow: Support Ticket Resolution",
                passed=False,
                score=0.0,
                max_score=weight,
                details=f"Ticket {ticket_id} not found.",
            )

        current_status = row["status"]
        if current_status == expected_status:
            return CheckResult(
                name="Workflow: Support Ticket Resolution",
                passed=True,
                score=weight,
                max_score=weight,
                details=f"Support ticket {ticket_id} successfully progressed to '{expected_status}'.",
                evidence={"ticket_id": ticket_id, "status": current_status},
            )
        else:
            return CheckResult(
                name="Workflow: Support Ticket Resolution",
                passed=False,
                score=0.0,
                max_score=weight,
                details=f"Support ticket {ticket_id} has status '{current_status}', expected '{expected_status}'.",
            )


def check_customer_notification_sent(
    client: EnterpriseClient,
    recipient_email: str,
    weight: float = 2.0,
) -> CheckResult:
    """Verify that a customer confirmation email was transmitted."""
    with sqlite3.connect(str(client.db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM email_messages WHERE recipient_emails_json LIKE ? AND folder = 'sent'",
            (f"%{recipient_email}%",),
        ).fetchall()

        if rows:
            return CheckResult(
                name="Communication: Customer Notification Sent",
                passed=True,
                score=weight,
                max_score=weight,
                details=f"Confirmation email transmitted to contact {recipient_email}.",
                evidence={"emails_count": len(rows), "recipient": recipient_email},
            )
        else:
            return CheckResult(
                name="Communication: Customer Notification Sent",
                passed=False,
                score=0.0,
                max_score=weight,
                details=f"No sent email found addressed to required contact {recipient_email}.",
            )
