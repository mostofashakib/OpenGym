"""Dependency injection and workspace context representation for Slack simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from slack_sim.identity import LOGGED_IN_USER
from slack_sim.scenario import Scenario
from slack_sim.seed import ACME_SCENARIO
from slack_sim.service import (
    DEFAULT_DB_PATH,
    DEFAULT_SNAPSHOT_PATH,
    execute_tool,
    export_state,
    seed_database,
)


@dataclass(frozen=True)
class SlackContext:
    """Dependency container representing a configured Slack workspace instance."""

    db_path: Path = DEFAULT_DB_PATH
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH
    actor_id: str = LOGGED_IN_USER.user_id
    scenario: Scenario = ACME_SCENARIO

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> SlackContext:
        """Resolve dependency configuration from environment variables with graceful fallback."""
        env = os.environ if environ is None else environ
        if "SLACK_DB" in env:
            db_path = Path(env["SLACK_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "slack.db"

        if "SLACK_SNAPSHOT" in env:
            snapshot_path = Path(env["SLACK_SNAPSHOT"])
        elif DEFAULT_SNAPSHOT_PATH.exists():
            snapshot_path = DEFAULT_SNAPSHOT_PATH
        else:
            snapshot_path = Path.cwd() / "slack_seed_snapshot.sql"

        actor_id = env.get("SLACK_ACTOR_ID", LOGGED_IN_USER.user_id)
        return cls(db_path=db_path, snapshot_path=snapshot_path, actor_id=actor_id)

    def ensure_initialized(self) -> None:
        """Ensure database exists, seeding from snapshot if absent."""
        if not self.db_path.exists():
            self.seed()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action against the configured database."""
        self.ensure_initialized()
        return execute_tool(self.db_path, tool_name, payload, actor_id=self.actor_id)

    def export_state(self) -> dict[str, Any]:
        """Export the full state of the configured database."""
        self.ensure_initialized()
        return export_state(self.db_path)

    def seed(self) -> None:
        """Seed or reset the workspace from snapshot using the configured scenario."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        seed_database(self.db_path, self.snapshot_path, self.scenario)
