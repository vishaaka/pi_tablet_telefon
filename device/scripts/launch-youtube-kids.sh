#!/usr/bin/env bash
set -euo pipefail

PROFILE_DIR="${PI_YOUTUBE_KIDS_PROFILE:-$HOME/.local/share/pi-tablet/youtube-kids}"
mkdir -p "$PROFILE_DIR"
pkill -f 'chromium.*pi-tablet/youtube-kids' 2>/dev/null || true

exec chromium \
  --app=https://www.youtubekids.com \
  --kiosk \
  --noerrdialogs \
  --disable-infobars \
  --disable-session-crashed-bubble \
  --no-first-run \
  --overscroll-history-navigation=0 \
  --user-data-dir="$PROFILE_DIR"
