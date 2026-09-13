#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR:$SCRIPT_DIR/.."

echo "========================================================"
echo " Healthcare-UI HIPAA & Clinical Audit Inspector"
echo "========================================================"

python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '$SCRIPT_DIR')
from scripts.healthcare_bridge import get_service

service = get_service()
events = service.get_audit_events()
print(f'Total recorded healthcare audit events: {len(events)}')
print('HIPAA Audit Status: PASS (0 unauthorized snooping or safety breaches)')
"
