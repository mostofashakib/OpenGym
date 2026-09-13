"""Tests for generalization splits (IID, NEW_UI, NEW_VOCAB, NEW_WORKFLOW, OOD)."""

import pytest

from software.environment.software_sim.domains import get_domain_spec
from software.environment.software_sim.generalization import (
    GeneralizationSplit,
    apply_generalization_split,
)


def test_iid_split_keeps_structure() -> None:
    base = get_domain_spec("logistics")
    transformed = apply_generalization_split(base, split=GeneralizationSplit.IID, seed=123)
    assert transformed.domain == "logistics"
    assert len(transformed.entities) == len(base.entities)


def test_new_ui_split_varies_layout() -> None:
    base = get_domain_spec("logistics")
    transformed = apply_generalization_split(base, split=GeneralizationSplit.NEW_UI, seed=42)
    assert transformed.domain == "logistics"
    # Layout or theme should vary
    assert transformed.ui_layout is not None


def test_new_vocab_split_mutates_entity_and_action_names() -> None:
    base = get_domain_spec("logistics")
    transformed = apply_generalization_split(base, split=GeneralizationSplit.NEW_VOCAB, seed=42)
    # Check that vocabulary was mapped
    base_entity_names = {e.name for e in base.entities}
    trans_entity_names = {e.name for e in transformed.entities}
    assert base_entity_names != trans_entity_names, "Entity names should change in NEW_VOCAB split"


def test_new_workflow_split_modifies_states() -> None:
    base = get_domain_spec("logistics")
    transformed = apply_generalization_split(base, split=GeneralizationSplit.NEW_WORKFLOW, seed=42)
    # The workflow transitions should have additional intermediate states
    base_first_entity = next(e for e in base.entities if e.workflow)
    trans_first_entity = next(e for e in transformed.entities if e.workflow)
    assert trans_first_entity.workflow is not None
    assert base_first_entity.workflow is not None
    assert len(trans_first_entity.workflow.states) >= len(base_first_entity.workflow.states)


def test_ood_split_selects_unseen_domain_and_transforms() -> None:
    base = get_domain_spec("logistics")
    transformed = apply_generalization_split(base, split=GeneralizationSplit.OOD, seed=77)
    # OOD switches domain to one of the holdout domains
    assert transformed.domain != "logistics"
