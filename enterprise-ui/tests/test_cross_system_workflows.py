"""Tests for cross-system workflow interactions across CRM, Billing, Support, and Email."""

import sqlite3
import pytest
from enterprise.environment.enterprise_sim.context import EnterpriseContext
from enterprise.environment.enterprise_sim.db_generator import compile_database_schema, populate_enterprise_organization
from enterprise.tools.enterprise_client import EnterpriseClient


@pytest.fixture
def enterprise_client(tmp_path):
    db_path = str(tmp_path / "test_workflows.db")
    conn = sqlite3.connect(db_path)
    compile_database_schema(conn)
    populate_enterprise_organization(conn, seed=42, num_employees=25, num_customers=15)
    conn.close()
    return EnterpriseClient(db_path=db_path)


def test_customer_360_profile_query(enterprise_client):
    client = enterprise_client
    prof = client.get_customer_profile("cust-0001")
    assert "customer" in prof
    assert prof["customer"]["company_name"] == "Acme Global Industries"
    assert len(prof["contacts"]) >= 1
    assert len(prof["contracts"]) >= 1
    assert prof["contracts"][0]["sla_tier"] == "platinum"
    assert len(prof["invoices"]) >= 1
    assert len(prof["tickets"]) >= 1


def test_support_and_billing_refund_flow(enterprise_client):
    client = enterprise_client

    # 1. Inspect ticket
    ticket = client.support_get_ticket("tkt-0001")
    assert "ticket" in ticket
    assert ticket["ticket"]["status"] == "open"

    # 2. Add internal comment
    comm_res = client.support_add_comment("tkt-0001", "Verifying contract terms with Director.", is_internal=True)
    assert comm_res["success"] is True

    # 3. Request manager approval for $2,400
    appr_req = client.workflow_request_approval(
        request_type="refund_approval",
        approver_id="emp-002",
        amount_usd=2400.0,
        reason="SLA concession verified against contract terms and outage report.",
    )
    assert appr_req["success"] is True

    # 4. Manager reviews and approves
    decisions = client.simulate_manager_approval(approver_id="emp-002")
    assert any(d["status"] == "approved" for d in decisions)

    # 5. Process refund
    ref_res = client.billing_process_refund(
        invoice_id="inv-cust-0001-01",
        customer_id="cust-0001",
        amount_usd=2400.0,
        reason="Outage refund approved by Director Marcus Vance",
        approved_by_id="emp-002",
    )
    assert ref_res["success"] is True
    assert ref_res["status"] == "processed"

    # 6. Update ticket status to resolved
    upd_res = client.support_update_ticket_status("tkt-0001", "resolved")
    assert upd_res["success"] is True

    # 7. Send confirmation email
    email_res = client.email_send_message(
        sender_email="ereyes@apex-corp.com",
        recipient_emails=["dmiller@acme-global.com"],
        subject="Service credit processed",
        body="Dear David, your $2,400 SLA credit has been successfully processed.",
    )
    assert email_res["success"] is True
