#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR:$SCRIPT_DIR/environment"

echo "========================================================"
echo " Software Simulation Audit Inspector"
echo "========================================================"

python3 -c "
import json
from pathlib import Path
from software.environment.software_sim.context import SoftwareContext

ctx = SoftwareContext.from_env()
ctx.ensure_initialized()
logs = ctx.service.get_audit_log(limit=50)
print(f'Total recorded audit log entries: {len(logs)}')
if not logs:
    print('Audit Status: Clean / Untouched')
else:
    print('Recent transitions and actions:')
    for entry in logs[:10]:
        print(f'  - [{entry.get(\"timestamp\", \"N/A\")}] {entry.get(\"actor\", \"unknown\")}: {entry.get(\"action\", \"\")} on {entry.get(\"entity_name\", \"\")}:{entry.get(\"entity_id\", \"\")}')
"
