#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y dkms
sudo apt install -y hailo-all
sudo apt-get install --reinstall -y hailort-pcie-driver
echo hailo_pci | sudo tee /etc/modules-load.d/hailo-pci.conf >/dev/null
sudo modprobe hailo_pci

echo
echo "Installed Hailo packages:"
dpkg -l | grep -E "hailo|hailort" || true

echo "Hailo packages installed. Reboot before verification:"
echo "sudo reboot"
