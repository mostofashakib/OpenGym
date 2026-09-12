"""Append-only action tracking in SQLite for layered verifiers."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from gmail_sim.clock import now


def log_action(
    conn: sqlite3.Connection,
    action: str,
    target_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    ts = now(conn)
    conn.execute(
        """
        INSERT INTO action_log (ts_iso, action, target_id, payload)
        VALUES (?, ?, ?, ?)
        """,
        (ts, action, target_id, json.dumps(payload or {}, sort_keys=True)),
    )


def get_actions(conn: sqlite3.Connection, action_name: str | None = None) -> list[dict[str, Any]]:
    if action_name:
        rows = conn.execute(
            "SELECT * FROM action_log WHERE action = ? ORDER BY id ASC", (action_name,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM action_log ORDER BY id ASC").fetchall()

    actions: list[dict[str, Any]] = []
    for r in rows:
        actions.append({
            "id": r["id"],
            "ts_iso": r["ts_iso"],
            "action": r["action"],
            "target_id": r["target_id"],
            "payload": json.loads(r["payload"]),
        })
    return actions
