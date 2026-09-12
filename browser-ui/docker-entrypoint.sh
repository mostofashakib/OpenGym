#!/usr/bin/env bash
set -euo pipefail

# Ensure DB directory exists and is seeded
mkdir -p /var/lib/browser
if [ ! -f /var/lib/browser/browser.db ]; then
  python3 scripts/browser_bridge.py seed
fi

# Run next server
exec npx next start -p "${PORT:-80}"
