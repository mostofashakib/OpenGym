"""Deterministic virtual clock backed by SQLite system_state."""

from __future__ import annotations

import datetime
from pathlib import Path
import sqlite3
from workstation_sim.sqlite_common import connect, get_system_state, set_system_state

DEFAULT_ANCHOR_ISO = "2026-10-14T09:00:00Z"


class VirtualClock:
    """Virtual clock providing reproducible timestamps across episodes."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    def get_time(self, conn: sqlite3.Connection | None = None) -> datetime.datetime:
        if conn is not None:
            raw = get_system_state(conn, "virtual_time_iso", DEFAULT_ANCHOR_ISO)
        else:
            with connect(self.db_path) as c:
                raw = get_system_state(c, "virtual_time_iso", DEFAULT_ANCHOR_ISO)
        iso = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        return datetime.datetime.fromisoformat(iso)

    def get_time_iso(self, conn: sqlite3.Connection | None = None) -> str:
        return self.get_time(conn).strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int = 15, conn: sqlite3.Connection | None = None) -> str:
        current = self.get_time(conn)
        new_time = current + datetime.timedelta(seconds=seconds)
        new_iso = new_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        if conn is not None:
            set_system_state(conn, "virtual_time_iso", new_iso)
            tick = int(get_system_state(conn, "clock_ticks", "0")) + 1
            set_system_state(conn, "clock_ticks", str(tick))
        else:
            with connect(self.db_path) as c:
                set_system_state(c, "virtual_time_iso", new_iso)
                tick = int(get_system_state(c, "clock_ticks", "0")) + 1
                set_system_state(c, "clock_ticks", str(tick))
        return new_iso

    def set_time(self, iso: str, conn: sqlite3.Connection | None = None) -> None:
        if conn is not None:
            set_system_state(conn, "virtual_time_iso", iso)
        else:
            with connect(self.db_path) as c:
                set_system_state(c, "virtual_time_iso", iso)
