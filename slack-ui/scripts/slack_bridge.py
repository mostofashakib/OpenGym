#!/usr/bin/env python3
"""CLI and REST Bridge for slack-ui Next.js application using dependency injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from slack_sim.context import SlackContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slack bridge CLI")
    parser.add_argument("--db", type=Path, default=None, help="Injected database path")
    parser.add_argument("--snapshot", type=Path, default=None, help="Injected snapshot path")
    parser.add_argument("--actor", type=str, default=None, help="Injected actor user ID")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # call_tool
    tool_parser = subparsers.add_parser("call_tool")
    tool_parser.add_argument("tool_name", type=str)
    tool_parser.add_argument("payload", type=str, nargs="?", default="{}")
    tool_parser.add_argument("actor_pos", type=str, nargs="?", default=None)

    # export_state
    subparsers.add_parser("export_state")

    # list_channels
    subparsers.add_parser("list_channels")

    # get_messages
    msg_parser = subparsers.add_parser("get_messages")
    msg_parser.add_argument("channel_id", type=str, nargs="?", default="C019")

    # get_threads
    thread_parser = subparsers.add_parser("get_threads")
    thread_parser.add_argument("thread_ts", type=str)
    thread_parser.add_argument("channel_id", type=str, nargs="?", default="C019")

    # list_users
    subparsers.add_parser("list_users")

    # seed
    subparsers.add_parser("seed")

    return parser


def create_context(args: argparse.Namespace) -> SlackContext:
    """Dependency injection factory for SlackContext."""
    ctx = SlackContext.from_env()
    db_path = args.db or ctx.db_path
    snapshot_path = args.snapshot or ctx.snapshot_path
    actor_id = getattr(args, "actor_pos", None) or args.actor or ctx.actor_id
    return SlackContext(db_path=db_path, snapshot_path=snapshot_path, actor_id=actor_id)


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

    elif args.command == "list_channels":
        print(json.dumps(context.execute_tool("list_channels", {"limit": 100})))

    elif args.command == "get_messages":
        print(json.dumps(context.execute_tool("get_channel_messages", {"channel_id": args.channel_id, "limit": 50})))

    elif args.command == "get_threads":
        print(json.dumps(context.execute_tool("get_thread_replies", {"thread_ts": args.thread_ts, "channel_id": args.channel_id})))

    elif args.command == "list_users":
        print(json.dumps(context.execute_tool("list_users", {"limit": 100})))

    elif args.command == "seed":
        context.seed()
        print(json.dumps({"ok": True, "db": str(context.db_path)}))


if __name__ == "__main__":
    main()
