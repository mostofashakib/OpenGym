#!/usr/bin/env bash
set -euo pipefail

# Ensure DB directory exists and is seeded
mkdir -p /var/lib/terminal
if [ ! -f /var/lib/terminal/terminal.db ]; then
  python3 scripts/terminal_bridge.py seed
fi

# Run next server
exec npx next start -p "${PORT:-80}"
