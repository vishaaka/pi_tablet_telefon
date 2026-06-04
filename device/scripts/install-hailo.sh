#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y dkms
sudo apt install -y hailo-all

echo
echo "Installed Hailo packages:"
dpkg -l | grep -E "hailo|hailort" || true

echo "Hailo packages installed. Reboot before verification:"
echo "sudo reboot"
