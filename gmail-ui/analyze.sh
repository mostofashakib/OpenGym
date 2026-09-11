#!/usr/bin/env bash
# Analyze trial results under jobs/harbor.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<'EOF'
import json
import sys
from pathlib import Path

jobs_dir = Path("jobs/harbor")
if not jobs_dir.exists():
    print("No jobs found in jobs/harbor.")
    sys.exit(0)

results = list(jobs_dir.glob("**/result.json"))
print(f"Found {len(results)} trial results:")
for r in results:
    try:
        data = json.loads(r.read_text())
        print(f"- {r.parent.name}: reward={data.get('reward')} success={data.get('success')}")
    except Exception as e:
        print(f"- {r.parent.name}: error reading result ({e})")
EOF
