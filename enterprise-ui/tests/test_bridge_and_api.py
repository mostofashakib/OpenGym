import json
from pathlib import Path
import subprocess
import pytest

BRIDGE_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "enterprise_bridge.py"
PYTHON_BIN = "/opt/homebrew/opt/python@3.11/bin/python3.11"


def run_bridge(cmd: str, *args: str) -> dict:
    call_args = [PYTHON_BIN, str(BRIDGE_SCRIPT), cmd] + list(args)
    res = subprocess.run(
        call_args,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def test_bridge_list_customers():
    res = run_bridge("list_customers")
    assert res.get("ok") is True
    assert "customers" in res
    assert len(res["customers"]) > 0


def test_bridge_get_customer_profile():
    res = run_bridge("list_customers")
    cust_id = res["customers"][0]["id"]
    prof_res = run_bridge("get_customer_profile", cust_id)
    assert prof_res.get("ok") is True
    assert "profile" in prof_res
    assert "customer" in prof_res["profile"]
    assert "contracts" in prof_res["profile"]


def test_bridge_list_tickets_and_comment():
    res = run_bridge("list_tickets")
    assert res.get("ok") is True
    assert "tickets" in res
    if res["tickets"]:
        tkt_id = res["tickets"][0]["id"]
        comm_res = run_bridge("add_comment", tkt_id, "Automated test response comment", "true")
        assert comm_res.get("ok") is True


def test_bridge_list_approvals():
    res = run_bridge("list_approvals")
    assert res.get("ok") is True
    assert "approvals" in res


def test_bridge_state_hash_and_step():
    hash_res = run_bridge("state_hash")
    assert hash_res.get("ok") is True
    assert len(hash_res["state_hash"]) == 64

    step_res = run_bridge("step_simulation", "15")
    assert step_res.get("ok") is True
    assert "step" in step_res

    sub_res = run_bridge("submit_task", "Test run completed", "cust-0001")
    assert sub_res.get("ok") is True
