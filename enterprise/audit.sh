#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:$SCRIPT_DIR:$SCRIPT_DIR/environment"

echo "========================================================"
echo " Enterprise Compliance & DLP Audit Inspector"
echo "========================================================"

python3 -c "
import json
from pathlib import Path
from enterprise.environment.enterprise_sim.context import EnterpriseContext
from enterprise.tools.enterprise_client import EnterpriseClient
from enterprise.verifiers.policy_verifier import verify_enterprise_policies

ctx = EnterpriseContext.from_env()
ctx.ensure_initialized()
client = EnterpriseClient(db_path=str(ctx.db_path))
logs = client.get_audit_log()
print(f'Total recorded enterprise audit events: {len(logs)}')
policy_check = verify_enterprise_policies(client, customer_id='cust-0001')
if policy_check.passed:
    print('Policy & Compliance Status: PASS (0 policy violations detected)')
else:
    print(f'Policy & Compliance Status: VIOLATIONS DETECTED: {policy_check.details}')
    print(json.dumps(policy_check.evidence, indent=2))
"
