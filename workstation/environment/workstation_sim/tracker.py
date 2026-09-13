"""Action tracking, audit logging, and reactive scenario evaluation for Workstation simulation."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from workstation_sim.clock import VirtualClock


def log_action(
    conn: sqlite3.Connection,
    clock: VirtualClock,
    actor: str,
    application: str,
    action: str,
    target_type: str = "",
    target_id: str = "",
    payload: dict[str, Any] | None = None,
) -> int:
    """Record an action into the authoritative append-only action_logs table."""
    ts = clock.get_time_iso(conn)
    cursor = conn.execute(
        """INSERT INTO action_logs (timestamp_iso, actor, application, action, target_type, target_id, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ts, actor, application, action, target_type, target_id, json.dumps(payload or {})),
    )
    return cursor.lastrowid or 0


def get_action_logs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve all logged actions in order."""
    rows = conn.execute("SELECT * FROM action_logs ORDER BY id ASC").fetchall()
    return [
        {
            "id": r["id"],
            "timestamp_iso": r["timestamp_iso"],
            "actor": r["actor"],
            "application": r["application"],
            "action": r["action"],
            "target_type": r["target_type"],
            "target_id": r["target_id"],
            "payload": json.loads(r["payload_json"]) if r["payload_json"] else {},
        }
        for r in rows
    ]
