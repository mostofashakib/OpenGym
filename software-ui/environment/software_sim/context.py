"""Dependency container and context representation for generated software applications."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .db_generator import create_dynamic_database
from .generalization import create_app_for_split
from .service import (
    SoftwareService,
    calculate_state_hash,
    create_entity,
    export_state,
    get_audit_log,
    get_entity,
    get_schema,
    search_entities,
    transition_entity,
    update_entity,
)
from .spec import AppSpec

DEFAULT_DB_PATH = Path("/var/lib/software/app.db")


@dataclass
class SoftwareContext:
    """Dependency container managing a generated application workspace."""

    db_path: Path | str = DEFAULT_DB_PATH
    domain: str = "logistics"
    split: str = "iid"
    seed: int = 42
    actor: str = "agent_operator"
    actor_role: str = "admin"
    app_spec: AppSpec | None = None
    app_spec_path: Path | str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.db_path, str):
            object.__setattr__(self, "db_path", Path(self.db_path))
        if isinstance(self.app_spec_path, str):
            object.__setattr__(self, "app_spec_path", Path(self.app_spec_path))

    @property
    def service(self) -> SoftwareService:
        return SoftwareService(self.db_path, spec=self.app_spec)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> SoftwareContext:
        env = os.environ if environ is None else environ
        if "SOFTWARE_DB" in env:
            db_path = Path(env["SOFTWARE_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "software.db"

        domain = env.get("SOFTWARE_DOMAIN", "logistics")
        split = env.get("SOFTWARE_SPLIT", "iid")
        seed = int(env.get("SOFTWARE_SEED", "42"))
        actor = env.get("SOFTWARE_ACTOR", "agent_operator")
        actor_role = env.get("SOFTWARE_ROLE", "admin")
        return cls(db_path=db_path, domain=domain, split=split, seed=seed, actor=actor, actor_role=actor_role)

    def ensure_initialized(self) -> None:
        if not Path(self.db_path).exists():
            self.seed_app()

    def seed_app(self) -> dict[str, Any]:
        if isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        spec = self.app_spec or create_app_for_split(split=self.split, seed=self.seed, domain=self.domain)
        return create_dynamic_database(self.db_path, spec)

    def reset(self, domain: str | None = None, seed: int | None = None, split: str | None = None) -> dict[str, Any]:
        """Reset and reseed database for a new episode."""
        if domain is not None:
            self.domain = domain
        if seed is not None:
            self.seed = seed
        if split is not None:
            self.split = split
        db_p = Path(self.db_path)
        if db_p.exists():
            db_p.unlink()
        return self.seed_app()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.ensure_initialized()
        if tool_name == "get_schema":
            return get_schema(self.db_path)
        elif tool_name == "search_entities":
            return search_entities(
                self.db_path,
                payload["entity_name"],
                payload.get("query", ""),
                payload.get("filters"),
                payload.get("sort_by"),
                payload.get("page", 1),
                payload.get("page_size", 25),
            )
        elif tool_name == "get_entity":
            return get_entity(self.db_path, payload["entity_name"], payload["entity_id"])
        elif tool_name == "create_entity":
            return create_entity(self.db_path, payload["entity_name"], payload["fields"])
        elif tool_name == "update_entity":
            return update_entity(self.db_path, payload["entity_name"], payload["entity_id"], payload["fields"])
        elif tool_name == "transition_entity":
            return transition_entity(
                self.db_path,
                payload["entity_name"],
                payload["entity_id"],
                payload["action"],
                actor_role=self.actor_role,
                fields=payload.get("fields"),
            )
        elif tool_name == "get_audit_log":
            return {"audit_log": get_audit_log(self.db_path)}
        else:
            raise ValueError(f"Unknown tool '{tool_name}'.")

    def export_state(self) -> dict[str, Any]:
        self.ensure_initialized()
        return export_state(self.db_path)

    def calculate_state_hash(self) -> str:
        self.ensure_initialized()
        return calculate_state_hash(self.db_path)
