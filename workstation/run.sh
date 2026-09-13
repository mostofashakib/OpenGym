#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

AGENT="${AGENT:-oracle}"
MODEL="${MODEL:-ollama/qwen3.6:35b}"

export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/environment${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ "$AGENT" == "oracle" ]]; then
  echo "Running deterministic reference oracle..."
  python3 "$SCRIPT_DIR/solution/oracle.py"
  exit 0
fi

if command -v harbor >/dev/null 2>&1; then
  echo "Running under Harbor with agent: $AGENT, model: $MODEL"
  harbor run -p "$SCRIPT_DIR" -a "$AGENT" -m "$MODEL" "$@"
else
  echo "Harbor is not installed. Running oracle self-verification directly:"
  python3 "$SCRIPT_DIR/solution/oracle.py"
fi
