#!/usr/bin/env bash
set -euo pipefail

# Ensure DB directory exists and is seeded
mkdir -p /var/lib/tasks
if [ ! -f /var/lib/tasks/tasks.db ]; then
  python3 scripts/task_bridge.py seed
fi

# Run next server
exec npx next start -p "${PORT:-80}"
