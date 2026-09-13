#!/usr/bin/env python3
"""JSON-over-CLI bridge connecting Next.js API route handlers to EnterpriseService."""

from __future__ import annotations

import json
from pathlib import Path
import sys

LOCAL_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = LOCAL_DIR.parent
sys.path.insert(0, str(LOCAL_DIR))
sys.path.insert(0, str(LOCAL_DIR / "environment"))
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "enterprise"))

try:
    from enterprise_sim.context import EnterpriseContext
    from enterprise_sim.service import EnterpriseService
except ImportError:
    from enterprise.environment.enterprise_sim.context import EnterpriseContext
    from enterprise.environment.enterprise_sim.service import EnterpriseService

_CONTEXT: EnterpriseContext | None = None


def get_service(actor_id: str = "emp-003", actor_role_id: str = "role-mgr-supp") -> EnterpriseService:
    global _CONTEXT
    if _CONTEXT is None:
        db_path = Path("/tmp/enterprise_sim_ui.db")
        _CONTEXT = EnterpriseContext(db_path=db_path, actor_id=actor_id, actor_role_id=actor_role_id, seed=42)
        _CONTEXT.ensure_initialized()
    return _CONTEXT.service


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument"}))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    service = get_service()

    try:
        if cmd == "list_org":
            query = args[0] if len(args) > 0 and args[0] != "" else None
            dept = args[1] if len(args) > 1 and args[1] != "" else None
            res = service.search_organization(query=query, department_code=dept)
            print(json.dumps({"ok": True, "employees": res}))

        elif cmd == "get_employee":
            emp_id = args[0]
            res = service.get_employee(employee_id=emp_id)
            print(json.dumps({"ok": True, "employee": res}))

        elif cmd == "list_customers":
            query = args[0] if len(args) > 0 and args[0] != "" else None
            res = service.list_customers(query=query)
            print(json.dumps({"ok": True, "customers": res}))

        elif cmd == "get_customer_profile":
            cust_id = args[0]
            res = service.get_customer_profile(customer_id=cust_id)
            print(json.dumps({"ok": True, "profile": res}))

        elif cmd == "list_tickets":
            status = args[0] if len(args) > 0 and args[0] != "" else None
            res = service.list_support_tickets(status=status)
            print(json.dumps({"ok": True, "tickets": res}))

        elif cmd == "get_ticket":
            tkt_id = args[0]
            res = service.support_get_ticket(ticket_id=tkt_id)
            print(json.dumps({"ok": True, "ticket": res}))

        elif cmd == "add_comment":
            tkt_id = args[0]
            content = args[1]
            is_internal = args[2].lower() in ("true", "1") if len(args) > 2 else False
            res = service.support_add_comment(ticket_id=tkt_id, content=content, is_internal=is_internal)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "update_ticket_status":
            tkt_id = args[0]
            status = args[1]
            res = service.support_update_ticket_status(ticket_id=tkt_id, status=status)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "get_invoices":
            cust_id = args[0]
            res = service.billing_get_invoices(customer_id=cust_id)
            print(json.dumps({"ok": True, "invoices": res}))

        elif cmd == "process_refund":
            inv_id = args[0]
            cust_id = args[1]
            amount = float(args[2])
            reason = args[3] if len(args) > 3 else "Customer satisfaction refund"
            approved_by = args[4] if len(args) > 4 and args[4] != "" else None
            res = service.billing_process_refund(
                invoice_id=inv_id,
                customer_id=cust_id,
                amount_usd=amount,
                reason=reason,
                approved_by_id=approved_by,
            )
            print(json.dumps({"ok": True, "refund": res}))

        elif cmd == "list_approvals":
            status = args[0] if len(args) > 0 and args[0] != "" else None
            res = service.list_approval_requests(status=status)
            print(json.dumps({"ok": True, "approvals": res}))

        elif cmd == "request_approval":
            req_type = args[0]
            approver_id = args[1]
            amount = float(args[2])
            reason = args[3] if len(args) > 3 else "Exception approval"
            res = service.workflow_request_approval(
                request_type=req_type,
                approver_id=approver_id,
                amount_usd=amount,
                reason=reason,
            )
            print(json.dumps({"ok": True, "request": res}))

        elif cmd == "decide_approval":
            req_id = args[0]
            decision = args[1]
            notes = args[2] if len(args) > 2 else ""
            res = service.decide_approval_request(request_id=req_id, decision=decision, notes=notes)
            print(json.dumps({"ok": True, "decision": res}))

        elif cmd == "read_inbox":
            user_email = args[0] if len(args) > 0 else "support-team@apexcorp.internal"
            res = service.email_read_inbox(user_email=user_email)
            print(json.dumps({"ok": True, "messages": res}))

        elif cmd == "send_email":
            sender = args[0]
            recipients = [r.strip() for r in args[1].split(",") if r.strip()]
            subject = args[2]
            body = args[3]
            res = service.email_send_message(
                sender_email=sender,
                recipient_emails=recipients,
                subject=subject,
                body=body,
            )
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "read_document":
            doc_id = args[0]
            res = service.document_read(document_id=doc_id)
            print(json.dumps({"ok": True, "document": res}))

        elif cmd == "get_audit_log":
            actor = args[0] if len(args) > 0 and args[0] != "" else None
            action = args[1] if len(args) > 1 and args[1] != "" else None
            res = service.get_audit_log(actor_id=actor, action=action)
            print(json.dumps({"ok": True, "audit_events": res}))

        elif cmd == "state_hash":
            h = service.calculate_state_hash()
            print(json.dumps({"ok": True, "state_hash": h}))

        elif cmd == "step_simulation":
            minutes = int(args[0]) if args else 15
            res = service.step_simulation(minutes=minutes)
            print(json.dumps({"ok": True, "step": res}))

        elif cmd == "submit_task":
            summary = args[0] if args else "Task completed"
            affected = args[1] if len(args) > 1 else ""
            res = service.submit_task(summary=summary, affected_ids=affected)
            print(json.dumps({"ok": True, "result": res}))

        else:
            print(json.dumps({"error": f"Unknown command: {cmd}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
