#!/usr/bin/env python3
"""CLI and REST Bridge for task_manager-ui Next.js application."""

import json
import os
import sys
from pathlib import Path

from task_sim.service import execute_tool, export_state, seed_database
from task_sim.identity import LOGGED_IN_USER

ROOT_DIR = Path(__file__).resolve().parent.parent

def resolve_db_path() -> Path:
    if "TASKS_DB" in os.environ:
        p = Path(os.environ["TASKS_DB"])
        if p.exists():
            return p
    var_db = Path("/var/lib/tasks/tasks.db")
    if var_db.exists():
        return var_db
    local_db = ROOT_DIR / "tasks.db"
    if not local_db.exists():
        local_db.parent.mkdir(parents=True, exist_ok=True)
        snap = ROOT_DIR / "tasks_seed_snapshot.sql"
        seed_database(local_db, snap)
    return local_db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: task_bridge.py <command> [args...]"}), file=sys.stderr)
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
        actor = sys.argv[4] if len(sys.argv) > 4 else LOGGED_IN_USER.user_id
        result = execute_tool(db_path, tool_name, args, actor_id=actor)
        print(json.dumps(result))

    elif cmd == "export_state":
        state = export_state(db_path)
        print(json.dumps(state))

    elif cmd == "list_tasks":
        raw_args = sys.argv[2] if len(sys.argv) > 2 else "{}"
        try:
            filters = json.loads(raw_args)
        except Exception:
            filters = {}
        res = execute_tool(db_path, "list_tasks", filters)
        print(json.dumps(res))

    elif cmd == "get_task":
        task_id = sys.argv[2]
        res = execute_tool(db_path, "get_task", {"task_id": task_id})
        print(json.dumps(res))

    elif cmd == "list_projects":
        res = execute_tool(db_path, "list_projects", {})
        print(json.dumps(res))

    elif cmd == "list_users":
        res = execute_tool(db_path, "list_users", {})
        print(json.dumps(res))

    elif cmd == "seed":
        snap = ROOT_DIR / "tasks_seed_snapshot.sql"
        seed_database(db_path, snap)
        print(json.dumps({"ok": True, "db": str(db_path)}))

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
