#!/usr/bin/env bash
# Harbor uploads and runs this script as the verifier user.
set -uo pipefail

if [ -d "/tests" ]; then
  TESTS_DIR="/tests"
  LOGS_DIR="${LOGS_DIR:-/logs/verifier}"
  export PYTHONPATH="/opt/grading:/opt/grading/verifiers:/opt/tools:/opt/agent:/opt:/tests:${PYTHONPATH:-}"
  SUITES=(test_mcp_server test_verifiers test_terminal_sim test_rl_env test_end_to_end)
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  TESTS_DIR="$SCRIPT_DIR/tests"
  LOGS_DIR="${LOGS_DIR:-$SCRIPT_DIR/logs/verifier}"
  export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tests:${PYTHONPATH:-}"
  SUITES=(test_agent_adapters test_mcp_server test_verifiers test_terminal_sim test_rl_env test_end_to_end)
fi

PYTHON_BIN="python3"
if [ -x "${SCRIPT_DIR:-}/.venv/bin/python" ]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

mkdir -p "$LOGS_DIR"

# Pre-seed reward.json with valid=0.0
cat << 'EOF' > "$LOGS_DIR/reward.json"
{
  "reward": 0.0,
  "success": 0.0,
  "valid": 0.0
}
EOF

selftest_status=0
for suite in "${SUITES[@]}"; do
  echo "--- Running ${suite} ---"
  if ! "$PYTHON_BIN" "$TESTS_DIR/${suite}.py"; then
    echo "SELF-TEST FAILED: ${suite}" >&2
    selftest_status=1
  fi
done

echo "--- Running Task Outcome Verification ---"
"$PYTHON_BIN" - <<EOF
import json
import os
from pathlib import Path
from verifiers.layered import evaluate_episode
from verifiers.harbor import reward_dict, blank_reward_dict

selftest = int(os.environ.get("SELFTEST_STATUS", "${selftest_status}"))
logs_dir = Path("${LOGS_DIR}")

if selftest != 0:
    reward = blank_reward_dict(valid=0.0)
else:
    eval_res = evaluate_episode()
    reward = reward_dict(eval_res)

out_file = logs_dir / "reward.json"
out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(reward, indent=2))
print("Final Harbor Reward:")
print(json.dumps(reward, indent=2))
EOF

verifier_status=$?

if [ "${selftest_status}" -ne 0 ]; then
  echo "Environment self-tests failed." >&2
  exit 1
fi

exit "${verifier_status}"
