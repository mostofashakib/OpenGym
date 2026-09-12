"""Dependency injection and workspace context representation for Browser simulation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from browser_sim.seed import seed_database
from browser_sim.service import BrowserService, export_state
from browser_sim.sqlite_common import get_connection

DEFAULT_DB_PATH = Path("/var/lib/browser/browser.db")


@dataclass(frozen=True)
class BrowserContext:
    """Dependency container representing a configured Browser workspace instance."""

    db_path: Path = DEFAULT_DB_PATH

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> BrowserContext:
        """Resolve dependency configuration from environment variables with graceful fallback."""
        env = os.environ if environ is None else environ
        if "BROWSER_DB" in env:
            db_path = Path(env["BROWSER_DB"])
        elif DEFAULT_DB_PATH.parent.exists():
            db_path = DEFAULT_DB_PATH
        else:
            db_path = Path.cwd() / "browser.db"

        return cls(db_path=db_path)

    def ensure_initialized(self) -> None:
        """Ensure database exists, seeding from snapshot if absent."""
        if not self.db_path.exists():
            self.seed()

    def execute_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool action against the configured database."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            service = BrowserService(conn)
            res = service.execute_tool(tool_name, payload)
            conn.commit()
            return res

    def export_state(self) -> dict[str, Any]:
        """Export the full state of the configured database."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            return export_state(conn)

    def get_dashboard(self) -> dict[str, Any]:
        """Retrieve aggregated dashboard data for the browser UI."""
        self.ensure_initialized()
        with get_connection(self.db_path) as conn:
            orders = [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()]
            vendors = [dict(r) for r in conn.execute("SELECT * FROM vendors ORDER BY id ASC").fetchall()]
            filings = [dict(r) for r in conn.execute("SELECT * FROM compliance_filings ORDER BY id DESC").fetchall()]
            sub_row = conn.execute("SELECT id, timestamp, summary, audited_ids FROM task_submission WHERE id = 1").fetchone()
            submission = dict(sub_row) if sub_row else None
            logs = [dict(r) for r in conn.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT 10").fetchall()]

            return {
                "orders": orders,
                "vendors": vendors,
                "compliance_filings": filings,
                "submission": submission,
                "recent_actions": logs,
                "stats": {
                    "pending_orders": sum(1 for o in orders if o["status"] == "PENDING_APPROVAL"),
                    "high_risk_vendors": sum(1 for v in vendors if v["risk_level"] in ("CRITICAL", "HIGH")),
                    "expired_soc2": sum(1 for v in vendors if v["soc2_certified"] == 0),
                    "total_pending_amount": sum(o["amount"] for o in orders if o["status"] == "PENDING_APPROVAL"),
                },
            }

    def seed(self) -> None:
        """Seed or reset the workspace from scratch."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        seed_database(self.db_path)

