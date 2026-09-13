"""Tests for all 20 procedural domain templates."""

import pytest

from software.environment.software_sim.domains import (
    DOMAIN_REGISTRY,
    get_all_domains,
    get_domain_spec,
)
from software.environment.software_sim.spec import AppSpec


def test_registry_contains_twenty_domains() -> None:
    domains = get_all_domains()
    assert len(domains) == 20, f"Expected 20 domains, got {len(domains)}"


@pytest.mark.parametrize("domain_name", list(DOMAIN_REGISTRY.keys()))
def test_domain_spec_integrity(domain_name: str) -> None:
    spec = get_domain_spec(domain_name)
    assert isinstance(spec, AppSpec)
    assert spec.domain == domain_name
    assert len(spec.name) > 0
    assert len(spec.entities) >= 2, f"Domain {domain_name} should define at least 2 entities"

    # Validate each entity
    for entity in spec.entities:
        assert len(entity.name) > 0
        assert len(entity.fields) >= 2, f"Entity {entity.name} should have at least 2 fields"
        assert any(f.is_primary_key for f in entity.fields), f"Entity {entity.name} must have primary key"

        if entity.workflow:
            assert len(entity.workflow.states) >= 2
            assert entity.workflow.initial_state in entity.workflow.states
            for t in entity.workflow.transitions:
                assert t.from_state in entity.workflow.states
                assert t.to_state in entity.workflow.states
                assert len(t.action) > 0
                assert len(t.allowed_roles) > 0

    # Validate roles
    assert len(spec.roles) >= 1
    assert any(r.name == "admin" for r in spec.roles)

    # Validate UI Layout
    assert spec.ui_layout is not None
    assert spec.ui_layout.navigation_style in ["sidebar", "top_nav", "nested_tree", "split_view"]
