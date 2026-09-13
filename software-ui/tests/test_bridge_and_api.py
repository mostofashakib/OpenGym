"""Test software-ui bridge and integration endpoints."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
BRIDGE_PATH = SCRIPT_DIR / "scripts" / "software_bridge.py"


def run_bridge(cmd: str, *args: str) -> dict:
    res = subprocess.run(
        [sys.executable, str(BRIDGE_PATH), cmd, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(res.stdout)


def test_bridge_list_domains():
    res = run_bridge("list_domains")
    assert res.get("ok") is True
    domains = res.get("domains", [])
    assert "logistics" in domains
    assert "research" in domains
    assert "clinical_trials" in domains


def test_bridge_get_schema():
    res = run_bridge("get_schema")
    assert res.get("ok") is True
    schema = res.get("schema", {})
    assert "entities" in schema
    assert len(schema["entities"]) > 0


def test_bridge_search_entities():
    res = run_bridge("search_entities", "Shipment", "", "", "1", "10")
    assert res.get("ok") is True
    items = res.get("result", {}).get("items", [])
    assert isinstance(items, list)


def test_bridge_state_hash():
    res = run_bridge("get_state_hash")
    assert res.get("ok") is True
    assert len(res.get("state_hash", "")) == 64


def test_bridge_submit_task():
    res = run_bridge("submit_task", "Handover completed", "SHP-1001")
    assert res.get("ok") is True
