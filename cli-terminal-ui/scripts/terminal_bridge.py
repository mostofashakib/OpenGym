#!/usr/bin/env python3
"""CLI and REST Bridge for terminal-ui Next.js application using dependency injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from terminal_sim.context import TerminalContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Terminal bridge CLI")
    parser.add_argument("--db", type=Path, default=None, help="Injected database path")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # call_tool
    tool_parser = subparsers.add_parser("call_tool")
    tool_parser.add_argument("tool_name", type=str)
    tool_parser.add_argument("payload", type=str, nargs="?", default="{}")

    # execute_command
    cmd_parser = subparsers.add_parser("execute_command")
    cmd_parser.add_argument("command_text", type=str)

    # get_system
    subparsers.add_parser("get_system")

    # list_files
    files_parser = subparsers.add_parser("list_files")
    files_parser.add_argument("directory", type=str, nargs="?", default="/")

    # seed
    subparsers.add_parser("seed")

    return parser


def create_context(args: argparse.Namespace) -> TerminalContext:
    """Dependency injection factory for TerminalContext."""
    ctx = TerminalContext.from_env()
    db_path = args.db or ctx.db_path
    return TerminalContext(db_path=db_path)


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

    elif args.command == "execute_command":
        result = context.execute_tool("execute_command", {"command": args.command_text})
        print(json.dumps(result))

    elif args.command == "get_system":
        print(json.dumps(context.get_system()))

    elif args.command == "list_files":
        print(json.dumps(context.list_files(args.directory)))

    elif args.command == "seed":
        context.seed()
        print(json.dumps({"ok": True, "db": str(context.db_path)}))



if __name__ == "__main__":
    main()
