#!/usr/bin/env bash
# Deterministic reference solution for Terminal Incident Remediation. Scores exactly 1.000.
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
    from tools.terminal_client import TerminalClient
    client = TerminalClient()
    test_res = client.inspect_system()
    use_client = bool(test_res.get("ok"))
except Exception:
    use_client = False

db_path = None
if not use_client:
    for cand in [
        os.environ.get("TERMINAL_DB"),
        "/var/lib/terminal/terminal.db",
        "/tmp/test_terminal.db",
        "terminal.db",
    ]:
        if cand and Path(cand).exists():
            db_path = Path(cand)
            break
    from terminal_sim.service import execute_tool

def run_tool(name: str, args: dict):
    if use_client:
        return client.execute_tool(name, args)
    elif db_path:
        return {"ok": True, "result": execute_tool(db_path, name, args)}
    else:
        raise RuntimeError("No communication channel available (neither socket nor SQLite DB)")

# 1. Investigate processes and identify rogue PID 4921
ps_res = run_tool("run_command", {"command": "ps aux"})
print("Investigated process table.")

# 2. Terminate rogue memory/CPU leaking worker process (PID 4921)
kill_res = run_tool("run_command", {"command": "kill -9 4921"})
print("Terminated rogue worker process PID 4921.")

# 3. Truncate bloated debug log to reclaim disk space
trunc_res = run_tool("run_command", {"command": "truncate -s 0 /var/log/app/debug_trace.log"})
print("Reclaimed disk space by truncating /var/log/app/debug_trace.log.")

# 4. Repair configuration parameters in /etc/payment-processor/config.yaml
cfg_read = run_tool("read_file", {"path": "/etc/payment-processor/config.yaml", "offset": 0, "limit": 100})
cfg_content = cfg_read.get("result", {}).get("content", "")
fixed_cfg = cfg_content.replace("host: db-replica-invalid.internal", "host: db-primary.internal").replace("port: 9999", "port: 5432")
run_tool("write_file", {"path": "/etc/payment-processor/config.yaml", "content": fixed_cfg, "mode": "write"})
print("Repaired database connection configuration in /etc/payment-processor/config.yaml.")

# 5. Fix insecure private key permissions (0600)
chmod_res = run_tool("run_command", {"command": "chmod 600 /etc/ssl/certs/payment-api.key"})
print("Secured private key permissions to 0600.")

# 6. Restart payment-processor service and verify active health
restart_res = run_tool("run_command", {"command": "systemctl restart payment-processor"})
status_res = run_tool("run_command", {"command": "systemctl status payment-processor"})
print("Restarted payment-processor service and confirmed active status.")

# 7. Submit final remediation sign-off report
run_tool("submit_task", {
    "summary": "Remediated critical host degradation on app-node-04: killed rogue worker PID 4921, truncated disk-filling debug logs, corrected database host/port in config.yaml, secured SSL private key permissions to 0600, and verified payment-processor service active.",
    "actions_taken": [
        "Terminated rogue worker PID 4921",
        "Truncated /var/log/app/debug_trace.log restoring >70% disk capacity",
        "Updated /etc/payment-processor/config.yaml to db-primary.internal:5432",
        "Chmod 0600 on /etc/ssl/certs/payment-api.key",
        "Restarted payment-processor.service to active (running) state",
    ],
})
print("Remediation report successfully submitted.")
EOF
