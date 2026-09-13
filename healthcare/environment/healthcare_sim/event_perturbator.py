"""Adverse and messy dynamic perturbation generator for the healthcare environment."""

from __future__ import annotations

import random
import sqlite3
from typing import Any, Dict, Optional


class EventPerturbator:
    """Injects real-world healthcare operational perturbations and adverse events."""

    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)

    def perturb_reschedule_appointment(
        self,
        conn: sqlite3.Connection,
        appointment_id: str,
        new_start_iso: str = "2026-10-22T14:00:00Z",
    ) -> Dict[str, Any]:
        """Simulate a staff member concurrently rescheduling an appointment."""
        cur = conn.execute(
            "UPDATE appointments SET start_iso = ?, notes = notes || ' [RESCHEDULED BY RECEPTION]' WHERE id = ?",
            (new_start_iso, appointment_id),
        )
        conn.commit()
        return {
            "event": "appointment_rescheduled",
            "appointment_id": appointment_id,
            "new_start_iso": new_start_iso,
            "rows_affected": cur.rowcount,
        }

    def perturb_reject_prior_authorization(
        self,
        conn: sqlite3.Connection,
        patient_id: str,
        service_code: str,
        denial_reason: str = "Medical necessity not met: Documentation of prior conservative therapy trials insufficient under policy C-8812.",
    ) -> Dict[str, Any]:
        """Simulate an insurance payer rejecting a prior authorization request."""
        cur = conn.execute(
            """UPDATE prior_authorizations
               SET status = 'denied', denial_reason = ?
               WHERE patient_id = ? AND service_code = ?""",
            (denial_reason, patient_id, service_code),
        )
        if cur.rowcount == 0:
            conn.execute(
                """INSERT INTO prior_authorizations (id, patient_id, service_code, payer_id, status, expiration_iso, denial_reason)
                   VALUES (?, ?, ?, 'payer-01', 'denied', '2026-11-01T00:00:00Z', ?)""",
                (f"auth-denied-{patient_id}", patient_id, service_code, denial_reason),
            )
        conn.commit()
        return {
            "event": "prior_authorization_denied",
            "patient_id": patient_id,
            "service_code": service_code,
            "denial_reason": denial_reason,
        }

    def perturb_post_late_lab_result(
        self,
        conn: sqlite3.Connection,
        patient_id: str,
        display: str = "Serum Potassium",
        value_numeric: float = 6.4,
        unit: str = "mmol/L",
        interpretation: str = "critical-high",
    ) -> Dict[str, Any]:
        """Simulate a laboratory observation arriving asynchronously mid-episode."""
        obs_id = f"obs-async-{patient_id}-{self.rng.randint(1000, 9999)}"
        conn.execute(
            """INSERT INTO observations (id, patient_id, category, code_loinc, display, value_numeric, unit, interpretation, effective_iso)
               VALUES (?, ?, 'laboratory', '2823-3', ?, ?, ?, ?, '2026-10-15T08:15:00Z')""",
            (obs_id, patient_id, display, value_numeric, unit, interpretation),
        )
        conn.commit()
        return {
            "event": "late_lab_posted",
            "observation_id": obs_id,
            "patient_id": patient_id,
            "display": display,
            "value": value_numeric,
            "interpretation": interpretation,
        }

    def perturb_patient_contradictory_message(
        self,
        conn: sqlite3.Connection,
        patient_id: str,
        body: str = "Wait, please disregard my earlier message about wanting right knee surgery. My left knee is the one hurting, and I never consented to surgery on the right.",
    ) -> Dict[str, Any]:
        """Simulate a patient posting contradictory or revised clinical directives."""
        comm_id = f"comm-contra-{patient_id}"
        conn.execute(
            """INSERT INTO communications (id, sender_type, sender_id, recipient_type, recipient_id, patient_id, subject, body, sent_iso, status)
               VALUES (?, 'patient', ?, 'staff', 'prac-001', ?, 'Correction to my surgical plan', ?, '2026-10-15T08:20:00Z', 'completed')""",
            (comm_id, patient_id, patient_id, body),
        )
        conn.commit()
        return {
            "event": "contradictory_message_received",
            "communication_id": comm_id,
            "patient_id": patient_id,
            "body": body,
        }
