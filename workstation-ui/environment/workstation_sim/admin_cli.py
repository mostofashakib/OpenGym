"""Admin command-line interface for the Workstation simulation environment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workstation_sim.context import WorkstationContext
from workstation_sim.service import calculate_state_hash, export_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Workstation admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("seed", help="Seed or reset database to initial state")

    export_p = subparsers.add_parser("export_state", help="Export workspace state as JSON")
    export_p.add_argument("--out", help="Path to write state JSON to (defaults to stdout)")

    hash_p = subparsers.add_parser("hash", help="Compute canonical SHA-256 state hash")

    parser.add_argument("--db", help="Path to workstation SQLite database")
    args = parser.parse_args(argv)

    environ = {}
    if args.db:
        environ["WORKSTATION_DB"] = args.db
    ctx = WorkstationContext.from_env(environ)

    if args.command == "seed":
        res = ctx.seed_db()
        print(f"Seeded database: {res}")
        return 0

    if args.command == "export_state":
        state = ctx.export_state()
        if args.out:
            dest = Path(args.out)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(state, indent=2), encoding="utf-8")
        else:
            print(json.dumps(state, indent=2))
        return 0

    if args.command == "hash":
        h = ctx.calculate_state_hash()
        print(h)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
