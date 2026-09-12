#!/usr/bin/env bash
set -euo pipefail

# Ensure DB directory exists and is seeded
mkdir -p /var/lib/slack
if [ ! -f /var/lib/slack/slack.db ]; then
  python3 scripts/slack_bridge.py seed
fi

# Run next server
exec npx next start -p "${PORT:-80}"
