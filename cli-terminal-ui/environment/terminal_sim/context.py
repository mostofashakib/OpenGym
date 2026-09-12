"""Dependency injection and workspace context representation for Terminal simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from terminal_sim.seed import seed_database
from terminal_sim.service import TerminalService
from terminal_sim.sqlite_common import get_connection

DEFAULT_DB_PATH = Path("/var/lib/terminal/terminal.db")


@dataclass(frozen=True)
class TerminalContext:
    """Dependency container representing a configured Terminal workspace instance."""

    db_path: Path = DEFAULT_DB_PATH

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> TerminalContext:
        """Resolve dependency configuration from environment variables with graceful fallback."""
        env = os.environ if environ is None else environ
        if "TERMINAL_DB" in env:
            db_path = Path(env["TERMINAL_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "terminal.db"

        return cls(db_path=db_path)

    def ensure_initialized(self) -> None:
        """Ensure database exists, seeding from snapshot if absent."""
        if not self.db_path.exists():
            self.seed()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action against the configured database."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            service = TerminalService(conn)
            res = service.execute_tool(tool_name, payload)
            conn.commit()
            return res

    def get_system(self) -> dict[str, Any]:
        """Retrieve aggregated system, process, service, and submission status."""
        self.ensure_initialized()
        sys_info = self.execute_tool("inspect_system", {})
        with get_connection(self.db_path) as conn:
            procs = conn.execute(
                "SELECT pid, name, command, user, cpu_percent, memory_mb, status FROM processes WHERE status != 'terminated' ORDER BY cpu_percent DESC"
            ).fetchall()
            proc_list = [dict(row) for row in procs]
            services = conn.execute("SELECT name, status, description, pid, enabled FROM services").fetchall()
            svc_list = [dict(row) for row in services]
            sub = conn.execute("SELECT id, timestamp, summary, actions_taken FROM task_submission WHERE id = 1").fetchone()
            sub_info = dict(sub) if sub else {"submitted": 0}

            return {
                "system": sys_info,
                "processes": proc_list,
                "services": svc_list,
                "submission": sub_info,
            }

    def list_files(self, directory: str = "/") -> list[dict[str, Any]]:
        """Retrieve list of files in the virtual filesystem."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT path, owner, group_owner, permissions, file_type, size, modified_at FROM files ORDER BY path ASC"
            ).fetchall()
            return [dict(row) for row in rows]

    def seed(self) -> None:
        """Seed or reset the workspace from scratch."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        seed_database(self.db_path)

