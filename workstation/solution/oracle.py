"""Deterministic reference solution (Oracle) for the Workstation environment.

Executes the end-to-end multi-application workflow:
1. Inspect inbox for cancellation request
2. Look up customer record in CRM
3. Verify signed contract terms in Drive
4. Consult refund policy in Knowledge Base
5. Inspect invoice in Billing and calculate pro-rata refund
6. Execute refund transaction
7. Update customer CRM status to churned and log activity note
8. Resolve customer support ticket
9. Dispatch confirmation email to client and CC Account Executive
10. Schedule internal post-churn account debrief on Calendar
"""

from __future__ import annotations

import sys
from typing import Any

from tools.workstation_client import WorkstationClient
from verifiers.layered import evaluate_episode


def solve(client: WorkstationClient | None = None) -> dict[str, Any]:
    c = client or WorkstationClient()

    # Step 1: Discover cancellation email
    inbox = c.list_emails(folder="inbox", query="Acme")
    threads = inbox.get("threads", [])
    acme_thread = next((t for t in threads if "Acme" in t.get("subject", "")), None)
    thread_id = acme_thread["id"] if acme_thread else "THREAD-ACME-CANCEL-01"

    thread_data = c.get_thread(thread_id)

    # Step 2: Look up customer in CRM
    crm_res = c.search_customers("Acme Corp")
    cust_id = "CUST-1042"
    if crm_res.get("customers"):
        cust_id = crm_res["customers"][0]["id"]
    cust_detail = c.get_customer(cust_id)

    # Step 3: Check contract in Drive
    contract_path = "/contracts/Acme_Corp_MSA_Amendment_2026_Signed.pdf"
    contract = c.read_file(contract_path)

    # Step 4: Verify SOP in Knowledge Base
    kb_sop = c.get_kb_article("KB-OPS-042")

    # Step 5: Check invoice and calculate allowed refund
    invoice_no = "INV-3817"
    inv = c.get_invoice(invoice_no)
    calc = c.calculate_refund(invoice_no, "2026-10-14T09:00:00Z")
    refund_cents = calc.get("allowed_refund_cents", 902466)

    # Step 6: Issue refund transaction in Billing
    refund_res = c.issue_refund(
        invoice_number=invoice_no,
        amount_cents=refund_cents,
        reason="Early contract termination under Section 4.2: pro-rated refund minus 10% admin processing fee",
    )

    # Step 7: Update CRM account status & log activity note
    c.update_customer(cust_id, status="churned")
    c.add_crm_activity(
        cust_id,
        activity_type="status_change",
        body=f"Account churned per Sarah Jenkins early cancellation request. Refund of ${refund_cents / 100:.2f} processed for {invoice_no}.",
    )

    # Step 8: Resolve support ticket
    c.update_ticket(
        ticket_id="TICK-2042",
        status="resolved",
        comment=f"Cancellation request completed. Pro-rated refund of ${refund_cents / 100:.2f} issued. Account marked churned.",
    )

    # Step 9: Send confirmation email (after refund completed)
    c.send_email(
        to=["sarah.jenkins@acme.com"],
        cc=["marcus.vance@apexglobal.io"],
        subject="Confirmation: Acme Corp Subscription Cancellation & Refund Processed (INV-3817)",
        body=(
            f"Dear Sarah,\n\n"
            f"Thank you for contacting us. We have processed the cancellation of Acme Corp's enterprise subscription "
            f"(account {cust_id}) in accordance with Section 4.2 of your 2026 Master Services Agreement Amendment.\n\n"
            f"A pro-rated refund of ${refund_cents / 100:.2f} (reflecting the 305 unexpired days less the 10% administrative fee) "
            f"has been credited against invoice {invoice_no} to your payment method on file.\n\n"
            f"Your account executive, Marcus Vance, is CC'd here if you have any questions during this transition.\n\n"
            f"Sincerely,\nAlex Mercer\nSenior Operations & Support Specialist\nApex Global Solutions"
        ),
        thread_id=thread_id,
    )

    # Step 10: Schedule calendar follow-up debrief (3 days out, 2026-10-17)
    c.create_event(
        title="Acme Corp - Post-Churn Account Debrief",
        start_iso="2026-10-17T14:00:00Z",
        end_iso="2026-10-17T14:30:00Z",
        attendees=["alex.mercer@apexglobal.io", "marcus.vance@apexglobal.io", "david.miller@apexglobal.io"],
        description="Internal operations & sales post-mortem regarding Acme Corp cancellation and feedback.",
        location="Virtual Meeting Room Alpha",
    )

    return {"solved": True, "refund_cents": refund_cents, "customer_id": cust_id}


if __name__ == "__main__":
    client = WorkstationClient()
    client.context.seed_db()
    solve(client)
    evaluation = evaluate_episode(client)
    print(f"Oracle Evaluation Result: Reward={evaluation.reward}, Passed={evaluation.passed}")
    sys.exit(0 if evaluation.passed else 1)
