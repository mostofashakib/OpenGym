"""Virtual-time event scheduler driving dynamic asynchronous enterprise events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import random
import sqlite3
from typing import Any, Dict, List, Optional


@dataclass
class ScheduledEvent:
    event_id: str
    timestamp_iso: str
    event_type: str
    payload: Dict[str, Any]
    executed: bool = False


class EventScheduler:
    """Controls virtual time progression and triggers time-dependent enterprise events."""

    def __init__(self, conn: sqlite3.Connection, seed: int = 42) -> None:
        self.conn = conn
        self.rng = random.Random(seed)

    def get_virtual_time(self) -> str:
        """Retrieve current simulated organization time."""
        row = self.conn.execute(
            "SELECT value FROM system_state WHERE key = 'virtual_time_iso'"
        ).fetchone()
        return row[0] if row else "2026-10-15T09:00:00Z"

    def advance_virtual_time(self, minutes: int = 30) -> str:
        """Advance the enterprise clock by specified minutes."""
        current_time_str = self.get_virtual_time()
        # Parse ISO string
        dt = datetime.fromisoformat(current_time_str.replace("Z", "+00:00"))
        new_dt = dt + timedelta(minutes=minutes)
        new_time_str = new_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        self.conn.execute(
            "UPDATE system_state SET value = ? WHERE key = 'virtual_time_iso'",
            (new_time_str,),
        )
        self.conn.commit()
        return new_time_str

    def trigger_incoming_email(
        self,
        sender_email: str,
        recipient_emails: List[str],
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        """Inject an asynchronous incoming email into the recipient's inbox."""
        time_iso = self.get_virtual_time()
        email_id = f"email-async-{self.rng.randint(1000, 9999)}"
        thread_id = f"th-{email_id}"

        self.conn.execute(
            """INSERT INTO email_messages (
                id, sender_email, recipient_emails_json, cc_emails_json, subject, body, sent_iso, thread_id, is_read, folder
            ) VALUES (?, ?, ?, '[]', ?, ?, ?, ?, 0, 'inbox')""",
            (email_id, sender_email, json.dumps(recipient_emails), subject, body, time_iso, thread_id),
        )
        self.conn.commit()

        return {
            "event": "incoming_email",
            "email_id": email_id,
            "sender": sender_email,
            "subject": subject,
            "timestamp": time_iso,
        }

    def trigger_payment_failure_alert(
        self,
        customer_id: str,
        invoice_id: str,
        amount_usd: float,
    ) -> Dict[str, Any]:
        """Trigger an automated payment webhook failure event."""
        time_iso = self.get_virtual_time()
        pay_id = f"pay-fail-{self.rng.randint(1000, 9999)}"

        self.conn.execute(
            """INSERT INTO payments (id, invoice_id, customer_id, amount_usd, payment_method, transaction_ref, status, paid_iso)
               VALUES (?, ?, ?, ?, 'credit_card', ?, 'failed', ?)""",
            (pay_id, invoice_id, customer_id, amount_usd, f"TXN-ERR-{pay_id}", time_iso),
        )
        self.conn.commit()

        return {
            "event": "payment_failure",
            "payment_id": pay_id,
            "invoice_id": invoice_id,
            "customer_id": customer_id,
            "amount_usd": amount_usd,
        }
