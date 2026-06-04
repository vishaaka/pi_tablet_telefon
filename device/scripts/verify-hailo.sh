#!/usr/bin/env bash
set -euo pipefail

echo "Checking PCIe devices..."
lspci | grep -i hailo || true

echo
echo "Checking installed Hailo packages..."
dpkg -l | grep -E "hailo|hailort" || true

echo
echo "Checking Hailo kernel module and device nodes..."
lsmod | grep -i hailo || true
ls -l /dev/hailo* 2>/dev/null || true

echo
echo "Checking hailortcli path..."
command -v hailortcli || true

echo "Checking HailoRT firmware identify..."
if command -v hailortcli >/dev/null 2>&1; then
  hailortcli fw-control identify
else
  echo "hailortcli not found. Try:"
  echo "sudo apt update"
  echo "apt-cache search '^(hailo|hailort)'"
  echo "sudo apt install --reinstall hailo-all hailort python3-hailort"
  echo "If hailo-dkms exists in your apt search output, also install it."
  echo "sudo reboot"
  exit 1
fi
