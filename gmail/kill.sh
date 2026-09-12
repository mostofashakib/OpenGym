#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TASK_SLUG="$(basename "$SCRIPT_DIR" | tr '[:upper:]' '[:lower:]')"
VIEWER_PORTS="8080-8089"

process_belongs_to_repo() {
  local pid="$1" cwd cmd
  [ "$pid" = "$$" ] && return 1
  [ "$pid" = "$PPID" ] && return 1

  cmd="$(ps -o command= -p "$pid" 2>/dev/null || true)"
  cwd="$(lsof -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | head -1)"

  case "$cwd" in
    "$REPO_ROOT"|"$REPO_ROOT"/*) return 0 ;;
  esac
  printf '%s' "$cmd" | grep -qF -- "$REPO_ROOT"
}

repo_processes() {
  local pid candidates
  candidates="$({
    pgrep -f '(^|/)harbor( |$)|/bin/harbor|harbor\.viewer' 2>/dev/null || true
    lsof -nP -t -iTCP:"$VIEWER_PORTS" -sTCP:LISTEN 2>/dev/null || true
  } | sort -un)"

  for pid in $candidates; do
    if process_belongs_to_repo "$pid"; then
      echo "$pid"
    fi
  done
}

compose_projects() {
  docker compose ls -a --format json 2>/dev/null \
    | python3 -c '
import json, sys
slug = sys.argv[1]
try:
    rows = json.load(sys.stdin)
except Exception:
    rows = []
for row in rows:
    name = row.get("Name") or ""
    if name.startswith(slug) or "vendor-renewals-triage" in name or "gmail" in name:
        print(name)
' "$TASK_SLUG" 2>/dev/null || true
}

terminate_processes() {
  local pids pid
  pids="$(repo_processes || true)"
  if [ -z "${pids//[[:space:]]/}" ]; then
    echo "No matching processes running."
    return 0
  fi

  echo "Terminating processes:"
  for pid in $pids; do
    ps -o pid=,command= -p "$pid" 2>/dev/null || true
  done

  kill $pids 2>/dev/null || true
  sleep 1

  pids="$(repo_processes || true)"
  if [ -n "${pids//[[:space:]]/}" ]; then
    echo "Force killing remaining:"
    kill -9 $pids 2>/dev/null || true
  fi
}

terminate_containers() {
  local projects project strays
  if ! docker info >/dev/null 2>&1; then
    echo "Docker is not responding; skipping container cleanup." >&2
    return
  fi

  projects="$(compose_projects)"
  if [ -n "${projects//[[:space:]]/}" ]; then
    echo "Removing Compose projects for $TASK_SLUG:"
    for project in $projects; do
      echo "  $project"
      docker compose -p "$project" down -v --remove-orphans --timeout 10 >/dev/null 2>&1 || true
    done
  fi

  strays="$(docker ps -aq --filter "name=${TASK_SLUG}" 2>/dev/null || true)"
  if [ -n "${strays//[[:space:]]/}" ]; then
    echo "Removing stray $TASK_SLUG containers."
    # shellcheck disable=SC2086
    docker rm -f $strays >/dev/null 2>&1 || true
  fi
}

terminate_processes
terminate_containers
echo "Cleanup complete. Harbor viewer ports 8080-8089 are reusable."
