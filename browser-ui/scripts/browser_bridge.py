#!/usr/bin/env python3
"""CLI and REST Bridge for browser-ui Next.js application using dependency injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from browser_sim.context import BrowserContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browser bridge CLI")
    parser.add_argument("--db", type=Path, default=None, help="Injected database path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # call_tool
    tool_parser = subparsers.add_parser("call_tool")
    tool_parser.add_argument("tool_name", type=str)
    tool_parser.add_argument("payload", type=str, nargs="?", default="{}")

    # export_state
    subparsers.add_parser("export_state")

    # get_dashboard
    subparsers.add_parser("get_dashboard")

    # seed
    subparsers.add_parser("seed")

    return parser


def create_context(args: argparse.Namespace) -> BrowserContext:
    """Dependency injection factory for BrowserContext."""
    ctx = BrowserContext.from_env()
    db_path = args.db or ctx.db_path
    return BrowserContext(db_path=db_path)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    context = create_context(args)

    if args.command == "call_tool":
        try:
            payload = json.loads(args.payload)
        except Exception:
            payload = {}
        result = context.execute_tool(args.tool_name, payload)
        print(json.dumps(result))

    elif args.command == "export_state":
        print(json.dumps(context.export_state()))

    elif args.command == "get_dashboard":
        print(json.dumps(context.get_dashboard()))

    elif args.command == "seed":
        context.seed()
        print(json.dumps({"ok": True, "db": str(context.db_path)}))



if __name__ == "__main__":
    main()
