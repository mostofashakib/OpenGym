#!/usr/bin/env python3
"""CLI bridge connecting healthcare-ui Next.js web application to HealthcareService."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

LOCAL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = LOCAL_DIR.parent
sys.path.insert(0, str(LOCAL_DIR))
sys.path.insert(0, str(LOCAL_DIR / "environment"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "healthcare"))

try:
    from healthcare_sim.context import HealthcareContext
    from healthcare_sim.service import HealthcareService
except ImportError:
    from healthcare.environment.healthcare_sim.context import HealthcareContext
    from healthcare.environment.healthcare_sim.service import HealthcareService


def get_service() -> HealthcareService:
    db_env = os.environ.get("HEALTHCARE_DB")
    if db_env:
        db_path = Path(db_env)
    elif (REPO_ROOT / "healthcare.db").exists():
        db_path = REPO_ROOT / "healthcare.db"
    else:
        db_path = Path("/tmp/healthcare_sim.db")

    actor_id = os.environ.get("HEALTHCARE_ACTOR_ID", "prac-001")
    actor_role = os.environ.get("HEALTHCARE_ACTOR_ROLE", "physician")

    ctx = HealthcareContext(db_path=db_path, actor_id=actor_id, actor_role=actor_role)
    ctx.ensure_initialized()
    return ctx.service


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument"}))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    service = get_service()

    try:
        if cmd == "list_patients":
            q = args[0] if args else None
            res = service.list_patients(query=q)
            print(json.dumps({"ok": True, "patients": res}))

        elif cmd == "verify_patient":
            identifier = args[0]
            dob = args[1] if len(args) > 1 and args[1] != "" else None
            res = service.verify_patient_identity(patient_id=identifier, birth_date=dob)
            print(json.dumps({"ok": True, "verified": res}))

        elif cmd == "get_patient_chart":
            pid = args[0]
            res = service.get_patient_chart(patient_id=pid)
            print(json.dumps({"ok": True, "chart": res}))

        elif cmd == "search_clinical_records":
            res_type = args[0] if args else "conditions"
            pid = args[1] if len(args) > 1 and args[1] != "" else None
            res = service.search_clinical_records(resource_type=res_type, patient_id=pid)
            print(json.dumps({"ok": True, "records": res}))

        elif cmd == "create_clinical_order":
            pid = args[0]
            order_type = args[1]  # "medication", "diagnostic", "referral"
            code = args[2]
            display = args[3]
            details = {
                "code": code,
                "display": display,
                "medication_name": display,
                "dose_amount": float(args[4]) if len(args) > 4 and args[4] != "" else 100.0,
                "dosage": args[4] if len(args) > 4 else "",
                "instructions": args[5] if len(args) > 5 else "",
                "is_stat": args[6].lower() == "true" if len(args) > 6 else False,
            }
            res = service.create_clinical_order(
                order_type=order_type,
                patient_id=pid,
                details=details,
            )
            print(json.dumps({"ok": True, "order": res}))

        elif cmd == "update_order":
            order_id = args[0]
            status = args[1]
            notes = args[2] if len(args) > 2 and args[2] is not None else ""
            res = service.update_order_or_referral(order_id=order_id, status=status, notes=notes)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "schedule_appointment":
            pid = args[0]
            prov_id = args[1]
            fac_id = args[2] if len(args) > 2 and args[2] != "" else "fac-main"
            slot_iso = args[3] if len(args) > 3 and args[3] != "" else "2026-10-16T10:00:00Z"
            reason = args[4] if len(args) > 4 else ""
            res = service.schedule_appointment(
                patient_id=pid, provider_id=prov_id, facility_id=fac_id, slot_iso=slot_iso, notes=reason
            )
            print(json.dumps({"ok": True, "appointment": res}))

        elif cmd == "send_portal_message":
            pid = args[0]
            subject = args[1]
            body = args[2]
            res = service.send_portal_message(
                recipient_type="patient",
                recipient_id=pid,
                patient_id=pid,
                subject=subject,
                body=body,
            )
            print(json.dumps({"ok": True, "message": res}))

        elif cmd == "escalate_emergency":
            pid = args[0]
            urgency = args[1] if len(args) > 1 else "emergency"
            summary = args[2] if len(args) > 2 else "Emergency triage threshold exceeded"
            action = args[3] if len(args) > 3 else "Immediate physician review"
            res = service.escalate_to_human_clinician(
                patient_id=pid, urgency=urgency, clinical_summary=summary, required_action=action
            )
            print(json.dumps({"ok": True, "escalation": res}))

        elif cmd == "submit_prior_auth":
            pid = args[0]
            code = args[1]
            payer = args[2] if len(args) > 2 else "payer-bluecross"
            rationale = args[3] if len(args) > 3 else "Clinical medical necessity"
            res = service.submit_prior_authorization(
                patient_id=pid, service_code=code, payer_id=payer, clinical_rationale=rationale
            )
            print(json.dumps({"ok": True, "prior_auth": res}))

        elif cmd == "get_audit_events":
            pid = args[0] if args and args[0] != "" else None
            res = service.get_audit_log(patient_id=pid)
            print(json.dumps({"ok": True, "audit_events": res}))

        elif cmd == "step_simulation":
            mins = int(args[0]) if args else 15
            res = service.step_simulation(minutes=mins)
            print(json.dumps({"ok": True, "simulation": res}))

        elif cmd == "submit_task":
            summary = args[0] if args else "Clinical coordination task completed"
            affected = args[1] if len(args) > 1 else ""
            res = service.submit_task(summary=summary, affected_ids=affected)
            print(json.dumps({"ok": True, "submission": res}))

        elif cmd == "get_state_hash":
            h = service.calculate_state_hash()
            print(json.dumps({"ok": True, "state_hash": h}))

        else:
            print(json.dumps({"error": f"Unknown command '{cmd}'"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
