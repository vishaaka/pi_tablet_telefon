#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y curl ca-certificates lxc dnsmasq-base python3-pip

if ! command -v pi-apps >/dev/null 2>&1; then
  echo "Pi-Apps is recommended for Waydroid on Raspberry Pi OS."
  echo "Install Pi-Apps, then install Waydroid from its app list."
  echo "Pi-Apps: https://pi-apps.io/install-app/install-waydroid-on-raspberry-pi/"
else
  echo "Pi-Apps found. Open Pi-Apps and install Waydroid."
fi

echo "After install:"
echo "waydroid session start"
echo "waydroid show-full-ui"
