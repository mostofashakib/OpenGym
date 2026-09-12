"""High-fidelity seed data for the browser environment."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from browser_sim.clock import VIRTUAL_CLOCK
from browser_sim.sqlite_common import init_db

INITIAL_ORDERS = [
    (
        "PO-9821",
        "VEND-GHOSTWIRE",
        "16x H100 SXM5 GPU Compute Cluster",
        480000.0,
        "dev-guest-02",
        "PENDING_APPROVAL",
        None,
        1773350000.0,
        1773350000.0,
    ),
    (
        "PO-3410",
        "VEND-CLOUDSCALE",
        "Enterprise Kubernetes License (Annual 128-node)",
        18500.0,
        "devops-lead",
        "PENDING_APPROVAL",
        None,
        1773351000.0,
        1773351000.0,
    ),
    (
        "PO-1022",
        "VEND-DELL",
        "27-inch UltraSharp 4K Monitors (x12)",
        7200.0,
        "office-manager",
        "APPROVED",
        None,
        1773340000.0,
        1773340000.0,
    ),
    (
        "PO-2045",
        "VEND-DATASYNC",
        "Cloud Backup Ingestion Tier 2",
        4200.0,
        "secops-analyst",
        "APPROVED",
        None,
        1773345000.0,
        1773345000.0,
    ),
]

INITIAL_VENDORS = [
    (
        "VEND-GHOSTWIRE",
        "GhostWire Hardware LLC",
        "CRITICAL",
        "PENDING_REVIEW",
        "Unverified offshore entity. Flagged by fraud heuristics for suspicious hardware requisitions.",
        0,
        None,
        None,
    ),
    (
        "VEND-CLOUDSCALE",
        "CloudScale Systems Inc.",
        "LOW",
        "ACTIVE",
        "Approved tier-1 cloud infrastructure vendor. Primary provider for cluster virtualization.",
        1,
        "SOC2-2025-CS-401",
        "2027-01-01",
    ),
    (
        "VEND-DATASYNC",
        "DataSync Corp",
        "MEDIUM",
        "ACTIVE",
        "SOC2 certification expired 30 days ago. Recertification submission pending audit sign-off.",
        0,
        "EXPIRED",
        "2026-08-01",
    ),
    (
        "VEND-DELL",
        "Dell Direct",
        "LOW",
        "ACTIVE",
        "Standard peripheral and office workstation supplier under master services agreement.",
        1,
        "SOC2-2025-DELL-900",
        "2027-05-15",
    ),
]

INITIAL_RULES = [
    ("rule_reject_fraud", "reject_order", "order=PO-9821", "fraud_quarantined", 0),
    ("rule_approve_renewal", "approve_order", "order=PO-3410", "renewal_approved", 0),
    ("rule_blacklist_vendor", "update_vendor", "vendor=VEND-GHOSTWIRE", "vendor_blacklisted", 0),
    ("rule_recertify_soc2", "compliance_filing", "vendor=VEND-DATASYNC", "soc2_renewed", 0),
]


def seed_database(db_path: Path | str) -> sqlite3.Connection:
    conn = init_db(db_path)

    # Clear existing rows
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM vendors")
    conn.execute("DELETE FROM compliance_filings")
    conn.execute("DELETE FROM browser_session")
    conn.execute("DELETE FROM action_log")
    conn.execute("DELETE FROM scenario_rules")
    conn.execute("DELETE FROM event_traces")
    conn.execute("DELETE FROM task_submission")

    # Insert orders
    for oid, vid, item, amt, req_by, status, reason, c_at, u_at in INITIAL_ORDERS:
        conn.execute(
            """
            INSERT INTO orders (id, vendor_id, item, amount, requested_by, status, rejection_reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (oid, vid, item, amt, req_by, status, reason, c_at, u_at),
        )

    # Insert vendors
    for vid, name, risk, status, notes, soc2_cert, cert_id, exp in INITIAL_VENDORS:
        conn.execute(
            """
            INSERT INTO vendors (id, name, risk_level, status, notes, soc2_certified, soc2_cert_id, soc2_expires)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (vid, name, risk, status, notes, soc2_cert, cert_id, exp),
        )

    # Initialize browser session
    conn.execute(
        """
        INSERT INTO browser_session (id, current_url, history_json)
        VALUES (1, 'https://procure.corp/dashboard', '["https://procure.corp/dashboard"]')
        """
    )

    # Insert scenario rules
    for rule_id, trigger, cond, effect, act in INITIAL_RULES:
        conn.execute(
            """
            INSERT INTO scenario_rules (rule_id, trigger, condition, effect, activated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (rule_id, trigger, cond, effect, act),
        )

    conn.commit()
    return conn
