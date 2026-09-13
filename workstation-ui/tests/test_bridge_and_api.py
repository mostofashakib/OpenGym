"""Test workstation-ui bridge and integration endpoints."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
BRIDGE_PATH = SCRIPT_DIR / "scripts" / "workstation_bridge.py"


def run_bridge(cmd: str, *args: str) -> dict:
    res = subprocess.run(
        [sys.executable, str(BRIDGE_PATH), cmd, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def test_bridge_list_apps():
    res = run_bridge("list_apps")
    assert res.get("ok") is True
    apps = res.get("apps", [])
    assert len(apps) == 12
    app_ids = [a["id"] for a in apps]
    assert "mail" in app_ids
    assert "crm" in app_ids
    assert "billing" in app_ids
    assert "tickets" in app_ids


def test_bridge_crm_customer():
    res = run_bridge("crm_get_customer", "CUST-001")
    assert res.get("ok") is True
    cust = res.get("customer", {})
    assert "customer_id" in cust or "id" in cust


def test_bridge_tickets():
    res = run_bridge("ticket_list", "all")
    assert res.get("ok") is True
    tickets = res.get("tickets", [])
    assert isinstance(tickets, list)


def test_bridge_state_hash():
    res = run_bridge("get_state_hash")
    assert res.get("ok") is True
    assert len(res.get("state_hash", "")) == 64


def test_bridge_step_and_submit():
    step_res = run_bridge("step_simulation", "15")
    assert step_res.get("ok") is True

    sub_res = run_bridge("submit_task", "Handover completed", "CUST-001,tkt-0001")
    assert sub_res.get("ok") is True
