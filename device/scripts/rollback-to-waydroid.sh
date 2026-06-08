#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
USER_NAME="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
LABWC_AUTOSTART="$USER_HOME/.config/labwc/autostart"
ROLLBACK_DIR="$USER_HOME/.local/share/pi-tablet-rust-rollback"

if ! command -v waydroid >/dev/null 2>&1; then
  echo "Waydroid was permanently removed. Restore the verified USB system backup instead."
  exit 1
fi

pkill -f /opt/pi-tablet-rust/bin/pi-tablet-shell 2>/dev/null || true
pkill -f 'chromium.*youtube' 2>/dev/null || true
sudo systemctl disable --now pi-tablet-backend-rust.service 2>/dev/null || true

if [ -f "$ROLLBACK_DIR/labwc-autostart.before-rust" ]; then
  cp "$ROLLBACK_DIR/labwc-autostart.before-rust" "$LABWC_AUTOSTART"
else
  grep -v 'run-rust-tablet-shell.sh' "$LABWC_AUTOSTART" >"$LABWC_AUTOSTART.tmp" || true
  mv "$LABWC_AUTOSTART.tmp" "$LABWC_AUTOSTART"
fi

sudo systemctl enable --now waydroid-container.service
bash "$REPO_DIR/device/scripts/install-phone-autostart-service.sh" "$REPO_DIR"

echo "Waydroid services restored. Reboot to return to the Android phone app."
