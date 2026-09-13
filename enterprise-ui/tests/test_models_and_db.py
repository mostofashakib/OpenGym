"""Tests for enterprise database schema compilation, synthetic generation, and state hashing."""

import os
import sqlite3
import tempfile
import pytest

from enterprise.environment.enterprise_sim.db_generator import (
    calculate_database_hash,
    create_enterprise_database,
)


def test_enterprise_seeding_and_counts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_enterprise.db")
        res = create_enterprise_database(db_path, seed=42)

        counts = res["counts"]
        assert counts["employees"] == 100, "Should generate exactly 100 enterprise employees"
        assert counts["customers"] == 1000, "Should generate exactly 1,000 customers"
        assert counts["contracts"] == 1000, "Every customer should have an active contract"
        assert counts["invoices"] >= 200, "Should have active customer invoices"
        assert counts["documents"] >= 2, "Should have corporate policy documents"

        conn = sqlite3.connect(db_path)
        depts_count = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
        assert depts_count == 5, "Should have 5 core enterprise departments"

        teams_count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        assert teams_count == 20, "Should have 20 teams (4 per department)"

        mgr_count = conn.execute("SELECT COUNT(DISTINCT manager_id) FROM employees WHERE manager_id IS NOT NULL").fetchone()[0]
        assert mgr_count >= 5, "Should have multiple reporting managers"
        conn.close()


def test_deterministic_state_hashing() -> None:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        db1 = os.path.join(tmp1, "comp1.db")
        db2 = os.path.join(tmp2, "comp2.db")

        create_enterprise_database(db1, seed=42)
        create_enterprise_database(db2, seed=42)

        h1 = calculate_database_hash(db1)
        h2 = calculate_database_hash(db2)
        assert h1 == h2, "Identical seeds must produce byte-identical SHA-256 state hashes"

        # Different seed
        db3 = os.path.join(tmp1, "comp3.db")
        create_enterprise_database(db3, seed=99)
        h3 = calculate_database_hash(db3)
        assert h1 != h3, "Different seeds must produce distinct state hashes"
