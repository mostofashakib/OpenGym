"""Admin CLI for Software Environment management.

Supports procedural application generation, seeding, state hashing, and task generation.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .context import SoftwareContext
from .db_generator import DatabaseGenerator
from .domains import get_domain_spec
from .generalization import GeneralizationSplit, apply_generalization_split
from .task_generator import TaskGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Software Environment CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # seed command
    seed_p = subparsers.add_parser("seed", help="Generate application schema and seed database")
    seed_p.add_argument("--db-path", default="/tmp/software_sim.db", help="Path to SQLite database")
    seed_p.add_argument("--domain", default="logistics", help="Domain template name")
    seed_p.add_argument("--split", default="iid", choices=["iid", "new_ui", "new_vocab", "new_workflow", "ood"])
    seed_p.add_argument("--seed", type=int, default=42, help="Random seed")
    seed_p.add_argument("--records-per-entity", type=int, default=25, help="Number of records per entity")
    seed_p.add_argument("--spec-out", default="/tmp/app_spec.json", help="Path to save generated AppSpec")

    # hash command
    hash_p = subparsers.add_parser("hash", help="Compute SHA-256 hash of database state")
    hash_p.add_argument("--db-path", default="/tmp/software_sim.db")

    # export command
    export_p = subparsers.add_parser("export", help="Export database state as JSON")
    export_p.add_argument("--db-path", default="/tmp/software_sim.db")
    export_p.add_argument("--out", default="-", help="Output JSON file or - for stdout")

    # task command
    task_p = subparsers.add_parser("task", help="Generate a synthetic task from the database")
    task_p.add_argument("--db-path", default="/tmp/software_sim.db")
    task_p.add_argument("--spec-path", default="/tmp/app_spec.json")
    task_p.add_argument("--seed", type=int, default=42)
    task_p.add_argument("--out", default="-", help="Output task JSON file or - for stdout")

    args = parser.parse_args()

    if args.command == "seed":
        split = GeneralizationSplit(args.split)
        base_spec = get_domain_spec(args.domain)
        spec = apply_generalization_split(base_spec, split=split, seed=args.seed)

        # Save spec
        with open(args.spec_out, "w", encoding="utf-8") as f:
            f.write(spec.model_dump_json(indent=2))

        # Generate database
        gen = DatabaseGenerator(spec, seed=args.seed)
        state_hash = gen.populate_database(args.db_path, records_per_entity=args.records_per_entity)
        print(f"Database generated successfully at {args.db_path}")
        print(f"App Spec saved to {args.spec_out}")
        print(f"Initial State Hash: {state_hash}")

    elif args.command == "hash":
        ctx = SoftwareContext(db_path=args.db_path)
        print(ctx.service.calculate_state_hash())

    elif args.command == "export":
        ctx = SoftwareContext(db_path=args.db_path)
        state = ctx.service.export_state()
        formatted = json.dumps(state, indent=2)
        if args.out == "-":
            print(formatted)
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Exported state to {args.out}")

    elif args.command == "task":
        ctx = SoftwareContext(db_path=args.db_path, app_spec_path=args.spec_path)
        spec = ctx.app_spec or get_domain_spec("logistics")
        task_gen = TaskGenerator(app_spec=spec, db_path=args.db_path, seed=args.seed)
        task = task_gen.generate_task()
        formatted = json.dumps(task, indent=2)
        if args.out == "-":
            print(formatted)
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Generated task saved to {args.out}")


if __name__ == "__main__":
    main()
