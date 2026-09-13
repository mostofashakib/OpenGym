#!/usr/bin/env python3
"""JSON CLI contract for the Enterprise Digital Twin RL Environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from enterprise_sim.context import EnterpriseContext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enterprise RL Environment CLI")
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

    ctx = EnterpriseContext(
        db_path=args.db or "/tmp/enterprise_sim.db",
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
            "search_organization_directory",
            "get_customer_profile",
            "crm_query_records",
            "crm_update_deal",
            "support_get_ticket",
            "support_add_comment",
            "support_update_ticket_status",
            "billing_get_invoices",
            "billing_process_refund",
            "email_read_inbox",
            "email_send_message",
            "workflow_request_approval",
            "workflow_get_approval_status",
            "document_read",
            "get_audit_trail",
            "step_simulation",
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
            svc = ctx.service
            if name == "search_organization_directory":
                res = svc.search_organization(query=payload.get("query"), department_code=payload.get("department_code"))
            elif name == "get_customer_profile":
                res = svc.get_customer_profile(customer_id=payload.get("customer_id", ""))
            elif name == "support_get_ticket":
                res = svc.support_get_ticket(ticket_id=payload.get("ticket_id", ""))
            elif name == "support_add_comment":
                res = svc.support_add_comment(
                    ticket_id=payload.get("ticket_id", ""),
                    content=payload.get("content", ""),
                    is_internal=payload.get("is_internal", False),
                )
            elif name == "billing_get_invoices":
                res = svc.billing_get_invoices(customer_id=payload.get("customer_id", ""))
            elif name == "billing_process_refund":
                res = svc.billing_process_refund(
                    invoice_id=payload.get("invoice_id", ""),
                    customer_id=payload.get("customer_id", ""),
                    amount_usd=float(payload.get("amount_usd", 0.0)),
                    reason=payload.get("reason", ""),
                    approved_by_id=payload.get("approved_by_id"),
                )
            elif name == "workflow_request_approval":
                res = svc.workflow_request_approval(
                    request_type=payload.get("request_type", ""),
                    approver_id=payload.get("approver_id", ""),
                    amount_usd=float(payload.get("amount_usd", 0.0)),
                    reason=payload.get("reason", ""),
                )
            elif name == "step_simulation":
                res = svc.step_simulation(minutes=int(payload.get("minutes", 15)))
            elif name == "submit_task":
                res = svc.submit_task(summary=payload.get("summary", ""), affected_ids=payload.get("affected_ids", ""))
            else:
                res = {"error": f"Unknown enterprise tool '{name}'"}

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
        logs = ctx.service.get_audit_log()
        print(json.dumps({"ok": True, "history": logs, "total_actions": len(logs)}))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
