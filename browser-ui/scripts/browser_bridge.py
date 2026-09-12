#!/usr/bin/env python3
"""CLI and REST Bridge for browser-ui Next.js application."""

import json
import os
import sys
from pathlib import Path

# Add environment to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
ENV_DIR = ROOT_DIR / "environment"
if str(ENV_DIR) not in sys.path:
    sys.path.insert(0, str(ENV_DIR))

from browser_sim.service import execute_tool, export_state, BrowserService
from browser_sim.sqlite_common import get_connection
from browser_sim.seed import seed_database

def resolve_db_path() -> Path:
    if "BROWSER_DB" in os.environ:
        p = Path(os.environ["BROWSER_DB"])
        if p.exists():
            return p
    var_db = Path("/var/lib/browser/browser.db")
    if var_db.exists():
        return var_db
    local_db = ROOT_DIR / "browser.db"
    if not local_db.exists():
        local_db.parent.mkdir(parents=True, exist_ok=True)
        seed_database(local_db)
    return local_db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: browser_bridge.py <command> [args...]"}), file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    db_path = resolve_db_path()

    if cmd == "call_tool":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing tool name"}), file=sys.stderr)
            sys.exit(1)
        tool_name = sys.argv[2]
        raw_args = sys.argv[3] if len(sys.argv) > 3 else "{}"
        try:
            args = json.loads(raw_args)
        except Exception:
            args = {}
        result = execute_tool(db_path, tool_name, args)
        print(json.dumps(result))

    elif cmd == "export_state":
        with get_connection(db_path) as conn:
            state = export_state(conn)
            print(json.dumps(state))

    elif cmd == "get_dashboard":
        with get_connection(db_path) as conn:
            orders = [dict(r) for r in conn.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()]
            vendors = [dict(r) for r in conn.execute("SELECT * FROM vendors ORDER BY id ASC").fetchall()]
            filings = [dict(r) for r in conn.execute("SELECT * FROM compliance_filings ORDER BY id DESC").fetchall()]
            sub_row = conn.execute("SELECT id, timestamp, summary, audited_ids FROM task_submission WHERE id = 1").fetchone()
            submission = dict(sub_row) if sub_row else None
            logs = [dict(r) for r in conn.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT 10").fetchall()]

            output = {
                "orders": orders,
                "vendors": vendors,
                "compliance_filings": filings,
                "submission": submission,
                "recent_actions": logs,
                "stats": {
                    "pending_orders": sum(1 for o in orders if o["status"] == "PENDING_APPROVAL"),
                    "high_risk_vendors": sum(1 for v in vendors if v["risk_level"] in ("CRITICAL", "HIGH")),
                    "expired_soc2": sum(1 for v in vendors if v["soc2_certified"] == 0),
                    "total_pending_amount": sum(o["amount"] for o in orders if o["status"] == "PENDING_APPROVAL"),
                }
            }
            print(json.dumps(output))

    elif cmd == "seed":
        seed_database(db_path)
        print(json.dumps({"ok": True, "db": str(db_path)}))

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
