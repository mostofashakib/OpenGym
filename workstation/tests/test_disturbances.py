"""Tests for controlled, seed-reproducible disturbances."""

from __future__ import annotations

import tempfile
from pathlib import Path

from tools.workstation_client import WorkstationClient
from workstation_sim.disturbances import DisturbanceError, DisturbanceManager
from workstation_sim.seed import seed_database


def test_disturbances_disabled_by_default() -> None:
    dm = DisturbanceManager(seed=42, disturbance_rate=0.0)
    for _ in range(100):
        # Must never raise with 0.0 rate
        dm.evaluate_action("crm", "get_customer")


def test_disturbances_trigger_deterministically_with_rate() -> None:
    dm1 = DisturbanceManager(seed=42, disturbance_rate=0.5)
    dm2 = DisturbanceManager(seed=42, disturbance_rate=0.5)

    outcomes1: list[bool] = []
    outcomes2: list[bool] = []

    for _ in range(20):
        try:
            dm1.evaluate_action("mail", "send_message")
            outcomes1.append(False)
        except DisturbanceError:
            outcomes1.append(True)

    for _ in range(20):
        try:
            dm2.evaluate_action("mail", "send_message")
            outcomes2.append(False)
        except DisturbanceError:
            outcomes2.append(True)

    assert outcomes1 == outcomes2, "Disturbances must produce identical patterns given the same seed and rate"
    assert any(outcomes1), "Expected at least one disturbance with 0.5 rate over 20 iterations"
