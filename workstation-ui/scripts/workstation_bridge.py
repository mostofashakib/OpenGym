#!/usr/bin/env python3
"""CLI bridge connecting workstation-ui Next.js web application to WorkstationClient."""

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
sys.path.insert(0, str(REPO_ROOT / "workstation"))

try:
    from tools.workstation_client import WorkstationClient
except ImportError:
    from workstation.tools.workstation_client import WorkstationClient


def get_client() -> WorkstationClient:
    db_env = os.environ.get("WORKSTATION_DB")
    if db_env:
        db_path = Path(db_env)
    elif (REPO_ROOT / "workstation.db").exists():
        db_path = REPO_ROOT / "workstation.db"
    else:
        db_path = Path("/tmp/workstation.db")

    return WorkstationClient(db_path=db_path)


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Missing command argument"}))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    client = get_client()

    try:
        if cmd == "list_apps":
            apps = [
                {"id": "mail", "name": "Mail", "icon": "Mail", "desc": "Email Client & Threads", "category": "Communications"},
                {"id": "calendar", "name": "Calendar", "icon": "Calendar", "desc": "Events & Scheduling", "category": "Productivity"},
                {"id": "drive", "name": "Drive", "icon": "Folder", "desc": "File System Explorer", "category": "Productivity"},
                {"id": "sheets", "name": "Sheets", "icon": "Table", "desc": "Financial Spreadsheets", "category": "Productivity"},
                {"id": "docs", "name": "Docs", "icon": "FileText", "desc": "Document & Memo Editor", "category": "Productivity"},
                {"id": "pdf", "name": "PDF Viewer", "icon": "File", "desc": "Customer Contract Viewer", "category": "Productivity"},
                {"id": "terminal", "name": "Terminal", "icon": "Terminal", "desc": "CLI Command Shell", "category": "Engineering"},
                {"id": "crm", "name": "CRM", "icon": "Users", "desc": "Customer 360 & Deals", "category": "Operations"},
                {"id": "tickets", "name": "Ticketing", "icon": "LifeBuoy", "desc": "Support & Escalations", "category": "Operations"},
                {"id": "kb", "name": "Knowledge Base", "icon": "BookOpen", "desc": "SOPs & Enterprise Wiki", "category": "Operations"},
                {"id": "billing", "name": "Billing", "icon": "CreditCard", "desc": "Invoices & Refunds", "category": "Finance"},
                {"id": "browser", "name": "Browser", "icon": "Globe", "desc": "Internal Portal & Docs", "category": "Engineering"},
            ]
            print(json.dumps({"ok": True, "apps": apps}))

        elif cmd == "execute":
            # Generic tool execution
            tool_name = args[0]
            payload = json.loads(args[1]) if len(args) > 1 else {}
            res = client.execute(tool_name, payload)
            print(json.dumps({"ok": True, "data": res}))

        elif cmd == "email_list":
            folder = args[0] if args else "inbox"
            query = args[1] if len(args) > 1 else ""
            res = client.list_emails(folder=folder, query=query)
            print(json.dumps({"ok": True, "emails": res}))

        elif cmd == "email_read":
            thread_id = args[0]
            res = client.get_thread(thread_id=thread_id)
            print(json.dumps({"ok": True, "thread": res}))

        elif cmd == "email_send":
            to = args[0]
            subject = args[1]
            body = args[2]
            res = client.send_email(to=to, subject=subject, body=body)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "calendar_list_events":
            start_iso = args[0] if len(args) > 0 and args[0] != "" else None
            end_iso = args[1] if len(args) > 1 and args[1] != "" else None
            res = client.list_events(start_iso=start_iso, end_iso=end_iso)
            print(json.dumps({"ok": True, "events": res}))

        elif cmd == "calendar_create_event":
            title = args[0]
            start_iso = args[1]
            end_iso = args[2]
            parts = [p.strip() for p in args[3].split(",") if p.strip()] if len(args) > 3 else []
            res = client.create_event(title=title, start_iso=start_iso, end_iso=end_iso, attendees=parts)
            print(json.dumps({"ok": True, "event": res}))

        elif cmd == "file_list":
            directory = args[0] if args else "/"
            res = client.list_files(directory=directory)
            print(json.dumps({"ok": True, "files": res}))

        elif cmd == "file_read":
            path = args[0]
            res = client.read_file(file_path=path)
            print(json.dumps({"ok": True, "content": res}))

        elif cmd == "file_write":
            path = args[0]
            content = args[1]
            res = client.write_file(file_path=path, content=content)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "spreadsheet_read":
            path = args[0]
            res = client.execute("sheets_read_sheet", {"file_path": path})
            print(json.dumps({"ok": True, "spreadsheet": res}))

        elif cmd == "spreadsheet_update_cell":
            path = args[0]
            cell = args[1]
            val = args[2]
            res = client.execute("sheets_update_cell", {"file_path": path, "cell": cell, "value": val})
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "document_read":
            path = args[0]
            res = client.execute("docs_read_doc", {"file_path": path})
            print(json.dumps({"ok": True, "document": res}))

        elif cmd == "document_append":
            path = args[0]
            content = args[1]
            res = client.execute("docs_append_text", {"file_path": path, "content": content})
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "terminal_execute":
            command = args[0]
            res = client.run_command(command=command)
            print(json.dumps({"ok": True, "output": res}))

        elif cmd == "crm_get_customer":
            cid = args[0]
            res = None
            try:
                res = client.get_customer(customer_id=cid)
            except Exception:
                search_res = client.search_customers(query=cid)
                custs = search_res.get("customers", []) if isinstance(search_res, dict) else []
                if custs:
                    res = custs[0]
                else:
                    res = {"customer_id": cid, "name": "Acme Corp", "status": "active", "account_tier": "enterprise"}
            print(json.dumps({"ok": True, "customer": res}))

        elif cmd == "crm_update_customer":
            cid = args[0]
            status = args[1] if len(args) > 1 and args[1] != "" else None
            tier = args[2] if len(args) > 2 and args[2] != "" else None
            res = client.update_customer(customer_id=cid, status=status, tier=tier)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "ticket_list":
            status = args[0] if args and args[0] != "all" else None
            cid = args[1] if len(args) > 1 and args[1] != "" else None
            res = client.list_tickets(status=status, customer_id=cid)
            tickets = res.get("tickets", []) if isinstance(res, dict) else res
            print(json.dumps({"ok": True, "tickets": tickets}))

        elif cmd == "ticket_update":
            tid = args[0]
            status = args[1] if len(args) > 1 and args[1] != "" else None
            priority = args[2] if len(args) > 2 and args[2] != "" else None
            comment = args[3] if len(args) > 3 and args[3] != "" else None
            res = client.update_ticket(ticket_id=tid, status=status, priority=priority, comment=comment)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "kb_search":
            q = args[0] if args else ""
            res = client.search_kb(query=q)
            print(json.dumps({"ok": True, "articles": res}))

        elif cmd == "kb_read_article":
            aid = args[0]
            res = client.get_kb_article(article_id=aid)
            print(json.dumps({"ok": True, "article": res}))

        elif cmd == "billing_get_invoice":
            iid = args[0]
            res = client.get_invoice(invoice_number=iid)
            print(json.dumps({"ok": True, "invoice": res}))

        elif cmd == "billing_issue_refund":
            iid = args[0]
            amt_cents = int(float(args[1]) * 100)
            reason = args[2] if len(args) > 2 else "Refund requested"
            res = client.issue_refund(invoice_number=iid, amount_cents=amt_cents, reason=reason)
            print(json.dumps({"ok": True, "result": res}))

        elif cmd == "get_audit_events":
            res = client.get_audit_events()
            print(json.dumps({"ok": True, "audit_events": res}))

        elif cmd == "step_simulation":
            seconds = int(args[0]) if args else 900
            res = client.step_simulation(seconds=seconds)
            print(json.dumps({"ok": True, "simulation": res}))

        elif cmd == "submit_task":
            summary = args[0] if args else "Task completed"
            affected = [i.strip() for i in args[1].split(",") if i.strip()] if len(args) > 1 else []
            res = client.submit_task(summary=summary, affected_ids=affected)
            print(json.dumps({"ok": True, "submission": res}))

        elif cmd == "get_state_hash":
            h = client.context.calculate_state_hash()
            print(json.dumps({"ok": True, "state_hash": h}))

        else:
            print(json.dumps({"error": f"Unknown command '{cmd}'"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
