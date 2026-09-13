#!/usr/bin/env bash
# Run the enterprise environment task under Harbor or locally.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$WORKSPACE_ROOT/.env"
TASK_PATH="$SCRIPT_DIR"
MODEL="${MODEL:-ollama/qwen3.6:35b}"
JOBS_PATH="$SCRIPT_DIR/jobs/harbor"
JOB_NAME="$(printf '%s' "$MODEL" | tr '/:' '__')__$(date -u +%Y-%m-%d__%H-%M-%S)"

export PYTHONPATH="$WORKSPACE_ROOT:$TASK_PATH:$TASK_PATH/environment${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

echo "Running Enterprise Agent Simulation Environment (Harbor)..."
exec harbor run \
  -p "$TASK_PATH" \
  -m "$MODEL" \
  --n-concurrent 1 \
  --job-name "$JOB_NAME" \
  -o "$JOBS_PATH" \
  "$@"
