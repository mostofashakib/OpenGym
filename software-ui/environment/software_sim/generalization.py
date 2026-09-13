"""Generalization split manager for benchmark training vs evaluation splits."""

from __future__ import annotations

import random
from enum import Enum
from typing import Any

from .domains import ALL_DOMAIN_KEYS, get_domain_template
from .spec import (
    AppSpec,
    EntitySpec,
    FieldSpec,
    RelationshipSpec,
    UILayoutFamily,
    UILayoutSpec,
    WorkflowSpec,
    WorkflowTransition,
)


class GeneralizationSplit(str, Enum):
    IID = "iid"
    NEW_UI = "new_ui"
    NEW_VOCAB = "new_vocab"
    NEW_WORKFLOW = "new_workflow"
    OOD = "ood"


def create_app_for_split(
    split: str = "iid",
    seed: int = 42,
    domain: str = "logistics",
) -> AppSpec:
    """Generate an application specification tailored to a specific generalization test split."""
    rng = random.Random(seed)
    split_enum = GeneralizationSplit(split.lower())

    if split_enum == GeneralizationSplit.IID:
        base = get_domain_template(domain, seed=seed)
        return base

    elif split_enum == GeneralizationSplit.NEW_UI:
        base = get_domain_template(domain, seed=seed)
        layouts = [l for l in UILayoutFamily if l != base.layout.layout_family]
        new_layout_family = rng.choice(layouts)
        new_layout = UILayoutSpec(
            layout_family=new_layout_family,
            terminology_map={
                e.name: f"{e.name}_CardView" if new_layout_family == UILayoutFamily.NESTED_TREE_CARDS else f"Workspace_{e.name}"
                for e in base.entities
            },
            pagination_size=15,
        )
        return AppSpec(
            name=f"{base.name} (Alternative UI)",
            domain=base.domain,
            description=base.description,
            seed=seed,
            entities=base.entities,
            workflows=base.workflows,
            relationships=base.relationships,
            roles=base.roles,
            layout=new_layout,
        )

    elif split_enum == GeneralizationSplit.NEW_VOCAB:
        base = get_domain_template(domain, seed=seed)
        # Vocabulary mapping dictionary for isomorphic concept translation
        synth_vocab = [
            ("AlphaUnit", "AlphaUnits"), ("BravoHub", "BravoHubs"),
            ("CharlieNode", "CharlieNodes"), ("DeltaIncident", "DeltaIncidents"),
            ("EchoRecord", "EchoRecords")
        ]
        name_map = {}
        new_entities: list[EntitySpec] = []
        for i, ent in enumerate(base.entities):
            syn_name, syn_plural = synth_vocab[i % len(synth_vocab)]
            name_map[ent.name] = syn_name

            new_fields = []
            for f in ent.fields:
                f_target = name_map.get(f.foreign_entity, f.foreign_entity) if f.foreign_entity else None
                new_fields.append(
                    FieldSpec(
                        name=f.name,
                        field_type=f.field_type,
                        required=f.required,
                        default=f.default,
                        enum_values=f.enum_values,
                        foreign_entity=f_target,
                    )
                )
            new_entities.append(
                EntitySpec(
                    name=syn_name,
                    plural_name=syn_plural,
                    description=f"Abstract entity mapping to {ent.name}",
                    fields=tuple(new_fields),
                    lifecycle_states=ent.lifecycle_states,
                )
            )

        new_workflows: list[WorkflowSpec] = []
        for w in base.workflows:
            mapped_ent = name_map.get(w.entity_name, w.entity_name)
            new_workflows.append(
                WorkflowSpec(
                    entity_name=mapped_ent,
                    initial_state=w.initial_state,
                    terminal_states=w.terminal_states,
                    transitions=w.transitions,
                )
            )

        new_relationships: list[RelationshipSpec] = []
        for r in base.relationships:
            new_relationships.append(
                RelationshipSpec(
                    source_entity=name_map.get(r.source_entity, r.source_entity),
                    target_entity=name_map.get(r.target_entity, r.target_entity),
                    relation_type=r.relation_type,
                    foreign_key_name=r.foreign_key_name,
                )
            )

        return AppSpec(
            name=f"{base.name} (Novel Vocabulary)",
            domain=f"synthetic_{base.domain}",
            description="Isomorphic workflow mapped to unfamiliar synthetic terminology",
            seed=seed,
            entities=tuple(new_entities),
            workflows=tuple(new_workflows),
            relationships=tuple(new_relationships),
            roles=base.roles,
            layout=base.layout,
        )

    elif split_enum == GeneralizationSplit.NEW_WORKFLOW:
        base = get_domain_template(domain, seed=seed)
        # Introduce a multi-tier branched workflow with required peer review and rollback
        main_ent = base.entities[0].name
        branched_states = ("draft", "manager_approved", "compliance_hold", "audited", "terminal_closed")
        branched_transitions = (
            WorkflowTransition(name="pre_approve", from_state="draft", to_state="manager_approved", required_roles=("manager", "admin")),
            WorkflowTransition(name="flag_compliance", from_state="manager_approved", to_state="compliance_hold", required_roles=("operator", "admin")),
            WorkflowTransition(name="release_compliance", from_state="compliance_hold", to_state="audited", required_roles=("admin",)),
            WorkflowTransition(name="finalize", from_state="audited", to_state="terminal_closed", required_roles=("manager", "admin")),
        )
        new_workflow = WorkflowSpec(
            entity_name=main_ent,
            initial_state="draft",
            terminal_states=("terminal_closed",),
            transitions=branched_transitions,
        )
        return AppSpec(
            name=f"{base.name} (Novel Multi-Stage Workflow)",
            domain=base.domain,
            description="Novel branched compliance workflow topology",
            seed=seed,
            entities=base.entities,
            workflows=(new_workflow,),
            relationships=base.relationships,
            roles=base.roles,
            layout=base.layout,
        )

    elif split_enum == GeneralizationSplit.OOD:
        # Pick completely distinct domain from the 20 templates with random layout
        other_domains = [d for d in ALL_DOMAIN_KEYS if d != domain]
        chosen_domain = rng.choice(other_domains)
        base = get_domain_template(chosen_domain, seed=seed)
        random_layout = rng.choice(list(UILayoutFamily))
        return AppSpec(
            name=f"Out-of-Distribution {base.name}",
            domain=base.domain,
            description="Fully novel domain, schema, and layout combination",
            seed=seed,
            entities=base.entities,
            workflows=base.workflows,
            relationships=base.relationships,
            roles=base.roles,
            layout=UILayoutSpec(layout_family=random_layout),
        )

    return get_domain_template(domain, seed=seed)


def apply_generalization_split(
    spec: AppSpec,
    split: GeneralizationSplit | str = GeneralizationSplit.IID,
    seed: int = 42,
) -> AppSpec:
    """Apply generalization split transformation to a base AppSpec."""
    split_str = split.value if isinstance(split, GeneralizationSplit) else str(split)
    return create_app_for_split(split=split_str, seed=seed, domain=spec.domain)

