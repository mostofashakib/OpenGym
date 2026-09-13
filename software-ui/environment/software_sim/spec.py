"""Declarative specifications for procedurally generated software applications."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    TEXT = "text"
    DATETIME = "datetime"
    FOREIGN_KEY = "foreign_key"
    JSON = "json"


class RelationType(str, Enum):
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    PARENT_CHILD = "parent_child"
    DEPENDS_ON = "depends_on"


class UILayoutFamily(str, Enum):
    SIDEBAR_TABLE = "sidebar_table"
    NESTED_TREE_CARDS = "nested_tree_cards"
    SPLIT_WORKSPACE = "split_workspace"
    TABBED_BOARD = "tabbed_board"


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    field_type: FieldType
    required: bool = True
    default: Any = None
    enum_values: tuple[str, ...] = ()
    foreign_entity: str | None = None
    description: str = ""

    @property
    def is_primary_key(self) -> bool:
        return self.name == "id"

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type.value,
            "required": self.required,
            "default": self.default,
            "enum_values": list(self.enum_values),
            "foreign_entity": self.foreign_entity,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class WorkflowTransition:
    name: str
    from_state: str
    to_state: str
    required_roles: tuple[str, ...] = ("admin", "operator")
    required_fields: tuple[str, ...] = ()
    prerequisite_conditions: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @property
    def action(self) -> str:
        return self.name

    @property
    def allowed_roles(self) -> tuple[str, ...]:
        return self.required_roles

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "required_roles": list(self.required_roles),
            "required_fields": list(self.required_fields),
            "prerequisite_conditions": self.prerequisite_conditions,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class WorkflowSpec:
    entity_name: str
    initial_state: str
    terminal_states: tuple[str, ...]
    transitions: tuple[WorkflowTransition, ...]

    @property
    def states(self) -> tuple[str, ...]:
        all_states = [self.initial_state, *self.terminal_states]
        for t in self.transitions:
            all_states.extend([t.from_state, t.to_state])
        return tuple(dict.fromkeys(all_states))

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "initial_state": self.initial_state,
            "terminal_states": list(self.terminal_states),
            "transitions": [t.as_dict() for t in self.transitions],
        }


@dataclass(frozen=True, slots=True)
class EntitySpec:
    name: str
    plural_name: str
    description: str
    fields: tuple[FieldSpec, ...]
    lifecycle_states: tuple[str, ...] = ()
    primary_key: str = "id"
    workflow: WorkflowSpec | None = None

    def as_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "name": self.name,
            "plural_name": self.plural_name,
            "description": self.description,
            "fields": [f.as_dict() for f in self.fields],
            "lifecycle_states": list(self.lifecycle_states),
            "primary_key": self.primary_key,
        }
        if self.workflow is not None:
            res["workflow"] = self.workflow.as_dict()
        return res


@dataclass(frozen=True, slots=True)
class RelationshipSpec:
    source_entity: str
    target_entity: str
    relation_type: RelationType
    foreign_key_name: str
    description: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_entity": self.source_entity,
            "target_entity": self.target_entity,
            "relation_type": self.relation_type.value,
            "foreign_key_name": self.foreign_key_name,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class RoleSpec:
    name: str
    description: str
    permissions: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
        }


@dataclass(frozen=True, slots=True)
class UILayoutSpec:
    layout_family: UILayoutFamily
    terminology_map: dict[str, str] = field(default_factory=dict)
    visible_columns: dict[str, tuple[str, ...]] = field(default_factory=dict)
    filter_fields: dict[str, tuple[str, ...]] = field(default_factory=dict)
    pagination_size: int = 25

    @property
    def navigation_style(self) -> str:
        fam = self.layout_family.value
        if "sidebar" in fam:
            return "sidebar"
        elif "nested" in fam or "tree" in fam:
            return "nested_tree"
        elif "split" in fam:
            return "split_view"
        return "top_nav"

    def as_dict(self) -> dict[str, Any]:
        return {
            "layout_family": self.layout_family.value,
            "terminology_map": self.terminology_map,
            "visible_columns": {k: list(v) for k, v in self.visible_columns.items()},
            "filter_fields": {k: list(v) for k, v in self.filter_fields.items()},
            "pagination_size": self.pagination_size,
        }


@dataclass(frozen=True, slots=True)
class AppSpec:
    name: str
    domain: str
    description: str
    seed: int
    entities: tuple[EntitySpec, ...]
    workflows: tuple[WorkflowSpec, ...]
    relationships: tuple[RelationshipSpec, ...]
    roles: tuple[RoleSpec, ...]
    layout: UILayoutSpec

    @property
    def ui_layout(self) -> UILayoutSpec:
        return self.layout

    def model_dump_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "seed": self.seed,
            "entities": [e.as_dict() for e in self.entities],
            "workflows": [w.as_dict() for w in self.workflows],
            "relationships": [r.as_dict() for r in self.relationships],
            "roles": [r.as_dict() for r in self.roles],
            "layout": self.layout.as_dict(),
        }
