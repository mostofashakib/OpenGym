#!/usr/bin/env python3
"""CLI and REST Bridge for slack-ui Next.js application."""

import json
import os
import sys
from pathlib import Path

from slack_sim.service import execute_tool, export_state, seed_database
from slack_sim.identity import LOGGED_IN_USER

ROOT_DIR = Path(__file__).resolve().parent.parent

def resolve_db_path() -> Path:
    if "SLACK_DB" in os.environ:
        p = Path(os.environ["SLACK_DB"])
        if p.exists():
            return p
    var_db = Path("/var/lib/slack/slack.db")
    if var_db.exists():
        return var_db
    local_db = ROOT_DIR / "slack.db"
    if not local_db.exists():
        local_db.parent.mkdir(parents=True, exist_ok=True)
        snap = ROOT_DIR / "slack_seed_snapshot.sql"
        seed_database(local_db, snap)
    return local_db

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: slack_bridge.py <command> [args...]"}), file=sys.stderr)
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

    elif cmd == "list_channels":
        res = execute_tool(db_path, "list_channels", {"limit": 100})
        print(json.dumps(res))

    elif cmd == "get_messages":
        channel_id = sys.argv[2] if len(sys.argv) > 2 else "C019"
        res = execute_tool(db_path, "get_channel_messages", {"channel_id": channel_id, "limit": 50})
        print(json.dumps(res))

    elif cmd == "get_threads":
        thread_ts = sys.argv[2]
        channel_id = sys.argv[3] if len(sys.argv) > 3 else "C019"
        res = execute_tool(db_path, "get_thread_replies", {"thread_ts": thread_ts, "channel_id": channel_id})
        print(json.dumps(res))

    elif cmd == "list_users":
        res = execute_tool(db_path, "list_users", {"limit": 100})
        print(json.dumps(res))

    elif cmd == "seed":
        snap = ROOT_DIR / "slack_seed_snapshot.sql"
        seed_database(db_path, snap)
        print(json.dumps({"ok": True, "db": str(db_path)}))

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
