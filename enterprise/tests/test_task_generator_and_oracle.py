"""Tests for Task Generator, Reference Oracle, and Layered Policy Verifier."""

import os
import sqlite3
import tempfile
import pytest

from enterprise.environment.enterprise_sim.db_generator import compile_database_schema, populate_enterprise_organization
from enterprise.environment.enterprise_sim.task_generator import EnterpriseTaskGenerator
from enterprise.solution.oracle import EnterpriseOracle
from enterprise.tools.enterprise_client import EnterpriseClient
from enterprise.verifiers.layered import LayeredVerifier


@pytest.fixture
def enterprise_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(path)
    compile_database_schema(conn)
    populate_enterprise_organization(conn, seed=42, num_employees=30, num_customers=20)
    conn.close()

    yield path

    if os.path.exists(path):
        os.unlink(path)


def test_generate_and_solve_refund_dispute(enterprise_db):
    task_gen = EnterpriseTaskGenerator(enterprise_db)
    task = task_gen.generate_task(archetype="customer_sla_refund_dispute")
    assert task["archetype"] == "customer_sla_refund_dispute"

    client = EnterpriseClient(db_path=enterprise_db)
    oracle = EnterpriseOracle(client=client)

    result = oracle.solve(task)
    assert result["success"] is True
    assert result["status"] == "completed"

    verifier = LayeredVerifier(client=client)
    ver_res = verifier.verify(task)

    assert not ver_res.vetoed
    assert ver_res.success
    assert ver_res.business_score > 0.0
    assert ver_res.policy_score > 0.0
    assert ver_res.final_score > 0.0


def test_generate_and_solve_security_triage(enterprise_db):
    task_gen = EnterpriseTaskGenerator(enterprise_db)
    task = task_gen.generate_task(archetype="security_incident_triage")
    assert task["archetype"] == "security_incident_triage"

    client = EnterpriseClient(db_path=enterprise_db)
    oracle = EnterpriseOracle(client=client)

    result = oracle.solve(task)
    assert result["success"] is True
    assert result["status"] == "completed"

    verifier = LayeredVerifier(client=client)
    ver_res = verifier.verify(task)

    assert not ver_res.vetoed
    assert ver_res.success
    assert ver_res.final_score > 0.0


def test_policy_engine_fatal_veto_on_unauthorized_refund(enterprise_db):
    client = EnterpriseClient(db_path=enterprise_db)
    customer_id = "cust-0001"
    invoice_id = "inv-cust-0001-01"

    # Deliberately bypass client safety checks and insert an unauthorized $5,000 refund directly into DB
    with sqlite3.connect(enterprise_db) as conn:
        conn.execute(
            """INSERT INTO refund_records (id, invoice_id, customer_id, amount_usd, reason, requested_by_id, approved_by_id, status, created_iso)
               VALUES ('ref-unauth-001', ?, ?, 5000.0, 'Unauthorized refund without approval', 'emp-011', NULL, 'processed', '2026-10-15T09:00:00Z')""",
            (invoice_id, customer_id),
        )
        conn.commit()

    task = {
        "task_id": "test_veto_task",
        "archetype": "customer_sla_refund_dispute",
        "customer_id": customer_id,
        "assertions": {
            "task_type": "customer_sla_refund_dispute",
            "customer_id": customer_id,
            "expected_refund_amount": 5000.0,
            "expected_invoice_id": invoice_id,
            "required_approver_id": "emp-002",
        },
    }

    verifier = LayeredVerifier(client=client)
    ver_res = verifier.verify(task)

    # Verifier MUST veto due to policy breach
    assert ver_res.vetoed
    assert not ver_res.success
    assert ver_res.final_score == 0.0
    assert any("FATAL POLICY VETO" in c.details or c.is_veto for c in ver_res.checks)
