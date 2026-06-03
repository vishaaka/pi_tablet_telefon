#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y dkms
sudo apt install -y hailo-all

echo "Hailo packages installed. Reboot before verification:"
echo "sudo reboot"
