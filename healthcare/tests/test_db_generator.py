"""Tests for relational database schema compilation, synthetic patient generation, and state hashing."""

import os
import sqlite3
import tempfile
import pytest

from healthcare.environment.healthcare_sim.context import HealthcareContext
from healthcare.environment.healthcare_sim.db_generator import (
    calculate_database_hash,
    create_dynamic_database,
)


def test_database_seeding_and_counts() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        res = create_dynamic_database(db_path, seed=42)

        counts = res["counts"]
        assert counts["patients"] == 1000, "Should generate exactly 1,000 synthetic patients"
        assert counts["allergies"] > 250, "Should generate realistic allergy anchor distribution"
        assert counts["encounters"] > 3000, "Should have longitudinal multi-year visits"
        assert counts["observations"] > 5000, "Should have longitudinal labs and vitals"

        conn = sqlite3.connect(db_path)
        staff_count = conn.execute("SELECT COUNT(*) FROM practitioners").fetchone()[0]
        assert staff_count == 50, "Should generate exactly 50 healthcare staff members"

        facilities_count = conn.execute("SELECT COUNT(*) FROM facilities").fetchone()[0]
        assert facilities_count == 4, "Should generate 4 clinical facilities"
        conn.close()


def test_deterministic_state_hashing() -> None:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        db1 = os.path.join(tmp1, "db1.db")
        db2 = os.path.join(tmp2, "db2.db")

        create_dynamic_database(db1, seed=123)
        create_dynamic_database(db2, seed=123)

        h1 = calculate_database_hash(db1)
        h2 = calculate_database_hash(db2)
        assert h1 == h2, "Identical seeds must produce byte-identical SHA-256 database hashes"

        # Different seed produces different hash
        db3 = os.path.join(tmp1, "db3.db")
        create_dynamic_database(db3, seed=124)
        h3 = calculate_database_hash(db3)
        assert h1 != h3, "Different seeds must produce different database hashes"


def test_state_hash_mutation() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        create_dynamic_database(db_path, seed=42)
        ctx = HealthcareContext(db_path=db_path)

        initial_hash = ctx.service.calculate_state_hash()

        # Mutate a patient record
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE patients SET phone = '555-999-0000' WHERE id = 'pat-0001'")
        conn.commit()
        conn.close()

        mutated_hash = ctx.service.calculate_state_hash()
        assert initial_hash != mutated_hash, "State hash must mutate when data changes"
