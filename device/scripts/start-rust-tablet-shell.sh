#!/usr/bin/env bash
set -euo pipefail

rm -f /tmp/pi-tablet-exit-to-desktop
pkill -f 'chromium.*pi-tablet/youtube-kids' 2>/dev/null || true

if pgrep -f '/opt/pi-tablet-rust/bin/pi-tablet-shell' >/dev/null; then
  exit 0
fi

nohup /opt/pi-tablet-rust/bin/run-rust-tablet-shell \
  >"$HOME/pi-tablet-rust-shell.log" 2>&1 &
