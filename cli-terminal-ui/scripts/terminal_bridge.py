#!/usr/bin/env python3
"""CLI and REST Bridge for terminal-ui Next.js application."""

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

from terminal_sim.service import execute_tool, TerminalService
from terminal_sim.sqlite_common import get_connection
from terminal_sim.seed import seed_database

def resolve_db_path() -> Path:
    if "TERMINAL_DB" in os.environ:
        p = Path(os.environ["TERMINAL_DB"])
        if p.exists():
            return p
    var_db = Path("/var/lib/terminal/terminal.db")
    if var_db.exists():
        return var_db
    local_db = ROOT_DIR / "terminal.db"
    if not local_db.exists():
        local_db.parent.mkdir(parents=True, exist_ok=True)
        seed_database(local_db)
    return local_db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: terminal_bridge.py <command> [args...]"}), file=sys.stderr)
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

    elif cmd == "get_system":
        sys_info = execute_tool(db_path, "inspect_system", {})
        with get_connection(db_path) as conn:
            # Also get process list
            procs = conn.execute("SELECT pid, name, command, user, cpu_percent, memory_mb, status FROM processes WHERE status != 'terminated' ORDER BY cpu_percent DESC").fetchall()
            proc_list = [dict(row) for row in procs]
            # Also get service list
            services = conn.execute("SELECT name, status, description, pid, enabled FROM services").fetchall()
            svc_list = [dict(row) for row in services]
            # Also check submission
            sub = conn.execute("SELECT id, timestamp, summary, actions_taken FROM task_submission WHERE id = 1").fetchone()
            sub_info = dict(sub) if sub else {"submitted": 0}

            output = {
                "system": sys_info,
                "processes": proc_list,
                "services": svc_list,
                "submission": sub_info,
            }
            print(json.dumps(output))

    elif cmd == "list_files":
        directory = sys.argv[2] if len(sys.argv) > 2 else "/"
        with get_connection(db_path) as conn:
            rows = conn.execute(
                "SELECT path, owner, group_owner, permissions, file_type, size, modified_at FROM files ORDER BY path ASC"
            ).fetchall()
            files = [dict(row) for row in rows]
            print(json.dumps(files))

    elif cmd == "seed":
        seed_database(db_path)
        print(json.dumps({"ok": True, "db": str(db_path)}))

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
