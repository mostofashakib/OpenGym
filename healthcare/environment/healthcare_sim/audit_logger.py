"""Audit logging system tracking all patient chart reads, writes, and disclosures."""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict, List, Optional


def init_audit_table(conn: sqlite3.Connection) -> None:
    """Initialize audit_events table."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_iso TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL DEFAULT '',
            action TEXT NOT NULL,  -- 'read', 'search', 'create', 'update', 'schedule', 'escalate', 'disclose'
            purpose_of_use TEXT NOT NULL DEFAULT 'treatment',  -- 'treatment', 'operations', 'payment', 'unspecified'
            authorized INTEGER NOT NULL DEFAULT 1,
            details_json TEXT NOT NULL DEFAULT '{}'
        );"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_patient ON audit_events(patient_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_events(actor_id);")


def log_audit_event(
    conn: sqlite3.Connection,
    timestamp_iso: str,
    actor_id: str,
    actor_role: str,
    patient_id: str,
    resource_type: str,
    action: str,
    resource_id: str = "",
    purpose_of_use: str = "treatment",
    authorized: bool = True,
    details: Optional[Dict[str, Any]] = None,
) -> int:
    """Record an audit trail event for every chart interaction."""
    cur = conn.execute(
        """INSERT INTO audit_events (
            timestamp_iso, actor_id, actor_role, patient_id, resource_type,
            resource_id, action, purpose_of_use, authorized, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            timestamp_iso,
            actor_id,
            actor_role,
            patient_id,
            resource_type,
            resource_id,
            action,
            purpose_of_use,
            1 if authorized else 0,
            json.dumps(details or {}),
        ),
    )
    return int(cur.lastrowid or 0)


def get_audit_trail(
    conn: sqlite3.Connection,
    patient_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Query audit trail with optional filtering."""
    query = "SELECT * FROM audit_events"
    conditions = []
    params: List[Any] = []

    if patient_id:
        conditions.append("patient_id = ?")
        params.append(patient_id)
    if actor_id:
        conditions.append("actor_id = ?")
        params.append(actor_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id ASC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, tuple(params)).fetchall()
    results = []
    for r in rows:
        results.append(
            {
                "id": r["id"],
                "timestamp_iso": r["timestamp_iso"],
                "actor_id": r["actor_id"],
                "actor_role": r["actor_role"],
                "patient_id": r["patient_id"],
                "resource_type": r["resource_type"],
                "resource_id": r["resource_id"],
                "action": r["action"],
                "purpose_of_use": r["purpose_of_use"],
                "authorized": bool(r["authorized"]),
                "details": json.loads(r["details_json"] or "{}"),
            }
        )
    return results
