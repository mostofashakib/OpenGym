"""Deterministic database seeder for Gmail simulation."""

from __future__ import annotations

import random
import sys
from pathlib import Path

try:
    from .clock import init_clock
    from .sqlite_common import get_connection, initialize_database
except (ImportError, ValueError):
    _pkg_root = Path(__file__).resolve().parent.parent
    if str(_pkg_root) not in sys.path:
        sys.path.insert(0, str(_pkg_root))
    from gmail_sim.clock import init_clock  # type: ignore[no-redef]
    from gmail_sim.sqlite_common import (  # type: ignore[no-redef]
        get_connection,
        initialize_database,
    )

SYSTEM_LABELS = [
    ("INBOX", "INBOX", "SYSTEM", None),
    ("SENT", "SENT", "SYSTEM", None),
    ("DRAFTS", "DRAFTS", "SYSTEM", None),
    ("TRASH", "TRASH", "SYSTEM", None),
    ("SPAM", "SPAM", "SYSTEM", None),
    ("ARCHIVE", "ARCHIVE", "SYSTEM", None),
    ("STARRED", "STARRED", "SYSTEM", None),
    ("IMPORTANT", "IMPORTANT", "SYSTEM", None),
]

USER_LABELS = [
    ("work", "work", "USER", "#1E88E5"),
    ("personal", "personal", "USER", "#43A047"),
    ("receipts", "receipts", "USER", "#FB8C00"),
    ("travel", "travel", "USER", "#8E24AA"),
    ("important", "important", "USER", "#E53935"),
]


def seed_database(db_path: Path | str, snapshot_path: Path | str | None = None, seed: str | int = "gmail") -> None:
    path = Path(db_path)
    initialize_database(path)

    random.seed(str(seed))

    with get_connection(path) as conn:
        # Settings
        conn.execute(
            """
            INSERT OR REPLACE INTO settings (id, display_name, email, signature)
            VALUES (1, 'You', 'you@example.com', 'Best regards,\nYou')
            """
        )

        # Labels
        for lid, name, ltype, color in SYSTEM_LABELS + USER_LABELS:
            conn.execute(
                """
                INSERT OR REPLACE INTO labels (id, name, type, color)
                VALUES (?, ?, ?, ?)
                """,
                (lid, name, ltype, color),
            )

        # Clock
        init_clock(conn)

        # Contacts
        contacts = [
            ("billing@company.com", "Accounting Dept"),
            ("finance@corp.co", "Finance Team"),
            ("shipping@logistics.net", "Global Express Shipping"),
            ("alex.smith@example.com", "Alex Smith"),
            ("jordan.williams@startup.io", "Jordan Williams"),
        ]
        for email, name in contacts:
            conn.execute(
                "INSERT OR REPLACE INTO contacts (email, name) VALUES (?, ?)",
                (email, name),
            )

        # Pre-seed realistic conversation threads and messages
        # 1. Invoice email from billing@company.com
        conn.execute(
            """
            INSERT OR REPLACE INTO threads (id, subject, last_activity_iso, snippet)
            VALUES ('T_INVOICE_01', 'Invoice attached - Q1 Cloud Infrastructure', '2030-03-14T02:30:00-05:00', 'Please review the attached invoice for Q1 cloud computing services.')
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO emails (
                id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
                subject, text, html, date_iso, is_read, is_starred, is_important,
                is_archived, is_trash, snooze_until, label_ids
            )
            VALUES (
                'MSG_INV_001', 'T_INVOICE_01', 'billing@company.com',
                '["you@example.com"]', '[]', '[]',
                'Invoice attached - Q1 Cloud Infrastructure',
                'Hello,\n\nPlease find attached the invoice for Q1 cloud infrastructure services. Kindly review and process payment at your earliest convenience.\n\nThank you,\nAccounting Dept',
                '<p>Hello,</p><p>Please find attached the invoice for Q1 cloud infrastructure services.</p>',
                '2030-03-14T02:30:00-05:00',
                0, 0, 0, 0, 0, NULL, '["INBOX"]'
            )
            """
        )

        # 2. Shipping notice email
        conn.execute(
            """
            INSERT OR REPLACE INTO threads (id, subject, last_activity_iso, snippet)
            VALUES ('T_SHIP_02', 'Shipping notice: Your equipment order #84920 has shipped', '2030-03-14T01:15:00-05:00', 'Your equipment shipment is in transit.')
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO emails (
                id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
                subject, text, html, date_iso, is_read, is_starred, is_important,
                is_archived, is_trash, snooze_until, label_ids
            )
            VALUES (
                'MSG_SHIP_002', 'T_SHIP_02', 'shipping@logistics.net',
                '["you@example.com"]', '[]', '[]',
                'Shipping notice: Your equipment order #84920 has shipped',
                'Your equipment shipment #84920 is on its way and scheduled for delivery on Monday.\n\nTracking: TRK-99281-US',
                '<p>Your shipment is on its way.</p>',
                '2030-03-14T01:15:00-05:00',
                1, 0, 0, 0, 0, NULL, '["INBOX"]'
            )
            """
        )

        # 3. Team project discussion
        conn.execute(
            """
            INSERT OR REPLACE INTO threads (id, subject, last_activity_iso, snippet)
            VALUES ('T_PROJ_03', 'Project Roadmap Alignment', '2030-03-13T18:45:00-05:00', 'Looking forward to reviewing the roadmap draft.')
            """
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO emails (
                id, thread_id, from_address, to_addresses, cc_addresses, bcc_addresses,
                subject, text, html, date_iso, is_read, is_starred, is_important,
                is_archived, is_trash, snooze_until, label_ids
            )
            VALUES (
                'MSG_PROJ_003', 'T_PROJ_03', 'alex.smith@example.com',
                '["you@example.com"]', '[]', '[]',
                'Project Roadmap Alignment',
                'Hi,\n\nWanted to check in on our roadmap sync for next quarter. Let me know when you are free.\n\nAlex',
                '<p>Wanted to check in on our roadmap sync.</p>',
                '2030-03-13T18:45:00-05:00',
                1, 0, 0, 0, 0, NULL, '["INBOX", "work"]'
            )
            """
        )

        if snapshot_path:
            snap = Path(snapshot_path)
            snap.parent.mkdir(parents=True, exist_ok=True)
            with open(snap, "w", encoding="utf-8") as f:
                f.writelines(f"{line}\n" for line in conn.iterdump())


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Seed Gmail database")
    parser.add_argument("--db", default="/var/lib/gmail/gmail.db", help="Path to sqlite db")
    parser.add_argument("--snapshot", default="/var/lib/gmail/gmail_seed_snapshot.sql", help="Path to snapshot sql")
    parser.add_argument("--seed", default="gmail", help="Random seed")
    args = parser.parse_args()
    seed_database(args.db, snapshot_path=args.snapshot, seed=args.seed)


if __name__ == "__main__":
    main()
