"""Privileged Admin CLI for browser environment."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from browser_sim.protocol import request
from browser_sim.seed import seed_database
from browser_sim.service import export_state
from browser_sim.sqlite_common import get_connection

ADMIN_SOCKET = os.environ.get("BROWSER_ADMIN_SOCKET", "/run/browser/admin.sock")
DB_PATH = os.environ.get("BROWSER_DB", "/var/lib/browser/browser.db")


def main() -> None:
    parser = argparse.ArgumentParser(description="Browser Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ping
    subparsers.add_parser("ping")

    # export_state
    exp = subparsers.add_parser("export_state")
    exp.add_argument("--out", default="/var/lib/browser/state-export.json")

    # seed
    seed = subparsers.add_parser("seed")
    seed.add_argument("--db", default=DB_PATH)

    args = parser.parse_args()

    if args.command == "ping":
        if os.path.exists(ADMIN_SOCKET):
            try:
                resp = request(ADMIN_SOCKET, {"op": "ping"})
                if resp.get("ok"):
                    print("pong")
                    return
            except Exception:
                pass
        if Path(DB_PATH).exists():
            print("pong (db direct)")
            return
        print("ping failed", file=sys.stderr)
        sys.exit(1)

    elif args.command == "seed":
        seed_database(args.db)
        print(f"Seeded browser database at {args.db}")

    elif args.command == "export_state":
        state = None
        if os.path.exists(ADMIN_SOCKET):
            try:
                resp = request(ADMIN_SOCKET, {"op": "export_state"})
                if resp.get("ok"):
                    state = resp.get("result")
            except Exception:
                pass

        if state is None:
            db_candidates = [
                Path(DB_PATH),
                Path("/var/lib/browser/browser.db"),
                Path("/tmp/test_browser.db"),
                Path("browser.db"),
            ]
            for cand in db_candidates:
                if cand.exists():
                    with get_connection(cand) as conn:
                        state = export_state(conn)
                        break

        if state is None:
            print("Could not retrieve state from socket or database", file=sys.stderr)
            sys.exit(1)

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"Exported state to {out_path}")


if __name__ == "__main__":
    main()
