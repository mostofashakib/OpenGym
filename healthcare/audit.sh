#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR:$SCRIPT_DIR/environment"

echo "========================================================"
echo " Healthcare HIPAA & Clinical Safety Audit Inspector"
echo "========================================================"

python3 -c "
import json
from pathlib import Path
from healthcare.environment.healthcare_sim.context import HealthcareContext

ctx = HealthcareContext.from_env()
ctx.ensure_initialized()
logs = ctx.service.get_audit_log(limit=50)
print(f'Total recorded HIPAA audit events: {len(logs)}')
if not logs:
    print('Audit Status: Clean / No interactions logged')
else:
    print('Recent clinical access & modification events:')
    for entry in logs[:10]:
        print(f'  - [{entry.get(\"timestamp\", \"N/A\")}] {entry.get(\"actor_id\", \"unknown\")} ({entry.get(\"actor_role\", \"\")}): {entry.get(\"action\", \"\")} on Patient:{entry.get(\"patient_id\", \"\")} -> Status: {entry.get(\"status\", \"\")}')
"
