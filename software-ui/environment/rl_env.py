#!/usr/bin/env python3
"""JSON CLI contract for the Procedural Software RL Environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from software_sim.context import SoftwareContext


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Software RL Environment CLI")
    parser.add_argument(
        "command",
        choices=["setup", "reset", "tools", "step", "state", "history"],
        help="RL lifecycle command to execute",
    )
    parser.add_argument("--db", default=None, help="Path to SQLite database")
    parser.add_argument("--spec", default=None, help="Path to application specification JSON")
    parser.add_argument("--domain", default="logistics", help="Domain to generate (default: logistics)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for environment")
    parser.add_argument("--session-cookie", default="default_sess", help="Session ID")
    parser.add_argument("--tool-name", default="", help="Tool name for step command")
    parser.add_argument("--input-payload", default="{}", help="JSON input arguments for step")
    parser.add_argument("--instruction", default="", help="Instruction for episode")

    args = parser.parse_args(argv)

    ctx = SoftwareContext(
        db_path=args.db or "/tmp/software_sim.db",
        app_spec_path=args.spec,
        seed=args.seed,
    )

    if args.command == "setup":
        ctx.ensure_initialized()
        print(json.dumps({"ok": True, "status": "initialized", "db": str(ctx.db_path)}))
        return 0

    elif args.command == "reset":
        ctx.reset(domain=args.domain, seed=args.seed)
        print(json.dumps({
            "ok": True,
            "session_cookie": args.session_cookie,
            "seed": args.seed,
            "domain": args.domain,
            "instruction": args.instruction,
            "status": "ready",
        }))
        return 0

    elif args.command == "tools":
        schema = ctx.service.get_schema()
        print(json.dumps({"ok": True, "app_schema": schema}))
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
            if name in ("get_schema", "get_application_schema"):
                res = ctx.service.get_schema()
            elif name in ("search_entities", "search"):
                res = ctx.service.search_entities(
                    payload.get("entity_name", ""),
                    query=payload.get("query"),
                    status_filter=payload.get("status_filter") or payload.get("status"),
                    limit=int(payload.get("limit", 50)),
                )
            elif name in ("get_entity", "get_entity_details"):
                res = ctx.service.get_entity(payload.get("entity_name", ""), payload.get("entity_id", ""))
            elif name == "create_entity":
                res = ctx.service.create_entity(payload.get("entity_name", ""), payload.get("fields", {}), actor=payload.get("actor", "agent"))
            elif name in ("update_entity", "update_entity_fields"):
                res = ctx.service.update_entity(payload.get("entity_name", ""), payload.get("entity_id", ""), payload.get("fields", {}), actor=payload.get("actor", "agent"))
            elif name in ("transition_entity", "transition_entity_workflow"):
                res = ctx.service.transition_entity(
                    payload.get("entity_name", ""),
                    payload.get("entity_id", ""),
                    payload.get("action", ""),
                    actor=payload.get("actor", "agent"),
                    actor_role=payload.get("actor_role", "admin"),
                    payload=payload.get("payload") or payload.get("fields"),
                )
            elif name in ("get_audit_log", "get_audit_trail"):
                res = ctx.service.get_audit_log(entity_id=payload.get("entity_id"), limit=int(payload.get("limit", 50)))
            else:
                res = {"error": f"Unknown tool '{name}'"}
            print(json.dumps({"ok": True, "result": res}))
            return 0
        except Exception as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1

    elif args.command == "state":
        state_hash = ctx.calculate_state_hash()
        print(json.dumps({"ok": True, "state_hash": state_hash}))
        return 0

    elif args.command == "history":
        logs = ctx.service.get_audit_log(limit=100)
        print(json.dumps({"ok": True, "history": logs, "total_actions": len(logs)}))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
