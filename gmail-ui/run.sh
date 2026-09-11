#!/usr/bin/env bash
# Run the task under Harbor.
#
# The default agent is this task's own (`agent/`), driving a local Ollama model:
# no account, no key, no per-token cost, and the model call happens on this
# machine rather than inside the environment. Point it somewhere else with one
# variable -- the provider is the head of the model spec:
#
#   ./run.sh                                              # ollama/qwen3.6:35b
#   TASK=urgent-email-triage ./run.sh                    # runs the urgent email triage task
#   MODEL=ollama/gemma4:26b ./run.sh
#   MODEL=openrouter/anthropic/claude-opus-5 ./run.sh     # needs OPEN_ROUTER_KEY
#   MODEL=anthropic/claude-opus-5 ./run.sh                # needs ANTHROPIC_API_KEY
#
# AGENT switches the harness rather than the model:
#
#   AGENT=claude-code MODEL=anthropic/claude-opus-4.7 ./run.sh
#   AGENT=oracle ./run.sh                                 # runs reference oracle
#
# Any further arguments are passed through to `harbor run`.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

TASK_NAME="${TASK:-vendor-renewals-triage}"
TASK_PATH="${TASK_PATH:-$SCRIPT_DIR/tasks/$TASK_NAME}"
AGENT="${AGENT:-agent.harbor_agent:GmailAgent}"
MODEL="${MODEL:-ollama/qwen3.6:35b}"
JOBS_PATH="$SCRIPT_DIR/jobs/harbor"
JOB_NAME="$(printf '%s' "$MODEL" | tr '/:' '__')__$(date -u +%Y-%m-%d__%H-%M-%S)"

CLEANUP=1
HARBOR_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-cleanup)
      CLEANUP=0
      shift
      ;;
    -p|--path)
      TASK_PATH="$2"
      shift 2
      ;;
    *)
      HARBOR_ARGS+=("$1")
      shift
      ;;
  esac
done

if [ "$CLEANUP" -eq 1 ]; then
  "$SCRIPT_DIR/kill.sh"
fi

export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

case "$MODEL" in
  ollama/*|ollama) NEEDS_KEY="" ;;
  openrouter/*)    NEEDS_KEY="OPEN_ROUTER_KEY" ;;
  anthropic/*)     NEEDS_KEY="ANTHROPIC_API_KEY" ;;
  *)               NEEDS_KEY="" ;;
esac

if [[ "$AGENT" == "claude-code" ]]; then
  NEEDS_KEY="OPEN_ROUTER_KEY"
fi

if [[ -n "$NEEDS_KEY" && -z "${!NEEDS_KEY:-}" ]]; then
  echo "$MODEL needs $NEEDS_KEY, which is missing or empty in $ENV_FILE" >&2
  echo "Run the default local model instead with: $(basename "$0")" >&2
  exit 1
fi

AGENT_ARGS=()
if [[ "$AGENT" == "claude-code" ]]; then
  export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
  export ANTHROPIC_API_KEY="$OPEN_ROUTER_KEY"
  unset ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN
  unset OPEN_ROUTER_KEY OPENROUTER_API_KEY
  AGENT_ARGS=(--ak reasoning_effort=high --ak max_turns=80 --ak max_budget_usd=25)
fi

exec harbor run \
  -p "$TASK_PATH" \
  -a "$AGENT" \
  -m "$MODEL" \
  ${AGENT_ARGS[@]+"${AGENT_ARGS[@]}"} \
  --n-concurrent 1 \
  --job-name "$JOB_NAME" \
  -o "$JOBS_PATH" \
  ${HARBOR_ARGS[@]+"${HARBOR_ARGS[@]}"}
