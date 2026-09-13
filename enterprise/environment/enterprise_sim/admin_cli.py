"""Administrative CLI for the Enterprise Simulation Platform."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict

from .db_generator import calculate_database_hash, create_enterprise_database
from .task_generator import TaskGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Environment Admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Seed
    p_seed = subparsers.add_parser("seed", help="Seed digital twin database")
    p_seed.add_argument("--db-path", default="/var/lib/enterprise/company.db")
    p_seed.add_argument("--seed", type=int, default=42)

    # Hash
    p_hash = subparsers.add_parser("hash", help="Compute SHA-256 state hash")
    p_hash.add_argument("--db-path", default="/var/lib/enterprise/company.db")

    # Export
    p_exp = subparsers.add_parser("export", help="Export organization state as JSON")
    p_exp.add_argument("--db-path", default="/var/lib/enterprise/company.db")
    p_exp.add_argument("--out", default="/var/lib/enterprise/state-export.json")

    # Task
    p_task = subparsers.add_parser("task", help="Generate benchmark task specification")
    p_task.add_argument("--db-path", default="/var/lib/enterprise/company.db")
    p_task.add_argument("--archetype", default="customer_sla_refund_dispute")
    p_task.add_argument("--out", required=False)

    args = parser.parse_args()

    if args.command == "seed":
        res = create_enterprise_database(args.db_path, seed=args.seed)
        h = calculate_database_hash(args.db_path)
        print(f"Enterprise database seeded successfully: {args.db_path}")
        print(f"Canonical state hash: {h}")
        print(f"Summary counts: {res['counts']}")

    elif args.command == "hash":
        h = calculate_database_hash(args.db_path)
        print(h)

    elif args.command == "export":
        conn = sqlite3.connect(args.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [r[0] for r in cursor.fetchall()]
            data: Dict[str, Any] = {"hash": calculate_database_hash(args.db_path)}
            for tbl in tables:
                rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
                data[tbl] = [dict(r) for r in rows]

            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"State exported to {args.out}")
        finally:
            conn.close()

    elif args.command == "task":
        gen = TaskGenerator(args.db_path)
        task_spec = gen.generate_task(archetype=args.archetype)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(task_spec, f, indent=2)
            print(f"Task written to {args.out}")
        else:
            print(json.dumps(task_spec, indent=2))


if __name__ == "__main__":
    main()
