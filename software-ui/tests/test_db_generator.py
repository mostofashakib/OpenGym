"""Tests for procedural database generation, edge case injection, and state hashing."""

import os
import tempfile
import pytest

from software.environment.software_sim.context import SoftwareContext
from software.environment.software_sim.db_generator import DatabaseGenerator
from software.environment.software_sim.domains import get_domain_spec


def test_db_generation_deterministic_hashing() -> None:
    spec = get_domain_spec("higher_ed")

    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        db1 = os.path.join(tmp1, "db1.db")
        db2 = os.path.join(tmp2, "db2.db")

        gen1 = DatabaseGenerator(spec, seed=99)
        hash1 = gen1.populate_database(db1, records_per_entity=15)

        gen2 = DatabaseGenerator(spec, seed=99)
        hash2 = gen2.populate_database(db2, records_per_entity=15)

        assert hash1 == hash2, "Identical seeds must yield identical SHA-256 database hashes"

        # Different seed must yield different hash
        db3 = os.path.join(tmp1, "db3.db")
        gen3 = DatabaseGenerator(spec, seed=100)
        hash3 = gen3.populate_database(db3, records_per_entity=15)
        assert hash1 != hash3


def test_state_hash_changes_after_mutation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        spec = get_domain_spec("equipment")
        gen = DatabaseGenerator(spec, seed=42)
        gen.populate_database(db_path, records_per_entity=10)

        ctx = SoftwareContext(db_path=db_path, app_spec=spec)
        initial_hash = ctx.service.calculate_state_hash()

        # Mutate an entity
        assets = ctx.service.search_entities("Asset", limit=1)
        assert len(assets) > 0
        ctx.service.update_entity(
            "Asset",
            assets[0]["id"],
            {"serial_no": "MODIFIED_SERIAL_123"},
        )

        mutated_hash = ctx.service.calculate_state_hash()
        assert initial_hash != mutated_hash, "State hash must change upon data mutation"
