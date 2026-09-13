#!/usr/bin/env bash
PORT=3005
URL="http://localhost:${PORT}"
echo "Opening Apex Enterprise Cloud UI in default browser: ${URL}"
open "${URL}" 2>/dev/null || xdg-open "${URL}" 2>/dev/null || echo "Please navigate to ${URL}"
