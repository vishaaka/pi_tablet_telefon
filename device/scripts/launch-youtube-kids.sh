#!/usr/bin/env bash
set -euo pipefail

PROFILE_DIR="${PI_YOUTUBE_KIDS_PROFILE:-$HOME/.local/share/pi-tablet/youtube-kids}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"
mkdir -p "$PROFILE_DIR"
pkill -f 'chromium.*pi-tablet/youtube-kids' 2>/dev/null || true

exec chromium \
  --ozone-platform=wayland \
  --app=https://www.youtubekids.com \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --no-first-run \
  --overscroll-history-navigation=0 \
  --user-data-dir="$PROFILE_DIR"
