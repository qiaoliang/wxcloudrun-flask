#!/usr/bin/env bash
set -euo pipefail
ports=(80 8080 90 9090 8888 9999)
for p in "${ports[@]}"; do
  pids=$(lsof -ti tcp:"$p" -sTCP:LISTEN 2>/dev/null || true)
  if [ -n "$pids" ]; then
    kill -9 $pids 2>/dev/null || sudo kill -9 $pids
  fi
done
