"""Tests for enterprise workflow engine and state machines."""

import sqlite3
import pytest
from enterprise.environment.enterprise_sim.db_generator import compile_database_schema
from enterprise.environment.enterprise_sim.workflow_engine import WorkflowEngine


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(":memory:")
    compile_database_schema(conn)
    yield conn
    conn.close()


def test_workflow_lifecycle(memory_db):
    engine = WorkflowEngine(memory_db)

    # 1. Start workflow
    wf = engine.start_workflow(
        workflow_name="customer_refund",
        customer_id="cust-0001",
        entity_id="inv-cust-0001-01",
        initial_data={"requested_amount": 2400.0, "reason": "API outage"},
    )
    assert wf["status"] == "running"
    assert wf["current_step"] == "verify_case"
    inst_id = wf["instance_id"]

    # 2. Advance step
    adv = engine.advance_step(inst_id, "verify_contract", {"sla_tier": "platinum"})
    assert adv["success"] is True
    assert adv["current_step"] == "verify_contract"
    assert adv["data"]["sla_tier"] == "platinum"

    # 3. Block for approval
    block_res = engine.block_for_approval(inst_id, "appr-001")
    assert block_res["success"] is True
    assert block_res["status"] == "blocked"

    # 4. Advance and mark completed
    comp_res = engine.advance_step(inst_id, "refund_completed", {"refund_id": "ref-001"}, mark_completed=True)
    assert comp_res["success"] is True
    assert comp_res["status"] == "completed"

    # 5. Fetch instance
    inst = engine.get_workflow_instance(inst_id)
    assert inst is not None
    assert inst["status"] == "completed"
    assert inst["step_data"]["refund_id"] == "ref-001"
