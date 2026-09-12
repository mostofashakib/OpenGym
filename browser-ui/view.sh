#!/usr/bin/env bash
# Start the Harbor viewer for Browser trial jobs.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
JOBS_PATH="$SCRIPT_DIR/jobs/harbor"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  if [[ -n "${OPEN_ROUTER_KEY:-}" ]]; then
    export ANTHROPIC_BASE_URL="https://openrouter.ai/api"
    export ANTHROPIC_API_KEY="$OPEN_ROUTER_KEY"
    unset ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN
    unset OPEN_ROUTER_KEY OPENROUTER_API_KEY
  fi
fi

exec harbor view "$JOBS_PATH" "$@"
