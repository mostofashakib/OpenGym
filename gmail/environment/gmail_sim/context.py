"""Dependency injection and workspace context representation for Gmail simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from gmail_sim.seed import seed_database
from gmail_sim.service import DEFAULT_DB_PATH, DEFAULT_SNAPSHOT_PATH, execute_tool, export_state
from gmail_sim.sqlite_common import get_connection


@dataclass(frozen=True)
class GmailContext:
    """Dependency container representing a configured Gmail workspace instance."""

    db_path: Path = DEFAULT_DB_PATH
    snapshot_path: Path | None = DEFAULT_SNAPSHOT_PATH
    scenario: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> GmailContext:
        """Resolve dependency configuration from environment variables with graceful fallback."""
        env = os.environ if environ is None else environ
        if "GMAIL_DB" in env:
            db_path = Path(env["GMAIL_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "gmail.db"

        if "GMAIL_SNAPSHOT" in env:
            snapshot_path: Path | None = Path(env["GMAIL_SNAPSHOT"])
        elif DEFAULT_SNAPSHOT_PATH.exists():
            snapshot_path = DEFAULT_SNAPSHOT_PATH
        else:
            snapshot_path = None

        scenario = env.get("GMAIL_SCENARIO")
        return cls(db_path=db_path, snapshot_path=snapshot_path, scenario=scenario)

    def ensure_initialized(self) -> None:
        """Ensure database exists, seeding from snapshot or scratch if absent."""
        if not self.db_path.exists():
            self.seed()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action against the configured database."""
        self.ensure_initialized()
        return execute_tool(self.db_path, tool_name, payload)

    def export_state(self) -> dict[str, Any]:
        """Export the full state of the configured database."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            return export_state(conn)

    def seed(self) -> None:
        """Seed or reset the workspace from scratch or snapshot."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        seed_database(self.db_path, self.snapshot_path)
