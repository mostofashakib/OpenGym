"""CLI runner for Gmail environment actions.

Allows executing tools via:
  python3 -m tools.gmail_cli <tool_name> [--input-payload '{"arg": "val"}']
  python3 -m tools.gmail_cli list_tools
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from tools.gmail_client import GmailClient
from tools.tool_definitions import get_tool_definitions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gmail CLI tool executor")
    parser.add_argument("tool", help="Name of the tool or 'list_tools'")
    parser.add_argument("--input-payload", default="{}", help="JSON dictionary of arguments")
    parser.add_argument("--base-url", default=None, help="Base URL of Gmail server")

    args, unknown = parser.parse_known_args(argv)

    if args.tool == "list_tools":
        print(json.dumps({"ok": True, "result": {"tools": list(get_tool_definitions())}}, indent=2))
        return 0

    try:
        payload: dict[str, Any] = json.loads(args.input_payload)
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": f"Invalid JSON in --input-payload: {exc}"}), file=sys.stderr)
        return 1

    # Parse any --key value pairs from unknown args to make CLI usage even easier
    i = 0
    while i < len(unknown):
        key = unknown[i]
        if key.startswith("--"):
            clean_key = key[2:].replace("-", "_")
            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                val = unknown[i + 1]
                # Cast booleans / ints / comma-separated lists if needed
                if val.lower() == "true":
                    payload[clean_key] = True
                elif val.lower() == "false":
                    payload[clean_key] = False
                elif val.isdigit():
                    payload[clean_key] = int(val)
                elif "," in val:
                    payload[clean_key] = val.split(",")
                else:
                    payload[clean_key] = val
                i += 2
                continue
            else:
                payload[clean_key] = True
                i += 1
                continue
        i += 1

    client_kwargs = {}
    if args.base_url:
        client_kwargs["base_url"] = args.base_url

    client = GmailClient(**client_kwargs)
    result = client.execute_tool(args.tool, payload)
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
