#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt full-upgrade -y
sudo apt install -y \
  curl \
  git \
  dkms \
  lspci \
  usbutils \
  alsa-utils \
  libinput-tools \
  python3 \
  python3-venv \
  python3-pip

echo "System update complete. Reboot is recommended:"
echo "sudo reboot"
