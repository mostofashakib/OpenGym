"""Universal clinical and operational service layer with RBAC and access auditing."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

from .audit_logger import get_audit_trail, log_audit_event
from .db_generator import calculate_database_hash
from .invariants import SafetyInvariantEngine


class HealthcareService:
    """Service layer managing clinical workflows, patient charts, and audit trails."""

    def __init__(self, db_path: Any) -> None:
        if hasattr(db_path, "db_path"):
            self.db_path = Path(db_path.db_path)
        else:
            self.db_path = Path(db_path)


    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def list_patients(self, query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List or search patient directory."""
        with self._connect() as conn:
            if query:
                like = f"%{query}%"
                rows = conn.execute(
                    "SELECT id, mrn, first_name, last_name, birth_date, gender FROM patients WHERE first_name LIKE ? OR last_name LIKE ? OR mrn LIKE ? LIMIT ?",
                    (like, like, like, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, mrn, first_name, last_name, birth_date, gender FROM patients LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    def verify_patient_identity(
        self,
        patient_id: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        birth_date: Optional[str] = None,
        mrn: Optional[str] = None,
        actor_id: str = "prac-001",
        actor_role: str = "physician",
    ) -> Dict[str, Any]:
        """Verify that patient identity matches records prior to executing clinical actions."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not row:
                log_audit_event(
                    conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                    "Patient", "verify_identity", authorized=False, details={"matched": False, "reason": "not_found"}
                )
                conn.commit()
                return {"verified": False, "error": f"Patient with ID {patient_id} not found."}

            pat = dict(row)
            mismatches = []
            if first_name and pat["first_name"].lower() != first_name.strip().lower():
                mismatches.append(f"first_name mismatch: expected '{pat['first_name']}', got '{first_name}'")
            if last_name and pat["last_name"].lower() != last_name.strip().lower():
                mismatches.append(f"last_name mismatch: expected '{pat['last_name']}', got '{last_name}'")
            if birth_date and pat["birth_date"] != birth_date.strip():
                mismatches.append(f"birth_date mismatch: expected '{pat['birth_date']}', got '{birth_date}'")
            if mrn and pat["mrn"].upper() != mrn.strip().upper():
                mismatches.append(f"MRN mismatch: expected '{pat['mrn']}', got '{mrn}'")

            verified = len(mismatches) == 0
            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "Patient", "verify_identity", authorized=verified,
                details={"verified": verified, "mismatches": mismatches}
            )
            conn.commit()
            return {
                "verified": verified,
                "patient_id": patient_id,
                "mrn": pat["mrn"],
                "full_name": f"{pat['first_name']} {pat['last_name']}",
                "birth_date": pat["birth_date"],
                "mismatches": mismatches,
            }

    def get_patient_chart(
        self,
        patient_id: str,
        section_filter: Optional[str] = None,
        actor_id: str = "prac-001",
        actor_role: str = "physician",
    ) -> Dict[str, Any]:
        """Fetch patient chart sections with access logging."""
        with self._connect() as conn:
            pat_row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not pat_row:
                return {"error": f"Patient {patient_id} not found."}

            chart: Dict[str, Any] = {"patient": dict(pat_row)}

            if not section_filter or section_filter == "conditions":
                conds = conn.execute("SELECT * FROM conditions WHERE patient_id = ?", (patient_id,)).fetchall()
                chart["conditions"] = [dict(r) for r in conds]

            if not section_filter or section_filter == "medications":
                meds = conn.execute("SELECT * FROM medication_requests WHERE patient_id = ?", (patient_id,)).fetchall()
                chart["medications"] = [dict(r) for r in meds]

            if not section_filter or section_filter == "allergies":
                allergies = conn.execute("SELECT * FROM allergy_intolerances WHERE patient_id = ?", (patient_id,)).fetchall()
                chart["allergies"] = [dict(r) for r in allergies]

            if not section_filter or section_filter == "observations":
                obs = conn.execute("SELECT * FROM observations WHERE patient_id = ? ORDER BY effective_iso DESC", (patient_id,)).fetchall()
                chart["observations"] = [dict(r) for r in obs]

            if not section_filter or section_filter == "encounters":
                encs = conn.execute("SELECT * FROM encounters WHERE patient_id = ? ORDER BY start_iso DESC", (patient_id,)).fetchall()
                chart["encounters"] = [dict(r) for r in encs]

            if not section_filter or section_filter == "referrals":
                srs = conn.execute("SELECT * FROM service_requests WHERE patient_id = ? ORDER BY created_iso DESC", (patient_id,)).fetchall()
                chart["service_requests"] = [dict(r) for r in srs]

            if not section_filter or section_filter == "appointments":
                apts = conn.execute("SELECT * FROM appointments WHERE patient_id = ? ORDER BY start_iso DESC", (patient_id,)).fetchall()
                chart["appointments"] = [dict(r) for r in apts]

            if not section_filter or section_filter == "documents":
                docs = conn.execute("SELECT * FROM document_references WHERE patient_id = ? ORDER BY created_iso DESC", (patient_id,)).fetchall()
                chart["documents"] = [dict(r) for r in docs]

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "PatientChart", "read", details={"section_filter": section_filter}
            )
            conn.commit()
            return chart

    def search_clinical_records(
        self,
        resource_type: str,
        patient_id: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        actor_id: str = "prac-001",
        actor_role: str = "physician",
    ) -> List[Dict[str, Any]]:
        """Search records across clinical tables with parameter filtering."""
        table_map = {
            "patients": "patients",
            "conditions": "conditions",
            "medications": "medication_requests",
            "allergies": "allergy_intolerances",
            "observations": "observations",
            "procedures": "procedures",
            "referrals": "service_requests",
            "appointments": "appointments",
            "communications": "communications",
            "documents": "document_references",
        }
        tbl = table_map.get(resource_type.lower())
        if not tbl:
            return []

        with self._connect() as conn:
            query = f"SELECT * FROM {tbl}"
            conditions = []
            params: List[Any] = []

            if patient_id:
                conditions.append("patient_id = ?")
                params.append(patient_id)

            if query_params:
                for k, v in query_params.items():
                    conditions.append(f"{k} = ?")
                    params.append(v)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " LIMIT 100"
            rows = conn.execute(query, tuple(params)).fetchall()

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role,
                patient_id or "all", resource_type, "search",
                details={"query_params": query_params, "result_count": len(rows)}
            )
            conn.commit()
            return [dict(r) for r in rows]

    def create_clinical_order(
        self,
        order_type: str,  # "medication" or "diagnostic" or "referral"
        patient_id: str,
        details: Dict[str, Any],
        actor_id: str = "prac-001",
        actor_role: str = "physician",
    ) -> Dict[str, Any]:
        """Create a clinical prescription, lab order, or specialty referral."""
        with self._connect() as conn:
            if order_type == "medication":
                med_name = details.get("medication_name", "")
                dose_amount = float(details.get("dose_amount", 0.0))

                # Check allergy contraindications
                allergies = conn.execute("SELECT * FROM allergy_intolerances WHERE patient_id = ?", (patient_id,)).fetchall()
                allergy_viol = SafetyInvariantEngine.check_allergy_contraindication(
                    med_name, [dict(a) for a in allergies], patient_id
                )
                if allergy_viol:
                    return {"success": False, "error": allergy_viol.description, "violation": allergy_viol.__dict__}

                # Check drug-drug interactions
                active_meds = conn.execute(
                    "SELECT * FROM medication_requests WHERE patient_id = ? AND status = 'active'", (patient_id,)
                ).fetchall()
                ddi_viol = SafetyInvariantEngine.check_drug_drug_interaction(
                    med_name, [dict(m) for m in active_meds], patient_id
                )
                if ddi_viol:
                    return {"success": False, "error": ddi_viol.description, "violation": ddi_viol.__dict__}

                # Check renal contraindication
                egfr_row = conn.execute(
                    "SELECT value_numeric FROM observations WHERE patient_id = ? AND code_loinc = '33914-3' ORDER BY effective_iso DESC LIMIT 1",
                    (patient_id,),
                ).fetchone()
                egfr_val = egfr_row[0] if egfr_row and egfr_row[0] is not None else None
                renal_viol = SafetyInvariantEngine.check_renal_contraindication(med_name, egfr_val, patient_id)
                if renal_viol:
                    return {"success": False, "error": renal_viol.description, "violation": renal_viol.__dict__}

                # Check dose ceiling
                dose_viol = SafetyInvariantEngine.check_dose_ceiling(med_name, dose_amount, patient_id)
                if dose_viol:
                    return {"success": False, "error": dose_viol.description, "violation": dose_viol.__dict__}

                order_id = f"med-req-{patient_id}-{len(active_meds) + 1:02d}"
                conn.execute(
                    """INSERT INTO medication_requests (
                        id, patient_id, medication_name, dosage_instruction, status, route, frequency,
                        dose_amount, dose_unit, prescriber_id, authored_on_iso, refills
                    ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, '2026-10-15T08:00:00Z', ?)""",
                    (
                        order_id,
                        patient_id,
                        med_name,
                        details.get("dosage_instruction", f"{dose_amount} mg daily"),
                        details.get("route", "oral"),
                        details.get("frequency", "daily"),
                        dose_amount,
                        details.get("dose_unit", "mg"),
                        actor_id,
                        details.get("refills", 0),
                    ),
                )
                log_audit_event(
                    conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                    "MedicationRequest", "create", resource_id=order_id, details=details
                )
                conn.commit()
                return {"success": True, "order_id": order_id, "type": "medication", "medication_name": med_name}

            elif order_type in ("diagnostic", "referral"):
                order_id = f"sr-{patient_id}-{details.get('service_code', 'order')}"
                conn.execute(
                    """INSERT INTO service_requests (
                        id, patient_id, service_code, display, intent, priority, status,
                        requester_id, recipient_id, created_iso, reason_text
                    ) VALUES (?, ?, ?, ?, 'order', ?, 'active', ?, ?, '2026-10-15T08:00:00Z', ?)""",
                    (
                        order_id,
                        patient_id,
                        details.get("service_code", "GEN-ORDER"),
                        details.get("display", "Clinical Diagnostic Order"),
                        details.get("priority", "routine"),
                        actor_id,
                        details.get("recipient_id", ""),
                        details.get("reason_text", ""),
                    ),
                )
                log_audit_event(
                    conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                    "ServiceRequest", "create", resource_id=order_id, details=details
                )
                conn.commit()
                return {"success": True, "order_id": order_id, "type": order_type, "display": details.get("display")}

            return {"success": False, "error": f"Unknown order_type: {order_type}"}

    def update_order_or_referral(
        self,
        order_id: str,
        status: str,
        notes: str = "",
        actor_id: str = "prac-001",
        actor_role: str = "physician",
    ) -> Dict[str, Any]:
        """Update the status of a service request or referral order."""
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE service_requests SET status = ?, reason_text = reason_text || ' ' || ? WHERE id = ?",
                (status, notes, order_id),
            )
            if cur.rowcount == 0:
                return {"success": False, "error": f"Order {order_id} not found."}

            row = conn.execute("SELECT patient_id FROM service_requests WHERE id = ?", (order_id,)).fetchone()
            patient_id = row[0] if row else "unknown"

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "ServiceRequest", "update", resource_id=order_id, details={"status": status, "notes": notes}
            )
            conn.commit()
            return {"success": True, "order_id": order_id, "new_status": status}

    def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        facility_id: str,
        slot_iso: str,
        visit_type: str = "consultation",
        notes: str = "",
        actor_id: str = "prac-001",
        actor_role: str = "scheduler",
    ) -> Dict[str, Any]:
        """Schedule an in-clinic appointment ensuring no conflicting double-bookings."""
        with self._connect() as conn:
            # Check provider conflict
            conflict = conn.execute(
                "SELECT * FROM appointments WHERE provider_id = ? AND start_iso = ? AND status = 'booked'",
                (provider_id, slot_iso),
            ).fetchone()
            if conflict:
                return {
                    "success": False,
                    "error": f"Provider {provider_id} is already booked at {slot_iso}."
                }

            apt_id = f"apt-{patient_id}-{len(conn.execute('SELECT id FROM appointments').fetchall()) + 1:04d}"
            conn.execute(
                """INSERT INTO appointments (
                    id, patient_id, provider_id, facility_id, service_type, status, start_iso, end_iso, notes
                ) VALUES (?, ?, ?, ?, ?, 'booked', ?, ?, ?)""",
                (apt_id, patient_id, provider_id, facility_id, visit_type, slot_iso, slot_iso, notes),
            )

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "Appointment", "schedule", resource_id=apt_id,
                details={"slot_iso": slot_iso, "provider_id": provider_id, "facility_id": facility_id}
            )
            conn.commit()
            return {
                "success": True,
                "appointment_id": apt_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "slot_iso": slot_iso,
            }

    def send_portal_message(
        self,
        recipient_type: str,
        recipient_id: str,
        patient_id: str,
        subject: str,
        body: str,
        actor_id: str = "prac-001",
        actor_role: str = "nurse",
    ) -> Dict[str, Any]:
        """Send message via secure patient portal or staff communication."""
        with self._connect() as conn:
            msg_id = f"comm-{patient_id}-{len(conn.execute('SELECT id FROM communications').fetchall()) + 1:04d}"
            conn.execute(
                """INSERT INTO communications (
                    id, sender_type, sender_id, recipient_type, recipient_id, patient_id, subject, body, sent_iso, status
                ) VALUES (?, 'staff', ?, ?, ?, ?, ?, ?, '2026-10-15T08:00:00Z', 'completed')""",
                (msg_id, actor_id, recipient_type, recipient_id, patient_id, subject, body),
            )

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "Communication", "disclose" if recipient_type == "patient" else "create",
                resource_id=msg_id,
                details={"subject": subject, "recipient_id": recipient_id}
            )
            conn.commit()
            return {"success": True, "communication_id": msg_id, "patient_id": patient_id}

    def submit_prior_authorization(
        self,
        patient_id: str,
        service_code: str,
        payer_id: str,
        clinical_rationale: str,
        actor_id: str = "prac-001",
        actor_role: str = "billing_specialist",
    ) -> Dict[str, Any]:
        """Submit a clinical prior authorization request to insurance payer."""
        with self._connect() as conn:
            auth_id = f"pa-{patient_id}-{service_code}"
            conn.execute(
                """INSERT OR REPLACE INTO prior_authorizations (
                    id, patient_id, service_code, payer_id, status, expiration_iso, clinical_rationale
                ) VALUES (?, ?, ?, ?, 'approved', '2027-01-01T00:00:00Z', ?)""",
                (auth_id, patient_id, service_code, payer_id, clinical_rationale),
            )

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "PriorAuthorization", "create", resource_id=auth_id,
                details={"service_code": service_code, "payer_id": payer_id}
            )
            conn.commit()
            return {"success": True, "auth_id": auth_id, "status": "approved"}

    def escalate_to_human_clinician(
        self,
        patient_id: str,
        urgency: str,  # "routine", "urgent", "emergency"
        clinical_summary: str,
        required_action: str,
        actor_id: str = "prac-001",
        actor_role: str = "nurse",
    ) -> Dict[str, Any]:
        """Legitimately hand off a case to an authorized physician when safety thresholds are crossed."""
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO human_escalations (
                    timestamp_iso, patient_id, urgency, clinical_summary, required_action, escalated_by, status
                ) VALUES ('2026-10-15T08:00:00Z', ?, ?, ?, ?, ?, 'open')""",
                (patient_id, urgency, clinical_summary, required_action, actor_id),
            )
            esc_id = int(cur.lastrowid or 0)

            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role, patient_id,
                "HumanEscalation", "escalate", resource_id=str(esc_id),
                details={"urgency": urgency, "required_action": required_action}
            )
            conn.commit()
            return {
                "success": True,
                "escalation_id": esc_id,
                "patient_id": patient_id,
                "urgency": urgency,
                "status": "open",
                "message": "Case successfully placed in safe holding state and escalated to attending physician.",
            }

    def get_audit_log(
        self,
        patient_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch audit trail records."""
        with self._connect() as conn:
            return get_audit_trail(conn, patient_id=patient_id, actor_id=actor_id, limit=limit)

    def calculate_state_hash(self) -> str:
        """Compute SHA-256 database state hash."""
        return calculate_database_hash(self.db_path)

    def step_simulation(self, minutes: int = 15) -> Dict[str, Any]:
        """Advance clinical virtual clock."""
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM system_state WHERE key = 'virtual_time_iso'").fetchone()
            current_time = row[0] if row else "2026-10-15T08:00:00Z"
            from datetime import datetime, timedelta
            dt = datetime.fromisoformat(current_time.replace("Z", "+00:00"))
            new_dt = dt + timedelta(minutes=minutes)
            new_time = new_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            conn.execute("UPDATE system_state SET value = ? WHERE key = 'virtual_time_iso'", (new_time,))
            conn.commit()
            return {"stepped_minutes": minutes, "current_virtual_time": new_time}

    def submit_task(self, summary: str, affected_ids: str = "", actor_id: str = "prac-001", actor_role: str = "physician") -> Dict[str, Any]:
        """Record formal clinical task handover in the audit trail."""
        parsed_ids = [i.strip() for i in affected_ids.split(",") if i.strip()] if affected_ids else []
        with self._connect() as conn:
            log_audit_event(
                conn, "2026-10-15T08:00:00Z", actor_id, actor_role,
                parsed_ids[0] if parsed_ids else "system",
                "Task", "submit_task", authorized=True,
                details={"summary": summary, "affected_ids": parsed_ids}
            )
            conn.commit()
        return {"submitted": True, "summary": summary, "affected_ids": parsed_ids, "status": "completed"}
