#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKUP_ROOT="${PI_TABLET_BACKUP_ROOT:-/mnt/pi-backup}"
LATEST_FILE="$BACKUP_ROOT/LATEST"
INSTALL_DIR="/opt/pi-tablet-rust"
SERVICE_FILE="/etc/systemd/system/pi-tablet-backend-rust.service"
USER_NAME="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
LABWC_AUTOSTART="$USER_HOME/.config/labwc/autostart"
ROLLBACK_DIR="$USER_HOME/.local/share/pi-tablet-rust-rollback"

if [ ! -f "$LATEST_FILE" ]; then
  echo "A verified USB backup is required before Rust migration: $LATEST_FILE"
  exit 1
fi
BACKUP_DIR="$(cat "$LATEST_FILE")"
if [ ! -f "$BACKUP_DIR/SHA256SUMS" ]; then
  echo "Backup checksums are missing: $BACKUP_DIR/SHA256SUMS"
  exit 1
fi
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)

sudo apt update
sudo apt install -y \
  cargo rustc build-essential pkg-config \
  libfontconfig1-dev libwayland-dev libxkbcommon-dev libudev-dev libinput-dev libgl1-mesa-dev \
  chromium gcompris-qt tuxpaint ffmpeg curl

cd "$REPO_DIR/rust-tablet"
CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-1}" cargo build --release

sudo mkdir -p "$INSTALL_DIR/bin" /var/lib/pi-tablet-rust/audio
sudo install -m 0755 target/release/pi-tablet-shell "$INSTALL_DIR/bin/pi-tablet-shell"
sudo install -m 0755 target/release/pi-tablet-backend-rs "$INSTALL_DIR/bin/pi-tablet-backend-rs"
sudo chown -R "$USER_NAME:$USER_NAME" /var/lib/pi-tablet-rust

sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=Pi Tablet Rust backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
Environment=HOME=$USER_HOME
Environment=PI_TABLET_AUDIO_DIR=/var/lib/pi-tablet-rust/audio
Environment=PI_EDGE_TTS_COMMAND=$REPO_DIR/backend/.venv/bin/edge-tts
ExecStart=$INSTALL_DIR/bin/pi-tablet-backend-rs
Restart=always
RestartSec=2
MemoryMax=160M

[Install]
WantedBy=multi-user.target
SERVICE

mkdir -p "$ROLLBACK_DIR" "$(dirname "$LABWC_AUTOSTART")"
if [ -f "$LABWC_AUTOSTART" ] && [ ! -f "$ROLLBACK_DIR/labwc-autostart.before-rust" ]; then
  cp "$LABWC_AUTOSTART" "$ROLLBACK_DIR/labwc-autostart.before-rust"
fi
grep -v 'run-rust-tablet-shell.sh' "$LABWC_AUTOSTART" 2>/dev/null >"$LABWC_AUTOSTART.tmp" || true
mv "$LABWC_AUTOSTART.tmp" "$LABWC_AUTOSTART"
echo "$REPO_DIR/device/scripts/run-rust-tablet-shell.sh >>$USER_HOME/pi-tablet-rust-shell.log 2>&1 &" >>"$LABWC_AUTOSTART"

sudo systemctl disable --now pi-tablet-phone-autostart.service 2>/dev/null || true
sudo systemctl disable --now waydroid-container.service 2>/dev/null || true
waydroid session stop 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable --now pi-tablet-backend-rust.service

echo "Rust tablet installed."
echo "Backend: http://127.0.0.1:8090/health"
echo "Reboot to start the native kiosk shell."
