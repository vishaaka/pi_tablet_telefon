#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKUP_ROOT="${PI_TABLET_BACKUP_ROOT:-/mnt/pi-backup}"
LATEST_FILE="$BACKUP_ROOT/LATEST"
USER_NAME="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"

if [ ! -f "$LATEST_FILE" ]; then
  echo "Refusing legacy cleanup without the USB backup marker: $LATEST_FILE"
  exit 1
fi
BACKUP_DIR="$(cat "$LATEST_FILE")"
if [ ! -f "$BACKUP_DIR/SHA256SUMS" ]; then
  echo "Refusing legacy cleanup without backup checksums: $BACKUP_DIR/SHA256SUMS"
  exit 1
fi
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)

if ! curl -fsS http://127.0.0.1:8090/health | grep -q '"runtime":"rust"'; then
  echo "Refusing legacy cleanup because the Rust backend is not healthy."
  exit 1
fi

echo "Stopping and removing legacy tablet services..."
for service in \
  pi-tablet-phone-autostart.service \
  pi-tablet-backend.service \
  pi-tablet-local-ai.service \
  waydroid-container.service; do
  sudo systemctl disable --now "$service" 2>/dev/null || true
done
waydroid session stop 2>/dev/null || true
pkill -f 'waydroid|uvicorn|llama-server|whisper-cli' 2>/dev/null || true

sudo rm -f \
  /etc/systemd/system/pi-tablet-phone-autostart.service \
  /etc/systemd/system/pi-tablet-backend.service \
  /etc/systemd/system/pi-tablet-local-ai.service
sudo rm -rf /etc/systemd/system/pi-tablet-backend.service.d
sudo systemctl daemon-reload

echo "Removing Waydroid packages and data..."
if dpkg-query -W -f='${Status}' waydroid 2>/dev/null | grep -q 'install ok installed'; then
  sudo apt-get purge -y waydroid
fi
sudo rm -rf \
  /var/lib/waydroid \
  /etc/waydroid-extra \
  /var/lib/misc/dnsmasq.waydroid0.leases \
  "$USER_HOME/.local/share/waydroid" \
  "$USER_HOME/.config/waydroid" \
  "$USER_HOME/.cache/waydroid" \
  "$USER_HOME/pi-apps/apps/Waydroid" \
  "$USER_HOME/pi-apps/logs/install-incomplete-Waydroid.log1" \
  "$USER_HOME/pi-apps/logs/install-fail-Waydroid.log" \
  "$USER_HOME/pi-apps/logs/install-success-Waydroid.log2" \
  "$USER_HOME/Desktop/Waydroid.desktop"

echo "Removing legacy Python runtime and local AI models..."
rm -rf "$REPO_DIR/backend/.venv"
sudo rm -rf /opt/pi-tablet-ai
sudo find /var/lib/pi-tablet-rust/audio -maxdepth 1 -type f -name '*.mp3' -delete
rm -f \
  "$USER_HOME/pi-tablet-phone-autostart.log" \
  "$USER_HOME/.local/share/pi-tablet-rust-rollback/labwc-autostart.before-rust"

echo "Cleaning unused packages and caches..."
sudo apt-get autoremove --purge -y
sudo apt-get clean
rm -rf "$REPO_DIR/rust-tablet/target"

sudo systemctl enable --now pi-tablet-backend-rust.service
curl -fsS http://127.0.0.1:8090/health
echo
echo "Legacy tablet system removed. Rust tablet is the only active tablet runtime."
