#!/usr/bin/env bash
set -euo pipefail

open "http://localhost:3007" 2>/dev/null || xdg-open "http://localhost:3007" 2>/dev/null || echo "Open http://localhost:3007 in your browser"
