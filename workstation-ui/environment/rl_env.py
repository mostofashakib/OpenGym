#!/usr/bin/env python3
"""JSON CLI contract for the Workstation RL Environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from workstation_sim.context import WorkstationContext
from workstation_sim.tool_definitions import TOOL_DEFINITIONS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Workstation RL Environment CLI")
    parser.add_argument(
        "command",
        choices=["setup", "reset", "tools", "step", "state", "history"],
        help="RL lifecycle command to execute",
    )
    parser.add_argument("--db", default=None, help="Path to SQLite database")
    parser.add_argument("--session-cookie", default="default_sess", help="Session ID")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for environment")
    parser.add_argument("--tool-name", default="", help="Tool name for step command")
    parser.add_argument("--input-payload", default="{}", help="JSON input arguments for step")
    parser.add_argument("--instruction", default="", help="Instruction for episode")

    args = parser.parse_args(argv)

    environ = {}
    if args.db:
        environ["WORKSTATION_DB"] = args.db
    environ["WORKSTATION_SEED"] = str(args.seed)

    ctx = WorkstationContext.from_env(environ)

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
        tools_formatted = [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            }
            for t in TOOL_DEFINITIONS
        ]
        print(json.dumps({"ok": True, "tools": tools_formatted}))
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
            res = ctx.execute_tool(args.tool_name, payload)
            print(json.dumps({"ok": True, "result": res}))
            return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1

    elif args.command == "state":
        state = ctx.export_state()
        summary = {
            "customers_count": len(state.get("customers", [])),
            "invoices_count": len(state.get("invoices", [])),
            "tickets_count": len(state.get("tickets", [])),
            "emails_count": len(state.get("emails", [])),
            "refunds_count": len(state.get("refunds", [])),
            "action_logs_count": len(state.get("action_logs", [])),
        }
        print(json.dumps({"ok": True, "state_summary": summary}))
        return 0

    elif args.command == "history":
        state = ctx.export_state()
        logs = state.get("action_logs", [])
        print(json.dumps({"ok": True, "history": logs, "total_actions": len(logs)}))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
