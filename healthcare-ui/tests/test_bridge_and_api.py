"""Test healthcare-ui bridge and integration endpoints."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
BRIDGE_PATH = SCRIPT_DIR / "scripts" / "healthcare_bridge.py"


def run_bridge(cmd: str, *args: str) -> dict:
    res = subprocess.run(
        [sys.executable, str(BRIDGE_PATH), cmd, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def test_bridge_list_patients():
    res = run_bridge("list_patients")
    assert res.get("ok") is True
    patients = res.get("patients", [])
    assert len(patients) > 0
    first = patients[0]
    assert "id" in first
    assert "mrn" in first


def test_bridge_get_patient_chart():
    res = run_bridge("get_patient_chart", "pat-0001")
    assert res.get("ok") is True
    chart = res.get("chart", {})
    assert "patient" in chart
    assert "allergies" in chart
    assert "conditions" in chart


def test_bridge_verify_patient():
    res = run_bridge("verify_patient", "pat-0001", "1975-05-15")
    assert res.get("ok") is True
    assert res.get("verified", {}).get("verified") is True


def test_bridge_state_hash():
    res = run_bridge("get_state_hash")
    assert res.get("ok") is True
    assert len(res.get("state_hash", "")) == 64


def test_bridge_step_and_submit():
    step_res = run_bridge("step_simulation", "15")
    assert step_res.get("ok") is True

    sub_res = run_bridge("submit_task", "Clinical clearance completed", "pat-0001,sr-pat-0001")
    assert sub_res.get("ok") is True
