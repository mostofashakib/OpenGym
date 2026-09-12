"""Agent CLI for browser environment."""

from __future__ import annotations

import argparse
import json
import os
import sys

from browser_sim.protocol import request

AGENT_SOCKET = os.environ.get("BROWSER_SOCKET", "/run/browser/agent.sock")


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # navigate
    nav_parser = subparsers.add_parser("navigate")
    nav_parser.add_argument("url", help="URL to navigate to")

    # get_page
    subparsers.add_parser("get_page")

    # click
    click_parser = subparsers.add_parser("click")
    click_parser.add_argument("element_id", help="Element ID to click")

    # type
    type_parser = subparsers.add_parser("type")
    type_parser.add_argument("element_id", help="Element ID")
    type_parser.add_argument("text", help="Text to input")

    # submit
    sub_parser = subparsers.add_parser("submit")
    sub_parser.add_argument("--summary", required=True)
    sub_parser.add_argument("--audited-ids", nargs="*", default=[])

    args = parser.parse_args()

    tool_name = ""
    tool_args = {}
    if args.command == "navigate":
        tool_name = "navigate"
        tool_args = {"url": args.url}
    elif args.command == "get_page":
        tool_name = "get_page"
        tool_args = {}
    elif args.command == "click":
        tool_name = "click"
        tool_args = {"element_id": args.element_id}
    elif args.command == "type":
        tool_name = "type_text"
        tool_args = {"element_id": args.element_id, "text": args.text}
    elif args.command == "submit":
        tool_name = "submit_task"
        tool_args = {"summary": args.summary, "audited_ids": args.audited_ids}

    try:
        resp = request(AGENT_SOCKET, {"op": "call_tool", "tool": tool_name, "args": tool_args})
        print(json.dumps(resp, indent=2))
    except Exception as exc:
        print(f"Error communicating with browser daemon: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
