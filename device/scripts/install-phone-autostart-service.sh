#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
SERVICE_FILE="/etc/systemd/system/pi-tablet-phone-autostart.service"
USER_NAME="${SUDO_USER:-$USER}"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
USER_ID="$(id -u "$USER_NAME")"
SCRIPT_PATH="$REPO_DIR/device/scripts/autostart-phone.sh"

if [ ! -x "$SCRIPT_PATH" ]; then
  chmod +x "$SCRIPT_PATH"
fi

sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=Pi Tablet Telefon Waydroid app autostart
After=network-online.target graphical.target pi-tablet-backend.service waydroid-container.service
Wants=network-online.target pi-tablet-backend.service

[Service]
Type=oneshot
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$REPO_DIR
Environment=HOME=$USER_HOME
Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DISPLAY=:0
Environment=PI_TABLET_VOLUME=2.00
ExecStart=/usr/bin/bash $SCRIPT_PATH $REPO_DIR
RemainAfterExit=yes
TimeoutStartSec=180

[Install]
WantedBy=graphical.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now pi-tablet-phone-autostart.service
sudo systemctl status pi-tablet-phone-autostart.service --no-pager
