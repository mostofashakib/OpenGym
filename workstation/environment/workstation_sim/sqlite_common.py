"""Authoritative SQLite database schema and connection management for Workstation simulation."""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    department TEXT NOT NULL,
    manager_id TEXT,
    phone TEXT NOT NULL DEFAULT '',
    permissions TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    account_tier TEXT NOT NULL DEFAULT 'standard',
    status TEXT NOT NULL DEFAULT 'active',
    phone TEXT NOT NULL DEFAULT '',
    primary_contact_id TEXT,
    msa_date TEXT NOT NULL DEFAULT '',
    created_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    is_primary INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS crm_deals (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    title TEXT NOT NULL,
    value_cents INTEGER NOT NULL DEFAULT 0,
    stage TEXT NOT NULL DEFAULT 'prospect',
    owner_id TEXT NOT NULL,
    close_date TEXT NOT NULL DEFAULT '',
    contract_file_id TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(id),
    FOREIGN KEY(owner_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS crm_activity_logs (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    body TEXT NOT NULL,
    created_ts TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS email_threads (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL DEFAULT '',
    customer_id TEXT,
    last_activity_iso TEXT NOT NULL,
    snippet TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    from_addr TEXT NOT NULL,
    to_addrs TEXT NOT NULL DEFAULT '[]',
    cc_addrs TEXT NOT NULL DEFAULT '[]',
    bcc_addrs TEXT NOT NULL DEFAULT '[]',
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    date_iso TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    is_starred INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    is_trash INTEGER NOT NULL DEFAULT 0,
    folder TEXT NOT NULL DEFAULT 'inbox',
    attachments TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(thread_id) REFERENCES email_threads(id)
);

CREATE TABLE IF NOT EXISTS email_drafts (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    to_addrs TEXT NOT NULL DEFAULT '[]',
    cc_addrs TEXT NOT NULL DEFAULT '[]',
    bcc_addrs TEXT NOT NULL DEFAULT '[]',
    subject TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    updated_iso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    organizer_email TEXT NOT NULL,
    start_iso TEXT NOT NULL,
    end_iso TEXT NOT NULL,
    location TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'confirmed',
    attendees TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    virtual_path TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL DEFAULT 'text/plain',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    owner_email TEXT NOT NULL,
    customer_id TEXT,
    content_text TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    created_iso TEXT NOT NULL,
    updated_iso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    requester_email TEXT NOT NULL,
    assignee_id TEXT,
    subject TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'open',
    created_iso TEXT NOT NULL,
    updated_iso TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS ticket_comments (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    author_email TEXT NOT NULL,
    body TEXT NOT NULL,
    is_internal INTEGER NOT NULL DEFAULT 0,
    created_iso TEXT NOT NULL,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    invoice_number TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'unpaid',
    issued_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    paid_date TEXT,
    items TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS refunds (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'completed',
    processed_by TEXT NOT NULL,
    created_iso TEXT NOT NULL,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id),
    FOREIGN KEY(customer_id) REFERENCES customers(id)
);

CREATE TABLE IF NOT EXISTS kb_articles (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    author_id TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    updated_iso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS browser_history (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    visited_iso TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_iso TEXT NOT NULL,
    actor TEXT NOT NULL,
    application TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL DEFAULT '',
    target_id TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS scenario_rules (
    rule_id TEXT PRIMARY KEY,
    trigger_event TEXT NOT NULL,
    condition_json TEXT NOT NULL DEFAULT '{}',
    action_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS latent_events (
    event_id TEXT PRIMARY KEY,
    trigger_type TEXT NOT NULL,
    condition_json TEXT NOT NULL DEFAULT '{}',
    payload_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    activated_at_iso TEXT
);

CREATE TABLE IF NOT EXISTS disturbances (
    id TEXT PRIMARY KEY,
    disturbance_type TEXT NOT NULL,
    trigger_at_tick INTEGER NOT NULL DEFAULT 0,
    probability REAL NOT NULL DEFAULT 1.0,
    payload_json TEXT NOT NULL DEFAULT '{}',
    has_fired INTEGER NOT NULL DEFAULT 0
);
"""


@contextlib.contextmanager
def connect(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    """Connect to SQLite database with WAL and foreign keys enabled."""
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(conn: sqlite3.Connection) -> None:
    """Create all schema tables if not existing."""
    conn.executescript(SCHEMA)


def query_rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Execute query and return list of dictionaries."""
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


def get_system_state(conn: sqlite3.Connection, key: str, default: str = "") -> str:
    """Read a system state property."""
    row = conn.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row else default


def set_system_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Upsert a system state property."""
    conn.execute(
        "INSERT INTO system_state (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def calculate_database_hash(conn: sqlite3.Connection) -> str:
    """Computes a deterministic, canonical SHA-256 hash over the entire SQLite database.
    
    Excludes non-reproducible dynamic action logs so seed state is reproducible.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name NOT IN ('action_logs') "
        "ORDER BY name ASC;"
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    hasher = hashlib.sha256()
    for table in tables:
        hasher.update(table.encode("utf-8"))
        cursor.execute(f"PRAGMA table_info('{table}');")
        cols = [col[1] for col in cursor.fetchall()]
        first_col = cols[0] if cols else "rowid"
        cursor.execute(f"SELECT * FROM '{table}' ORDER BY {first_col} ASC;")
        rows = cursor.fetchall()
        for row in rows:
            row_repr = json.dumps(list(row), sort_keys=True, ensure_ascii=True, default=str)
            hasher.update(row_repr.encode("utf-8"))
            
    return hasher.hexdigest()
