#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR:$SCRIPT_DIR/environment"

echo "========================================================"
echo " Workstation Audit Inspector"
echo "========================================================"

python3 -c "
import json
from pathlib import Path
from workstation_sim.context import WorkstationContext
from verifiers.auditor import audit_run

ctx = WorkstationContext.from_env()
ctx.ensure_initialized()
state = ctx.export_state()
logs = state.get('action_logs', [])
print(f'Total recorded actions: {len(logs)}')
penalties = audit_run(logs)
if not penalties:
    print('Audit Status: PASS (0 policy/privacy violations)')
else:
    print(f'Audit Status: VIOLATIONS DETECTED ({len(penalties)} penalties):')
    for p in penalties:
        print(f'  - [{p.source}] -{p.amount}: {p.reason}')
"
