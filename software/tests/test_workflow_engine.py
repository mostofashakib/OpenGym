"""Tests for StateMachineEngine workflow transitions and permission enforcement."""

import os
import tempfile
import pytest

from software.environment.software_sim.context import SoftwareContext
from software.environment.software_sim.db_generator import DatabaseGenerator
from software.environment.software_sim.domains import get_domain_spec


@pytest.fixture
def temp_software_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        spec = get_domain_spec("logistics")
        gen = DatabaseGenerator(spec, seed=42)
        gen.populate_database(db_path, records_per_entity=10)
        ctx = SoftwareContext(db_path=db_path, app_spec=spec)
        yield ctx, db_path


def test_valid_workflow_transition(temp_software_env) -> None:
    ctx, _ = temp_software_env
    # Find a Shipment in 'booked' status
    shipments = ctx.service.search_entities("Shipment", status_filter="booked", limit=1)
    assert len(shipments) > 0, "Should have booked shipment"
    shipment_id = shipments[0]["id"]

    # Dispatch shipment: booked -> in_transit
    result = ctx.service.transition_entity(
        entity_name="Shipment",
        entity_id=shipment_id,
        action="dispatch",
        actor="dispatcher_bob",
        actor_role="manager",
    )
    assert result["success"] is True
    assert result["new_status"] == "in_transit"

    # Verify updated in DB
    updated = ctx.service.get_entity("Shipment", shipment_id)
    assert updated is not None
    assert updated["status"] == "in_transit"

    # Check audit log
    logs = ctx.service.get_audit_log(entity_id=shipment_id)
    assert len(logs) >= 1
    assert logs[0]["action"] == "dispatch"
    assert logs[0]["from_state"] == "booked"
    assert logs[0]["to_state"] == "in_transit"


def test_invalid_transition_rejected(temp_software_env) -> None:
    ctx, _ = temp_software_env
    shipments = ctx.service.search_entities("Shipment", status_filter="booked", limit=1)
    assert len(shipments) > 0
    shipment_id = shipments[0]["id"]

    # Attempt to 'confirm_delivery' directly from 'booked' (must be out_for_delivery first)
    result = ctx.service.transition_entity(
        entity_name="Shipment",
        entity_id=shipment_id,
        action="confirm_delivery",
        actor="courier",
        actor_role="admin",
    )
    assert result["success"] is False
    assert "Invalid transition" in result["error"]


def test_unauthorized_role_rejected(temp_software_env) -> None:
    ctx, _ = temp_software_env
    shipments = ctx.service.search_entities("Shipment", status_filter="booked", limit=1)
    shipment_id = shipments[0]["id"]

    # Try dispatching with an unauthorized role (e.g. viewer or guest)
    result = ctx.service.transition_entity(
        entity_name="Shipment",
        entity_id=shipment_id,
        action="dispatch",
        actor="unauth_user",
        actor_role="viewer",
    )
    assert result["success"] is False
    assert "does not have permission" in result["error"]
