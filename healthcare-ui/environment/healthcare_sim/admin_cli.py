"""Admin CLI for the Healthcare Simulation Environment."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .context import HealthcareContext
from .db_generator import create_dynamic_database
from .task_generator import TaskGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Healthcare Environment Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # seed command
    seed_p = subparsers.add_parser("seed", help="Seed database with 1,000 patients and 50 staff")
    seed_p.add_argument("--db-path", default="/tmp/healthcare_sim.db")
    seed_p.add_argument("--seed", type=int, default=42)

    # hash command
    hash_p = subparsers.add_parser("hash", help="Compute SHA-256 state hash")
    hash_p.add_argument("--db-path", default="/tmp/healthcare_sim.db")

    # export command
    export_p = subparsers.add_parser("export", help="Export clinical database state as JSON")
    export_p.add_argument("--db-path", default="/tmp/healthcare_sim.db")
    export_p.add_argument("--out", default="-")

    # task command
    task_p = subparsers.add_parser("task", help="Generate benchmark task")
    task_p.add_argument("--db-path", default="/tmp/healthcare_sim.db")
    task_p.add_argument("--archetype", default="referral_preop_coordination")
    task_p.add_argument("--seed", type=int, default=42)
    task_p.add_argument("--out", default="-")

    args = parser.parse_args()

    if args.command == "seed":
        res = create_dynamic_database(args.db_path, seed=args.seed)
        ctx = HealthcareContext(db_path=args.db_path)
        h = ctx.service.calculate_state_hash()
        print(f"Database seeded successfully at {args.db_path}")
        print(f"State Hash: {h}")
        print(f"Record Counts: {res['counts']}")

    elif args.command == "hash":
        ctx = HealthcareContext(db_path=args.db_path)
        print(ctx.service.calculate_state_hash())

    elif args.command == "export":
        ctx = HealthcareContext(db_path=args.db_path)
        data = {
            "state_hash": ctx.service.calculate_state_hash(),
            "audit_log": ctx.service.get_audit_log(limit=200),
        }
        formatted = json.dumps(data, indent=2)
        if args.out == "-":
            print(formatted)
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Exported state to {args.out}")

    elif args.command == "task":
        gen = TaskGenerator(db_path=args.db_path, seed=args.seed)
        task = gen.generate_task(archetype=args.archetype)
        formatted = json.dumps(task, indent=2)
        if args.out == "-":
            print(formatted)
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Task saved to {args.out}")


if __name__ == "__main__":
    main()
