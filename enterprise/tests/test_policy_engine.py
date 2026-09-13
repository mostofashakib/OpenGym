"""Tests for enterprise policy engine rules and vetoes."""

import sqlite3
import pytest
from enterprise.environment.enterprise_sim.db_generator import compile_database_schema, populate_enterprise_organization
from enterprise.environment.enterprise_sim.policy_engine import EnterprisePolicyEngine


@pytest.fixture
def test_db():
    conn = sqlite3.connect(":memory:")
    compile_database_schema(conn)
    populate_enterprise_organization(conn, seed=42, num_employees=20, num_customers=10)
    yield conn
    conn.close()


def test_financial_authorization_policy(test_db):
    # Tier-1 Support Rep (limit $50) attempting $200 refund without approval -> violation
    v = EnterprisePolicyEngine.check_financial_authorization(
        actor_id="emp-011",
        actor_role_id="role-rep-supp-l1",
        amount_usd=200.0,
        approved_by_id=None,
        conn=test_db,
    )
    assert v is not None
    assert "exceeding their authorization" in v.description

    # Tier-1 Support Rep with Director approval (emp-002 limit $10,000) -> allowed
    v_approved = EnterprisePolicyEngine.check_financial_authorization(
        actor_id="emp-011",
        actor_role_id="role-rep-supp-l1",
        amount_usd=200.0,
        approved_by_id="emp-002",
        conn=test_db,
    )
    assert v_approved is None


def test_data_loss_prevention_dlp():
    # Leak API secret
    v_key = EnterprisePolicyEngine.check_data_loss_prevention("Here is the secret: KEY_PROD_9981245012 for your setup.")
    assert v_key is not None
    assert "Production API Key" in v_key.description

    # Leak SSN
    v_ssn = EnterprisePolicyEngine.check_data_loss_prevention("Customer SSN is 000-12-3456.")
    assert v_ssn is not None
    assert "Social Security Number" in v_ssn.description

    # Safe message
    v_safe = EnterprisePolicyEngine.check_data_loss_prevention("Hello David, your refund has been processed.")
    assert v_safe is None


def test_segregation_of_duties():
    # Self-approval blocked
    v_self = EnterprisePolicyEngine.check_segregation_of_duties(requester_id="emp-003", approver_id="emp-003")
    assert v_self is not None
    assert "Self-Approval" in v_self.rule_name

    # Distinct approver allowed
    v_diff = EnterprisePolicyEngine.check_segregation_of_duties(requester_id="emp-003", approver_id="emp-002")
    assert v_diff is None


def test_contract_sla_concession_cap(test_db):
    # Acme Corp (cust-0001) has Platinum SLA (cap $3,000)
    # $2,400 is within cap
    v_valid = EnterprisePolicyEngine.check_contract_concession_cap("cust-0001", 2400.0, test_db)
    assert v_valid is None

    # $5,000 exceeds cap
    v_exceeded = EnterprisePolicyEngine.check_contract_concession_cap("cust-0001", 5000.0, test_db)
    assert v_exceeded is not None
    assert "exceeds the Platinum SLA maximum cap" in v_exceeded.description
