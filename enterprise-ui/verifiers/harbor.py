"""Harbor evaluation CLI entrypoint for the Enterprise Environment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .layered import LayeredVerifier
from enterprise.tools.enterprise_client import EnterpriseClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise Environment Harbor Verifier")
    parser.add_argument("--task-file", required=True, help="Path to task JSON")
    parser.add_argument("--db-path", default="/var/lib/enterprise/company.db", help="Path to SQLite database")
    parser.add_argument("--out", required=False, help="Output destination")
    args = parser.parse_args()

    with open(args.task_file, "r", encoding="utf-8") as f:
        task_spec = json.load(f)

    client = EnterpriseClient(db_path=args.db_path)
    verifier = LayeredVerifier(client)
    res = verifier.verify(task_spec)

    output_data = res.to_dict()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
    else:
        print(json.dumps(output_data, indent=2))

    sys.exit(0 if res.success else 1)


if __name__ == "__main__":
    main()
