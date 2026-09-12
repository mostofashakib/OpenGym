#!/usr/bin/env bash
# Harbor uploads this directory to /tests and runs this script as the verifier
# user (root). The workspace lives in the `slack` service; nothing here opens a
# database directly.
#
# Deliberately not `set -e`: a failing environment self-test must still produce
# a reward file. A missing reward file reaches Harbor as RewardFileNotFoundError,
# which says nothing about what went wrong; `valid=0` in the reward stream says
# the environment was broken and the episode should not be read as evidence
# about the agent.
set -uo pipefail

# /opt/grading holds the full simulator and the verifier package, readable only
# by root; /opt holds the agent's client-only package. Order matters: the
# verifier needs the full one.
if [ -d "/tests" ]; then
  export PYTHONPATH="/opt/grading:/opt:/tests"
  TESTS_DIR="/tests"
  LOGS_DIR="/logs/verifier"
else
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  TESTS_DIR="$SCRIPT_DIR/tests"
  LOGS_DIR="${LOGS_DIR:-$SCRIPT_DIR/logs/verifier}"
  export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment:$SCRIPT_DIR/tools:$SCRIPT_DIR/agent:$SCRIPT_DIR/verifiers:$TESTS_DIR:${PYTHONPATH:-}"
fi

PYTHON_BIN="python3"
if [ -x "${SCRIPT_DIR:-}/.venv/bin/python" ]; then
  PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

mkdir -p "$LOGS_DIR"
export TASK_REWARD_DIR="$LOGS_DIR"

selftest_status=0
for suite in test_virtual_clock test_scenario_engine test_slack_surface test_mcp_server test_event_activation test_trigger_fairness test_verifiers test_harbor_reward test_reward_validation test_reward_matrix test_integrity_violations test_migration_fixture test_migration_reward test_tool_contract test_rl_contract test_agent_adapters test_environment_contract test_slack_bridge; do
  echo "--- ${suite} ---"
  if ! "$PYTHON_BIN" "${TESTS_DIR}/${suite}.py"; then
    echo "SELF-TEST FAILED: ${suite}" >&2
    selftest_status=1
  fi
done

# The graded outcome always runs, and always writes a reward.
export TASK_SELFTEST_STATUS="${selftest_status}"
"$PYTHON_BIN" "${TESTS_DIR}/test_migration_readiness.py"
verifier_status=$?

if [ "${selftest_status}" -ne 0 ]; then
  echo "Environment self-tests failed; reward reports valid=0." >&2
fi
exit "${verifier_status}"
