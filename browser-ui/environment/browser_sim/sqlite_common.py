"""SQLite database schema and utilities for browser simulation."""

from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path
from typing import Iterator

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL,
    item TEXT NOT NULL,
    amount REAL NOT NULL,
    requested_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
    rejection_reason TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    risk_level TEXT NOT NULL DEFAULT 'LOW',
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    notes TEXT NOT NULL,
    soc2_certified INTEGER NOT NULL DEFAULT 1,
    soc2_cert_id TEXT,
    soc2_expires TEXT
);

CREATE TABLE IF NOT EXISTS compliance_filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id TEXT NOT NULL,
    cert_type TEXT NOT NULL,
    cert_reference TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED',
    submitted_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS browser_session (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    current_url TEXT NOT NULL DEFAULT 'https://procure.corp/dashboard',
    history_json TEXT NOT NULL DEFAULT '["https://procure.corp/dashboard"]'
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
    audited_ids TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_vendors_status ON vendors(status);
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
