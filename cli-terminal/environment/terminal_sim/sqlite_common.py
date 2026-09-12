"""SQLite database utilities for terminal simulation."""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import Iterator


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    owner TEXT NOT NULL DEFAULT 'root',
    group_owner TEXT NOT NULL DEFAULT 'root',
    permissions TEXT NOT NULL DEFAULT '0644',
    file_type TEXT NOT NULL DEFAULT 'file',
    size INTEGER NOT NULL DEFAULT 0,
    modified_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS processes (
    pid INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    command TEXT NOT NULL,
    user TEXT NOT NULL DEFAULT 'root',
    cpu_percent REAL NOT NULL DEFAULT 0.0,
    memory_mb REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'running',
    started_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
    name TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'active',
    description TEXT NOT NULL,
    pid INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    disk_total_mb INTEGER NOT NULL DEFAULT 20480,
    disk_used_mb INTEGER NOT NULL DEFAULT 19800,
    memory_total_mb INTEGER NOT NULL DEFAULT 8192,
    memory_used_mb INTEGER NOT NULL DEFAULT 4200
);

CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    tool TEXT NOT NULL,
    arguments TEXT NOT NULL,
    result TEXT NOT NULL,
    actor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenario_rules (
    rule_id TEXT PRIMARY KEY,
    trigger TEXT NOT NULL,
    condition TEXT NOT NULL,
    effect TEXT NOT NULL,
    activated INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS event_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    event_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    result TEXT NOT NULL,
    detail TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_submission (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    timestamp REAL NOT NULL,
    summary TEXT NOT NULL,
    actions_taken TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_processes_status ON processes(status);
CREATE INDEX IF NOT EXISTS idx_action_log_tool ON action_log(tool);
"""


def init_db(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


@contextlib.contextmanager
def get_connection(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
