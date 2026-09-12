"""Authoritative SQLite database schema and connection management for Gmail simulation."""

from __future__ import annotations

import contextlib
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    display_name TEXT NOT NULL DEFAULT 'You',
    email TEXT NOT NULL DEFAULT 'you@example.com',
    signature TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS labels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'USER',
    color TEXT
);

CREATE TABLE IF NOT EXISTS threads (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL DEFAULT '',
    last_activity_iso TEXT NOT NULL,
    snippet TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    from_address TEXT NOT NULL,
    to_addresses TEXT NOT NULL DEFAULT '[]',
    cc_addresses TEXT NOT NULL DEFAULT '[]',
    bcc_addresses TEXT NOT NULL DEFAULT '[]',
    subject TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    html TEXT,
    date_iso TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    is_starred INTEGER NOT NULL DEFAULT 0,
    is_important INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    is_trash INTEGER NOT NULL DEFAULT 0,
    snooze_until TEXT,
    label_ids TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS drafts (
    id TEXT PRIMARY KEY,
    to_addresses TEXT NOT NULL DEFAULT '[]',
    cc_addresses TEXT NOT NULL DEFAULT '[]',
    bcc_addresses TEXT NOT NULL DEFAULT '[]',
    subject TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    html TEXT,
    date_iso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contacts (
    email TEXT PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS virtual_clock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    now_iso TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'America/Chicago',
    is_fixed INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_iso TEXT NOT NULL,
    action TEXT NOT NULL,
    target_id TEXT,
    payload TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_emails_thread ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_flags ON emails(is_read, is_starred, is_trash, is_archived);
"""


class WorldError(Exception):
    """Base exception for simulation environment errors."""
    code: str = "error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(WorldError):
    code = "not_found"


class ValidationError(WorldError):
    code = "validation_error"


class UnknownToolError(WorldError):
    code = "unknown_tool"


class InternalError(WorldError):
    code = "internal_error"


@contextlib.contextmanager
def storage_errors() -> Iterator[None]:
    try:
        yield
    except sqlite3.OperationalError as exc:
        raise InternalError(f"Database operational error: {exc}") from exc
    except sqlite3.IntegrityError as exc:
        raise ValidationError(f"Database integrity error: {exc}") from exc


@contextlib.contextmanager
def get_connection(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
    finally:
        conn.close()


def initialize_database(db_path: Path | str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as conn:
        conn.executescript(SCHEMA)
