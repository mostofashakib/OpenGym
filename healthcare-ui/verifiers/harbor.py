"""Harbor evaluation entrypoint for the Healthcare Environment."""

from __future__ import annotations

import argparse
import json
import sys

from .layered import LayeredVerifier
from healthcare.tools.healthcare_client import HealthcareClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Healthcare Environment Harbor Verifier")
    parser.add_argument("--task-file", required=True, help="Path to task JSON")
    parser.add_argument("--db-path", default="/tmp/healthcare_sim.db", help="Path to SQLite database")
    parser.add_argument("--out", default="-", help="Output destination")

    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = HealthcareClient(db_path=args.db_path)
    verifier = LayeredVerifier(client)
    res = verifier.verify(task_spec)

    output = json.dumps(res.to_dict(), indent=2)
    if args.out == "-":
        print(output)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)

    sys.exit(0 if res.success else 1)


if __name__ == "__main__":
    main()
