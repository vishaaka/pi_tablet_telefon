#!/usr/bin/env bash
set -euo pipefail

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"
export SLINT_FULLSCREEN=1
export SLINT_BACKEND="${SLINT_BACKEND:-winit-femtovg}"

wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 2>/dev/null || true
wpctl set-volume @DEFAULT_AUDIO_SINK@ 1.50 2>/dev/null || true

while true; do
  /opt/pi-tablet-rust/bin/pi-tablet-shell
  sleep 2
done
