"""Tests for deterministic database seeding and state hashing."""

from __future__ import annotations

import tempfile
from pathlib import Path

from workstation_sim.seed import seed_database
from workstation_sim.service import calculate_state_hash, export_state
from workstation_sim.sqlite_common import calculate_database_hash, connect


def test_seed_determinism_identical_hashes() -> None:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        db1 = Path(tmp1) / "db1.db"
        db2 = Path(tmp2) / "db2.db"

        seed_database(db1, seed=42)
        seed_database(db2, seed=42)

        hash1 = calculate_state_hash(db1)
        hash2 = calculate_state_hash(db2)

        assert hash1 == hash2, f"Expected identical state hashes for seed 42, got {hash1} vs {hash2}"

        with connect(db1) as conn1, connect(db2) as conn2:
            db_hash1 = calculate_database_hash(conn1)
            db_hash2 = calculate_database_hash(conn2)
            assert db_hash1 == db_hash2, f"Expected identical OES-1 database hashes, got {db_hash1} vs {db_hash2}"


def test_different_seeds_produce_distinct_states() -> None:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        db1 = Path(tmp1) / "db1.db"
        db2 = Path(tmp2) / "db2.db"

        seed_database(db1, seed=42)
        seed_database(db2, seed=99)

        hash1 = calculate_state_hash(db1)
        hash2 = calculate_state_hash(db2)

        assert hash1 != hash2, "Expected distinct hashes for different seeds"


def test_seed_dataset_scale_and_completeness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        meta = seed_database(db, seed=42)
        state = export_state(db)

        assert len(state["employees"]) == 50, f"Expected 50 employees, got {len(state['employees'])}"
        assert len(state["customers"]) == 200, f"Expected 200 customers, got {len(state['customers'])}"
        assert len(state["files"]) == 1000, f"Expected 1000 files, got {len(state['files'])}"
        assert len(state["email_threads"]) == 500, f"Expected 500 email threads, got {len(state['email_threads'])}"
        assert len(state["calendar_events"]) == 100, f"Expected 100 calendar events, got {len(state['calendar_events'])}"
        assert len(state["tickets"]) == 300, f"Expected 300 tickets, got {len(state['tickets'])}"
        assert len(state["invoices"]) == 200, f"Expected 200 invoices, got {len(state['invoices'])}"
        assert len(state["crm_deals"]) >= 50, "Expected at least 50 CRM deals"
