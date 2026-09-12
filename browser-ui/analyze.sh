#!/usr/bin/env bash
# Analyze trial outcomes and event traces for browser environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tools:${PYTHONPATH:-}"

python3 - <<'EOF'
import json
import os
import sys
from pathlib import Path

for cand in ["/var/lib/browser/state-export.json", "/tmp/state-export.json", "state-export.json"]:
    p = Path(cand)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        print(f"Loaded state from {p}")
        print("Orders count:", len(data.get("orders", [])))
        print("Vendors count:", len(data.get("vendors", [])))
        print("Compliance filings count:", len(data.get("compliance_filings", [])))
        print("Action log count:", len(data.get("action_log", [])))
        print("Event traces count:", len(data.get("event_traces", [])))
        sys.exit(0)

print("No state export found to analyze.")
EOF
