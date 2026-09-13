#!/usr/bin/env python3
"""JSON CLI contract for the Healthcare Clinical Operations RL Environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from healthcare_sim.context import HealthcareContext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Healthcare RL Environment CLI")
    parser.add_argument(
        "command",
        choices=["setup", "reset", "tools", "step", "state", "history"],
        help="RL lifecycle command to execute",
    )
    parser.add_argument("--db", default=None, help="Path to SQLite database")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for environment")
    parser.add_argument("--session-cookie", default="default_sess", help="Session ID")
    parser.add_argument("--tool-name", default="", help="Tool name for step command")
    parser.add_argument("--input-payload", default="{}", help="JSON input arguments for step")
    parser.add_argument("--instruction", default="", help="Instruction for episode")

    args = parser.parse_args(argv)

    ctx = HealthcareContext(
        db_path=args.db or "/tmp/healthcare_sim.db",
        seed=args.seed,
    )

    if args.command == "setup":
        ctx.ensure_initialized()
        print(json.dumps({"ok": True, "status": "initialized", "db": str(ctx.db_path)}))
        return 0

    elif args.command == "reset":
        ctx.seed_db()
        print(json.dumps({
            "ok": True,
            "session_cookie": args.session_cookie,
            "seed": args.seed,
            "instruction": args.instruction,
            "status": "ready",
        }))
        return 0

    elif args.command == "tools":
        tools_list = [
            "verify_patient_identity",
            "get_patient_chart",
            "search_clinical_records",
            "create_clinical_order",
            "update_order_or_referral",
            "schedule_appointment",
            "send_portal_message",
            "submit_prior_authorization",
            "escalate_to_human_clinician",
            "get_audit_log",
            "submit_task",
        ]
        print(json.dumps({"ok": True, "tools": tools_list}))
        return 0

    elif args.command == "step":
        if not args.tool_name:
            print(json.dumps({"ok": False, "error": "Missing --tool-name parameter"}))
            return 1
        try:
            payload = json.loads(args.input_payload)
        except Exception as e:
            print(json.dumps({"ok": False, "error": f"Invalid input-payload JSON: {e}"}))
            return 1

        try:
            name = args.tool_name
            if name == "verify_patient_identity":
                res = ctx.service.verify_patient_identity(
                    payload.get("patient_id", ""),
                    first_name=payload.get("first_name"),
                    last_name=payload.get("last_name"),
                    birth_date=payload.get("birth_date"),
                    mrn=payload.get("mrn"),
                )
            elif name == "get_patient_chart":
                res = ctx.service.get_patient_chart(payload.get("patient_id", ""), section_filter=payload.get("section_filter"))
            elif name == "create_clinical_order":
                res = ctx.service.create_clinical_order(payload.get("order_type", ""), payload.get("patient_id", ""), payload.get("details", {}))
            elif name == "update_order_or_referral":
                res = ctx.service.update_order_or_referral(payload.get("order_id", ""), payload.get("status", ""), notes=payload.get("notes", ""))
            elif name == "schedule_appointment":
                res = ctx.service.schedule_appointment(
                    payload.get("patient_id", ""),
                    payload.get("provider_id", ""),
                    payload.get("facility_id", ""),
                    payload.get("slot_iso", ""),
                    visit_type=payload.get("visit_type", "consultation"),
                    notes=payload.get("notes", ""),
                )
            elif name == "send_portal_message":
                res = ctx.service.send_portal_message(
                    payload.get("recipient_type", "patient"),
                    payload.get("recipient_id", ""),
                    payload.get("patient_id", ""),
                    payload.get("subject", ""),
                    payload.get("body", ""),
                )
            elif name == "escalate_to_human_clinician":
                res = ctx.service.escalate_to_human_clinician(
                    payload.get("patient_id", ""),
                    payload.get("urgency", "urgent"),
                    payload.get("clinical_summary", ""),
                    payload.get("required_action", ""),
                )
            elif name == "get_audit_log":
                res = ctx.service.get_audit_log(patient_id=payload.get("patient_id"), limit=int(payload.get("limit", 50)))
            elif name == "submit_task":
                res = {"submitted": True, "summary": payload.get("summary", ""), "status": "completed"}
            else:
                res = {"error": f"Unknown healthcare tool '{name}'"}

            print(json.dumps({"ok": True, "result": res}))
            return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1

    elif args.command == "state":
        state_hash = ctx.service.calculate_state_hash()
        print(json.dumps({"ok": True, "state_hash": state_hash}))
        return 0

    elif args.command == "history":
        logs = ctx.service.get_audit_log(limit=100)
        print(json.dumps({"ok": True, "history": logs, "total_actions": len(logs)}))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
