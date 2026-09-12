#!/usr/bin/env python3
"""CLI and REST Bridge for task_manager-ui Next.js application using dependency injection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task_sim.context import TaskContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Task Manager bridge CLI")
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

    # list_tasks
    task_parser = subparsers.add_parser("list_tasks")
    task_parser.add_argument("payload", type=str, nargs="?", default="{}")

    # get_task
    get_parser = subparsers.add_parser("get_task")
    get_parser.add_argument("task_id", type=str)

    # list_projects
    subparsers.add_parser("list_projects")

    # list_users
    subparsers.add_parser("list_users")

    # seed
    subparsers.add_parser("seed")

    return parser


def create_context(args: argparse.Namespace) -> TaskContext:
    """Dependency injection factory for TaskContext."""
    ctx = TaskContext.from_env()
    db_path = args.db or ctx.db_path
    snapshot_path = args.snapshot or ctx.snapshot_path
    actor_id = getattr(args, "actor_pos", None) or args.actor or ctx.actor_id
    return TaskContext(db_path=db_path, snapshot_path=snapshot_path, actor_id=actor_id)


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

    elif args.command == "list_tasks":
        try:
            payload = json.loads(args.payload)
        except Exception:
            payload = {}
        print(json.dumps(context.execute_tool("list_tasks", payload)))

    elif args.command == "get_task":
        print(json.dumps(context.execute_tool("get_task", {"task_id": args.task_id})))

    elif args.command == "list_projects":
        print(json.dumps(context.execute_tool("list_projects", {})))

    elif args.command == "list_users":
        print(json.dumps(context.execute_tool("list_users", {})))

    elif args.command == "seed":
        context.seed()
        print(json.dumps({"ok": True, "db": str(context.db_path)}))


if __name__ == "__main__":
    main()
