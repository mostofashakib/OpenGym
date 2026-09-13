"""Dependency injection and workspace context representation for Workstation simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from workstation_sim.seed import seed_database
from workstation_sim.service import DEFAULT_ACTOR, calculate_state_hash, execute_tool, export_state

DEFAULT_DB_PATH = Path("/var/lib/workstation/workstation.db")


@dataclass(frozen=True)
class WorkstationContext:
    """Dependency container representing a configured Workstation workspace instance."""

    db_path: Path = DEFAULT_DB_PATH
    actor: str = DEFAULT_ACTOR
    task_id: str = "account-cancellation-refund"
    seed: int = 42

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> WorkstationContext:
        """Resolve dependency configuration from environment variables."""
        env = os.environ if environ is None else environ
        if "WORKSTATION_DB" in env:
            db_path = Path(env["WORKSTATION_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "workstation.db"

        actor = env.get("WORKSTATION_ACTOR", DEFAULT_ACTOR)
        task_id = env.get("WORKSTATION_TASK_ID", "account-cancellation-refund")
        seed = int(env.get("WORKSTATION_SEED", "42"))
        return cls(db_path=db_path, actor=actor, task_id=task_id, seed=seed)

    def ensure_initialized(self) -> None:
        """Ensure database exists, seeding from scratch if absent."""
        if not self.db_path.exists():
            self.seed_db()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action against the configured database."""
        self.ensure_initialized()
        return execute_tool(self.db_path, tool_name, payload, actor=self.actor)

    def export_state(self) -> dict[str, Any]:
        """Export the full state of the configured database."""
        self.ensure_initialized()
        return export_state(self.db_path)

    def calculate_state_hash(self) -> str:
        """Calculate state hash for determinism verification."""
        self.ensure_initialized()
        return calculate_state_hash(self.db_path)

    def seed_db(self) -> dict[str, Any]:
        """Populate database with deterministic initial state."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return seed_database(self.db_path, seed=self.seed, task_id=self.task_id)
