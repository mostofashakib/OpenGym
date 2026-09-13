"""Harbor benchmark verifier entrypoint for the Software Environment.

Accepts task specification JSON, executes layered evaluation, and prints
standardized JSON evaluation results.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .layered import LayeredVerifier
from software.tools.software_client import SoftwareClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Software Environment Harbor Verifier")
    parser.add_argument("--task-file", required=True, help="Path to task JSON file")
    parser.add_argument("--db-path", default="/tmp/software_sim.db", help="Path to SQLite database")
    parser.add_argument("--spec-path", default=None, help="Path to AppSpec JSON file")
    parser.add_argument("--out", default="-", help="Output file or - for stdout")

    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = SoftwareClient(db_path=args.db_path, app_spec_path=args.spec_path)
    verifier = LayeredVerifier(client)
    result = verifier.verify(task_spec)

    output_data = result.to_dict()
    formatted = json.dumps(output_data, indent=2)

    if args.out == "-":
        print(formatted)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(formatted)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
