#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
PKG="com.vishaaka.pitablettelefon"
APK_PATH="$REPO_DIR/device/artifacts/pi-telefon-debug.apk"
LOG_FILE="${PI_TABLET_AUTOSTART_LOG:-$HOME/pi-tablet-phone-autostart.log}"
USER_ID="$(id -u)"

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$USER_ID}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export DISPLAY="${DISPLAY:-:0}"

mkdir -p "$(dirname "$LOG_FILE")"
exec >>"$LOG_FILE" 2>&1

echo
echo "== $(date -Is) pi-tablet phone autostart =="
echo "repo=$REPO_DIR"
echo "runtime=$XDG_RUNTIME_DIR wayland=$WAYLAND_DISPLAY"

wait_for_file() {
  local path="$1"
  local label="$2"
  local tries="${3:-90}"
  for _ in $(seq 1 "$tries"); do
    if [ -e "$path" ]; then
      echo "$label ready: $path"
      return 0
    fi
    sleep 1
  done
  echo "$label not ready: $path"
  return 1
}

wait_for_backend() {
  for _ in $(seq 1 90); do
    if curl -fsS http://127.0.0.1:8080/health >/dev/null 2>&1; then
      echo "backend ready"
      return 0
    fi
    sleep 1
  done
  echo "backend not ready"
  return 1
}

start_waydroid_session() {
  if waydroid status 2>/dev/null | grep -q "Session:[[:space:]]*RUNNING"; then
    echo "waydroid session already running"
    return 0
  fi
  echo "starting waydroid session"
  nohup waydroid session start >/tmp/pi-tablet-waydroid-session.log 2>&1 &
  sleep 4
}

wait_for_waydroid() {
  for _ in $(seq 1 90); do
    if waydroid status 2>/dev/null | grep -Eq "Container:[[:space:]]*(RUNNING|FROZEN)"; then
      waydroid status || true
      return 0
    fi
    sleep 1
  done
  echo "waydroid container not ready"
  return 1
}

wait_for_android() {
  for _ in $(seq 1 120); do
    if [ "$(sudo -n waydroid shell -- getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] &&
      sudo -n waydroid shell -- dumpsys package android >/dev/null 2>&1; then
      echo "android ready"
      return 0
    fi
    sleep 1
  done
  echo "android not ready"
  return 1
}

ensure_apk_installed() {
  if sudo -n waydroid shell -- dumpsys package "$PKG" 2>/dev/null | grep -q "versionCode"; then
    echo "$PKG installed"
    return 0
  fi
  if [ ! -f "$APK_PATH" ]; then
    echo "APK not found: $APK_PATH"
    return 1
  fi
  echo "installing $APK_PATH"
  waydroid app install "$APK_PATH"
}

launch_phone() {
  for _ in $(seq 1 30); do
    if waydroid app launch "$PKG"; then
      echo "$PKG launched"
      return 0
    fi
    sleep 2
  done
  echo "could not launch $PKG"
  return 1
}

wait_for_file "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" "wayland socket" 120
wait_for_backend

wpctl set-mute @DEFAULT_AUDIO_SINK@ 0 || true
wpctl set-volume @DEFAULT_AUDIO_SINK@ "${PI_TABLET_VOLUME:-1.50}" || true
wpctl get-volume @DEFAULT_AUDIO_SINK@ || true

start_waydroid_session
wait_for_waydroid
wait_for_android
ensure_apk_installed

echo "launching $PKG"
launch_phone
echo "autostart complete"
