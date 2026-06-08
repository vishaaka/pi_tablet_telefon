#!/usr/bin/env bash
set -euo pipefail

echo "== System =="
date -Is
uname -r
free -h

echo
echo "== Main processes by RSS =="
ps -eo pid,comm,rss,%cpu --sort=-rss |
  grep -E 'PID|waydroid|android|pi-tablet|uvicorn|llama|chromium|gcompris|tuxpaint' |
  head -n 30

echo
echo "== Services =="
systemctl is-active \
  pi-tablet-backend.service \
  pi-tablet-local-ai.service \
  pi-tablet-backend-rust.service \
  waydroid-container.service 2>/dev/null || true

echo
echo "== Rust backend =="
curl -fsS http://127.0.0.1:8090/health 2>/dev/null || true
echo
