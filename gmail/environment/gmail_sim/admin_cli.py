"""Admin command-line interface for the Gmail simulation environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gmail_sim.protocol import ADMIN_SOCKET, request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gmail admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ping", help="Check if the world daemon is healthy")

    export_p = subparsers.add_parser("export_state", help="Export workspace state")
    export_p.add_argument("--out", help="Path to write state JSON to (defaults to stdout)")

    parser.add_argument("--socket", default=ADMIN_SOCKET, help="Path to admin socket")
    args = parser.parse_args(argv)

    if args.command == "ping":
        try:
            res = request(args.socket, {"op": "ping"})
            if res.get("ok"):
                print("PONG")
                return 0
            print(f"FAIL: {res}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1

    if args.command == "export_state":
        res = request(args.socket, {"op": "export_state"})
        if not res.get("ok"):
            print(f"Error: {res.get('error')}", file=sys.stderr)
            return 1

        state = res.get("result", {})
        if args.out:
            dest = Path(args.out)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(state, indent=2), encoding="utf-8")
        else:
            print(json.dumps(state, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
