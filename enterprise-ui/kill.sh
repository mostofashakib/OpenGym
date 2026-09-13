#!/usr/bin/env bash
PORT=3005
echo "Stopping Apex Enterprise Cloud UI on port ${PORT}..."
PIDS=$(lsof -ti :${PORT} 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  kill -9 $PIDS
  echo "Terminated PID(s): $PIDS"
else
  echo "No process running on port ${PORT}."
fi
