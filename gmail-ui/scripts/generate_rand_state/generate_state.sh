#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/generate_state.py"

SEED="gmail"
THREADS=8
SINGLES=12
MAX_PER_THREAD=4
BASE_URL="http://localhost:3000"
API_PATH="/api/state"
OUTPUT=""
DRY_RUN=0
VERBOSE=0

usage() {
  cat <<USAGE
Usage: $(basename "$0") [options]

Options:
  --seed SEED                  Seed for deterministic generation (default: gmail)
  --threads N                  Number of threaded conversations (default: 8)
  --singles N                  Number of standalone messages (default: 12)
  --maxMessagesPerThread N     Max messages per thread (default: 4)
  --url URL                    Base URL to post to (default: http://localhost:3000)
  --path PATH                  API path (default: /api/state)
  --output FILE                Also write generated JSON to FILE
  --dry-run                    Generate only; do not POST
  --verbose                    Verbose logging
  -h, --help                   Show this help

Examples:
  $(basename "$0") --seed myseed --threads 10 --singles 25 --maxMessagesPerThread 5
  $(basename "$0") --url http://localhost:3001 --output state.json
USAGE
}

log() { if [[ "$VERBOSE" -eq 1 ]]; then echo "[seed] $*"; fi }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --seed) SEED="$2"; shift 2;;
    --threads) THREADS="$2"; shift 2;;
    --singles) SINGLES="$2"; shift 2;;
    --maxMessagesPerThread) MAX_PER_THREAD="$2"; shift 2;;
    --url) BASE_URL="$2"; shift 2;;
    --path) API_PATH="$2"; shift 2;;
    --output) OUTPUT="$2"; shift 2;;
    --dry-run) DRY_RUN=1; shift;;
    --verbose) VERBOSE=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown option: $1" >&2; usage; exit 1;;
  esac
done

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

GEN_ARGS=(
  --seed "$SEED"
  --threads "$THREADS"
  --singles "$SINGLES"
  --maxMessagesPerThread "$MAX_PER_THREAD"
)

log "Generating with: seed=$SEED threads=$THREADS singles=$SINGLES max=$MAX_PER_THREAD"

if [[ "$DRY_RUN" -eq 1 ]]; then
  if [[ -n "$OUTPUT" ]]; then
    python3 "$PY_SCRIPT" "${GEN_ARGS[@]}" -o "$OUTPUT"
    log "Wrote $OUTPUT (dry run, no POST)"
  else
    python3 "$PY_SCRIPT" "${GEN_ARGS[@]}"
  fi
  exit 0
fi

POST_URL="${BASE_URL%/}${API_PATH}"
log "Posting to: $POST_URL"

if [[ -n "$OUTPUT" ]]; then
  python3 "$PY_SCRIPT" "${GEN_ARGS[@]}" | tee "$OUTPUT" | \
    curl -sS -X POST "$POST_URL" -H 'content-type: application/json' -H 'Authorization: Basic YWdlbnQ6d2UtbG92ZS1jdWEh' -d @-
  log "Also wrote $OUTPUT"
else
  python3 "$PY_SCRIPT" "${GEN_ARGS[@]}" | \
    curl -sS -X POST "$POST_URL" -H 'content-type: application/json' -H 'Authorization: Basic YWdlbnQ6d2UtbG92ZS1jdWEh' -d @-
fi

echo
log "Done"


