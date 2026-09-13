"""Tests for synthetic human actors and virtual-time event scheduling."""

import sqlite3
import pytest
from enterprise.environment.enterprise_sim.actor_simulator import ActorSimulator
from enterprise.environment.enterprise_sim.db_generator import compile_database_schema, populate_enterprise_organization
from enterprise.environment.enterprise_sim.event_scheduler import EventScheduler


@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    compile_database_schema(conn)
    populate_enterprise_organization(conn, seed=42, num_employees=20, num_customers=10)
    yield conn
    conn.close()


def test_manager_approval_actor_decision(test_db):
    simulator = ActorSimulator()

    # Create an approval request for Director Marcus Vance (emp-002)
    test_db.execute(
        """INSERT INTO approval_requests (id, request_type, requester_id, approver_id, amount_usd, reason, status, created_iso)
           VALUES ('appr-test-01', 'refund_approval', 'emp-003', 'emp-002', 2400.0, 'Valid SLA outage concession for Acme Corp', 'pending', '2026-10-15T09:00:00Z')"""
    )
    test_db.commit()

    decisions = simulator.process_pending_manager_approvals(test_db, manager_id="emp-002")
    assert len(decisions) == 1
    assert decisions[0]["status"] == "approved"

    row = test_db.execute("SELECT status, decision_notes FROM approval_requests WHERE id = 'appr-test-01'").fetchone()
    assert row[0] == "approved"
    assert "Approved" in row[1]


def test_customer_actor_reply(test_db):
    simulator = ActorSimulator()
    res = simulator.simulate_customer_reply(
        test_db, ticket_id="tkt-0001", customer_contact_id="cont-cust-0001-01", message="Attached are our API logs."
    )
    assert res["ticket_id"] == "tkt-0001"

    row = test_db.execute("SELECT content FROM ticket_comments WHERE id = ?", (res["comment_id"],)).fetchone()
    assert "Attached are our API logs." in row[0]


def test_event_scheduler_time_and_events(test_db):
    scheduler = EventScheduler(test_db, seed=42)
    initial_time = scheduler.get_virtual_time()
    assert "2026-10-15" in initial_time

    # Advance clock by 45 minutes
    new_time = scheduler.advance_virtual_time(minutes=45)
    assert new_time != initial_time
    assert scheduler.get_virtual_time() == new_time

    # Trigger incoming email
    res = scheduler.trigger_incoming_email(
        sender_email="vip@acme-global.com",
        recipient_emails=["ereyes@apex-corp.com"],
        subject="Follow-up on Service Credit",
        body="Any update on our ticket?",
    )
    assert res["event"] == "incoming_email"

    row = test_db.execute("SELECT subject FROM email_messages WHERE id = ?", (res["email_id"],)).fetchone()
    assert "Follow-up on Service Credit" in row[0]
