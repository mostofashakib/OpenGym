"""Agent command-line interface for the Gmail simulation environment."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from gmail_sim.protocol import AGENT_SOCKET, request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gmail agent CLI")
    parser.add_argument("tool", help="Tool name or 'list_tools'")
    parser.add_argument("--input-payload", default="{}", help="JSON arguments dictionary")
    parser.add_argument("--socket", default=AGENT_SOCKET, help="Path to agent socket")

    args, unknown = parser.parse_known_args(argv)

    try:
        payload: dict[str, Any] = json.loads(args.input_payload)
    except json.JSONDecodeError as exc:
        print(json.dumps({"ok": False, "error": f"Invalid JSON payload: {exc}"}), file=sys.stderr)
        return 1

    i = 0
    while i < len(unknown):
        key = unknown[i]
        if key.startswith("--"):
            clean_key = key[2:].replace("-", "_")
            if i + 1 < len(unknown) and not unknown[i + 1].startswith("--"):
                val = unknown[i + 1]
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

    req = {"tool": args.tool, "arguments": payload}
    try:
        res = request(args.socket, req)
        print(json.dumps(res, sort_keys=True))
        return 0 if res.get("ok", True) else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
