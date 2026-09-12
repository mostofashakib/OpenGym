#!/usr/bin/env bash
# Deterministic reference solution for Browser Procurement Audit. Scores exactly 1.000.
set -euo pipefail

if [ -d "/tests" ] || [ -d "/opt/grading" ]; then
  export PYTHONPATH="/opt/grading:/opt/grading/verifiers:/opt/tools:/opt/agent:/opt:${PYTHONPATH:-}"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
  export PYTHONPATH="$ROOT_DIR:$ROOT_DIR/environment:$ROOT_DIR/tools:$ROOT_DIR/agent:$ROOT_DIR/verifiers:$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tools:${PYTHONPATH:+:$PYTHONPATH}"
fi

python3 - <<'EOF'
import json
import os
import sys
from pathlib import Path

# Helper to execute tools via client or direct sqlite fallback
try:
    from tools.browser_client import BrowserClient
    client = BrowserClient()
    test_res = client.get_page()
    use_client = bool(test_res.get("ok"))
except Exception:
    use_client = False

db_path = None
if not use_client:
    for cand in [
        os.environ.get("BROWSER_DB"),
        "/var/lib/browser/browser.db",
        "/tmp/test_browser.db",
        "browser.db",
    ]:
        if cand and Path(cand).exists():
            db_path = Path(cand)
            break
    from browser_sim.service import execute_tool

def run_tool(name: str, args: dict):
    if use_client:
        return client.execute_tool(name, args)
    elif db_path:
        return {"ok": True, "result": execute_tool(db_path, name, args)}
    else:
        raise RuntimeError("No communication channel available (neither socket nor SQLite DB)")

# 1. Navigate to /orders
orders_res = run_tool("navigate", {"url": "https://procure.corp/orders"})
print("Navigated to orders registry.")

# 2. Inspect and reject fraudulent PO-9821 with policy violation reason
run_tool("navigate", {"url": "https://procure.corp/orders/PO-9821"})
run_tool("type_text", {
    "element_id": "input-rejection-reason",
    "text": "POLICY_VIOLATION_UNAUTHORIZED_HARDWARE",
})
reject_res = run_tool("click", {"element_id": "btn-reject-po-9821"})
print("Rejected fraudulent requisition PO-9821.")

# 3. Inspect and approve legitimate infrastructure renewal PO-3410
run_tool("navigate", {"url": "https://procure.corp/orders/PO-3410"})
approve_res = run_tool("click", {"element_id": "btn-approve-po-3410"})
print("Approved legitimate renewal requisition PO-3410.")

# 4. Navigate to /vendors and blacklist shell supplier GhostWire Hardware
run_tool("navigate", {"url": "https://procure.corp/vendors"})
bl_res = run_tool("click", {"element_id": "btn-blacklist-vend-ghostwire"})
print("Blacklisted unverified supplier GhostWire Hardware LLC.")

# 5. Navigate to /compliance and submit SOC-2 recertification for DataSync Corp
run_tool("navigate", {"url": "https://procure.corp/compliance"})
run_tool("type_text", {
    "element_id": "input-cert-code",
    "text": "SOC2-2026-NEXUS-778",
})
submit_comp = run_tool("click", {"element_id": "btn-submit-compliance"})
print("Submitted SOC-2 recertification for DataSync Corp.")

# 6. Submit final audit sign-off report
run_tool("submit_task", {
    "summary": "Completed procurement and compliance audit: rejected unauthorized GPU cluster requisition PO-9821 with reason code POLICY_VIOLATION_UNAUTHORIZED_HARDWARE, approved critical Kubernetes license renewal PO-3410, blacklisted unverified supplier GhostWire Hardware LLC, and renewed DataSync Corp SOC-2 certification under code SOC2-2026-NEXUS-778.",
    "audited_ids": ["PO-9821", "PO-3410", "VEND-GHOSTWIRE", "VEND-DATASYNC"],
})
print("Procurement audit sign-off successfully submitted.")
EOF
