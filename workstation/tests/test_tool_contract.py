"""Tests verifying workstation tools, arguments, and contracts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from tools.workstation_client import WorkstationClient
from workstation_sim.seed import seed_database
from workstation_sim.service import ServiceError


def test_tool_contract_complete_suite() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        client = WorkstationClient(db_path=db)

        # 1. Email tools
        inbox = client.list_emails(folder="inbox")
        assert "threads" in inbox and inbox["count"] > 0
        first_thread_id = inbox["threads"][0]["id"]
        thread_details = client.get_thread(first_thread_id)
        assert "thread" in thread_details and "messages" in thread_details

        sent_res = client.send_email(
            to=["test@example.com"],
            subject="Test subject",
            body="Test body",
        )
        assert sent_res.get("sent") is True

        # 2. Calendar tools
        events = client.list_events()
        assert "events" in events and events["count"] > 0
        created_ev = client.create_event(
            title="Test Meeting",
            start_iso="2026-10-20T10:00:00Z",
            end_iso="2026-10-20T10:30:00Z",
        )
        assert created_ev.get("created") is True

        # 3. Drive & File tools
        files = client.list_files(directory="/contracts/")
        assert "files" in files and files["count"] > 0
        written_f = client.write_file("/test/sample.txt", "Hello World")
        assert written_f.get("written") is True
        read_f = client.read_file("/test/sample.txt")
        assert read_f["content_text"] == "Hello World"

        # 4. CRM tools
        crm_search = client.search_customers("Acme")
        assert len(crm_search["customers"]) > 0
        cust_id = crm_search["customers"][0]["id"]
        cust_record = client.get_customer(cust_id)
        assert cust_record["customer"]["id"] == cust_id
        assert len(cust_record["contacts"]) > 0

        # 5. Billing tools
        inv = client.get_invoice("INV-3817")
        assert inv["invoice_number"] == "INV-3817"
        calc = client.calculate_refund("INV-3817")
        assert calc["allowed_refund_cents"] > 0

        # 6. Tickets tools
        ticks = client.list_tickets()
        assert ticks["count"] > 0
        first_tick_id = ticks["tickets"][0]["id"]
        tick = client.get_ticket(first_tick_id)
        assert tick["ticket"]["id"] == first_tick_id

        # 7. KB tools
        kb_res = client.search_kb("cancellation")
        assert kb_res["count"] > 0
        art = client.get_kb_article(kb_res["articles"][0]["id"])
        assert "Standard Operating Procedure" in art["body"]

        # 8. Terminal tool
        cmd_res = client.run_command("whoami")
        assert cmd_res["stdout"] == "alex.mercer"

        # 9. Core standard primitives (OES-1)
        audit_res = client.get_audit_events(limit=10)
        assert "events" in audit_res and audit_res["count"] > 0

        step_res = client.step_simulation(seconds=120)
        assert step_res["stepped_seconds"] == 120

        submit_res = client.submit_task("Triage and cancellation completed", ["CUST-1042", "INV-3817"])
        assert submit_res["submitted"] is True
        assert len(submit_res["affected_ids"]) == 2

        # 10. Parameter normalization test (camelCase vs snake_case)
        camel_thread = client.execute("mail_get_thread", {"threadId": first_thread_id})
        assert "thread" in camel_thread
        camel_inv = client.execute("billing_get_invoice", {"invoiceNumber": "INV-3817"})
        assert camel_inv["invoice_number"] == "INV-3817"
        camel_cust = client.execute("crm_get_customer", {"customerId": cust_id})
        assert camel_cust["customer"]["id"] == cust_id
