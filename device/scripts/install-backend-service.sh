#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKEND_DIR="$REPO_DIR/backend"
SERVICE_FILE="/etc/systemd/system/pi-tablet-backend.service"

if [ ! -x "$BACKEND_DIR/.venv/bin/uvicorn" ]; then
  echo "Backend virtualenv not found. Run first:"
  echo "bash device/scripts/install-backend.sh $REPO_DIR"
  exit 1
fi

sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=Pi Tablet Telefon backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BACKEND_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$BACKEND_DIR/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable --now pi-tablet-backend
sudo systemctl status pi-tablet-backend --no-pager
