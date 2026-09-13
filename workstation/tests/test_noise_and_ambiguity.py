"""Tests verifying presence of realistic noise, ambiguity, and cross-application references."""

from __future__ import annotations

import tempfile
from pathlib import Path

from workstation_sim.seed import seed_database
from workstation_sim.service import export_state


def test_similar_names_and_homoglyphs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        state = export_state(db)

        contacts = state["crm_contacts"]
        sarah_jenkins = [c for c in contacts if c["name"] == "Sarah Jenkins"]
        sara_jenkens = [c for c in contacts if c["name"] == "Sara Jenkens"]

        assert len(sarah_jenkins) >= 1, "Expected primary contact Sarah Jenkins at Acme"
        assert len(sara_jenkens) >= 1, "Expected noise contact Sara Jenkens at Globex"
        assert sarah_jenkins[0]["customer_id"] != sara_jenkens[0]["customer_id"], "Contacts must belong to different customers"


def test_superseded_contract_versions() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        state = export_state(db)

        files = state["files"]
        acme_contracts = [f for f in files if "Acme_Corp_MSA" in f["name"]]

        assert len(acme_contracts) >= 2, f"Expected both active and superseded Acme contracts, found: {len(acme_contracts)}"
        active = next((f for f in acme_contracts if "2026" in f["name"]), None)
        superseded = next((f for f in acme_contracts if "2023" in f["name"] or "Archived" in f["name"]), None)

        assert active is not None, "Active 2026 amendment must exist"
        assert superseded is not None, "Archived/superseded contract must exist"
        assert "Section 4.2" in active["content_text"], "Active amendment must specify Section 4.2 pro-rata refund terms"


def test_cross_application_customer_consistency() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        seed_database(db, seed=42)
        state = export_state(db)

        cust_id = "CUST-1042"
        # Check presence across all systems
        crm_cust = next((c for c in state["customers"] if c["id"] == cust_id), None)
        assert crm_cust is not None and crm_cust["name"] == "Acme Corp"

        invoices = [i for i in state["invoices"] if i["customer_id"] == cust_id]
        assert any(i["invoice_number"] == "INV-3817" for i in invoices), "Target invoice INV-3817 must exist for Acme"

        threads = [t for t in state["email_threads"] if t.get("customer_id") == cust_id]
        assert len(threads) >= 1, "Email threads must link to Acme customer ID"

        tickets = [t for t in state["tickets"] if t.get("customer_id") == cust_id]
        assert len(tickets) >= 1, "Support tickets must link to Acme customer ID"

        files = [f for f in state["files"] if f.get("customer_id") == cust_id]
        assert len(files) >= 1, "Files must link to Acme customer ID"
