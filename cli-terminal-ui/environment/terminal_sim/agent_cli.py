"""Agent CLI for terminal environment."""

from __future__ import annotations

import argparse
import json
import os
import sys

from terminal_sim.protocol import request

AGENT_SOCKET = os.environ.get("TERMINAL_SOCKET", "/run/terminal/agent.sock")


def main() -> None:
    parser = argparse.ArgumentParser(description="Terminal Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("cmd", help="Command to execute")
    run_parser.add_argument("--cwd", default="/home/admin", help="Working directory")

    # read file
    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("path", help="Path to file")
    read_parser.add_argument("--offset", type=int, default=0)
    read_parser.add_argument("--limit", type=int, default=100)

    # write file
    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("path", help="Path to file")
    write_parser.add_argument("content", help="File content")
    write_parser.add_argument("--mode", default="write", choices=["write", "append"])

    # ps
    subparsers.add_parser("ps")

    # system
    subparsers.add_parser("inspect")

    # submit
    sub_parser = subparsers.add_parser("submit")
    sub_parser.add_argument("--summary", required=True)
    sub_parser.add_argument("--actions", nargs="*", default=[])

    args = parser.parse_args()

    tool_name = ""
    tool_args = {}
    if args.command == "run":
        tool_name = "run_command"
        tool_args = {"command": args.cmd, "cwd": args.cwd}
    elif args.command == "read":
        tool_name = "read_file"
        tool_args = {"path": args.path, "offset": args.offset, "limit": args.limit}
    elif args.command == "write":
        tool_name = "write_file"
        tool_args = {"path": args.path, "content": args.content, "mode": args.mode}
    elif args.command == "ps":
        tool_name = "list_processes"
        tool_args = {}
    elif args.command == "inspect":
        tool_name = "inspect_system"
        tool_args = {}
    elif args.command == "submit":
        tool_name = "submit_task"
        tool_args = {"summary": args.summary, "actions_taken": args.actions}

    try:
        resp = request(AGENT_SOCKET, {"op": "call_tool", "tool": tool_name, "args": tool_args})
        print(json.dumps(resp, indent=2))
    except Exception as exc:
        print(f"Error communicating with terminal daemon: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
