"""SQLite-backed virtual clock for deterministic time travel."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FIXED_TIME = "2030-03-14T03:14:00-05:00"


def init_clock(conn: sqlite3.Connection, now_iso: str = DEFAULT_FIXED_TIME, tz: str = "America/Chicago") -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO virtual_clock (id, now_iso, timezone, is_fixed)
        VALUES (1, ?, ?, 1)
        """,
        (now_iso, tz),
    )


def now(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT now_iso FROM virtual_clock WHERE id = 1").fetchone()
    if row and row["now_iso"]:
        return str(row["now_iso"])
    return datetime.now(timezone.utc).isoformat()


def advance(conn: sqlite3.Connection, seconds: float) -> str:
    current = now(conn)
    # Simple ISO advance
    try:
        dt = datetime.fromisoformat(current)
        new_dt = datetime.fromtimestamp(dt.timestamp() + seconds, tz=dt.tzinfo)
        new_iso = new_dt.isoformat()
    except Exception:
        new_iso = current
    conn.execute("UPDATE virtual_clock SET now_iso = ? WHERE id = 1", (new_iso,))
    return new_iso
