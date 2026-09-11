#!/bin/sh
set -e

# Defaults
PORT="${PORT:-80}"
SEED_ON_STARTUP="${SEED_ON_STARTUP:-false}"
SEED_SEED="${SEED_SEED:-gmail}"
SEED_THREADS="${SEED_THREADS:-8}"
SEED_SINGLES="${SEED_SINGLES:-12}"
SEED_MAX_MESSAGES_PER_THREAD="${SEED_MAX_MESSAGES_PER_THREAD:-4}"
SEED_API_PATH="${SEED_API_PATH:-/api/state}"
SEED_BASE_URL="${SEED_BASE_URL:-http://127.0.0.1:${PORT}}"

echo "Generating randomization JSON"
node ./scripts/generate_randomization.js || echo "Randomization generation failed (continuing)"

# Expose generated randomization via static assets if present
if [ -f ./generated/randomization.json ]; then
  mkdir -p ./public/generated
  cp -f ./generated/randomization.json ./public/generated/randomization.json || true
  echo "Copied generated/randomization.json -> public/generated/randomization.json"
fi

echo "Starting Next.js on port ${PORT}"
npm start -- -p "${PORT}" &
APP_PID=$!

# Wait for server to be ready (up to ~30s)
ATTEMPTS=0
until curl -sf "${SEED_BASE_URL}" >/dev/null 2>&1 || [ $ATTEMPTS -ge 60 ]; do
  ATTEMPTS=$((ATTEMPTS+1))
  sleep 0.5
done

if [ "$SEED_ON_STARTUP" = "true" ] || [ "$SEED_ON_STARTUP" = "1" ] || [ "$SEED_ON_STARTUP" = "yes" ]; then
  echo "Seeding data via scripts/generate_rand_state/generate_state.sh -> ${SEED_BASE_URL}${SEED_API_PATH}"
  bash ./scripts/generate_rand_state/generate_state.sh \
    --seed "${SEED_SEED}" \
    --threads "${SEED_THREADS}" \
    --singles "${SEED_SINGLES}" \
    --maxMessagesPerThread "${SEED_MAX_MESSAGES_PER_THREAD}" \
    --url "${SEED_BASE_URL}" \
    --path "${SEED_API_PATH}" || echo "Seeding failed (continuing)"
fi

wait ${APP_PID}

 