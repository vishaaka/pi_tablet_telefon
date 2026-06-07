#!/usr/bin/env bash
set -euo pipefail

ASSET="${1:-/usr/share/rpi-camera-assets/hailo_yolov8_inference.json}"

echo "== Hailo device =="
lspci | grep -i hailo || true
ls -l /dev/hailo* 2>/dev/null || true
if [ ! -e /dev/hailo0 ]; then
  echo "Hailo PCIe device node is missing."
  echo "Repair for the current kernel:"
  echo "sudo apt-get install --reinstall -y hailort-pcie-driver"
  echo "sudo modprobe hailo_pci"
  exit 1
fi

echo
echo "== HailoRT =="
if ! command -v hailortcli >/dev/null 2>&1; then
  echo "hailortcli not found. Run: sudo apt install hailo-all"
  exit 1
fi
hailortcli fw-control identify

echo
echo "== rpicam Hailo assets =="
ls -1 /usr/share/rpi-camera-assets/hailo_*_inference.json 2>/dev/null || true
if [ ! -f "$ASSET" ]; then
  echo "Missing Hailo rpicam asset: $ASSET"
  echo "Try: sudo apt install hailo-models rpicam-apps-hailo-postprocess"
  exit 1
fi

echo
echo "== Camera list =="
if command -v rpicam-hello >/dev/null 2>&1; then
  rpicam-hello --list-cameras || true
else
  echo "rpicam-hello not found. Try: sudo apt install rpicam-apps"
  exit 1
fi

echo
echo "== 5 second Hailo YOLO camera test =="
echo "Using: $ASSET"
OUTPUT="$(mktemp)"
trap 'rm -f "$OUTPUT"' EXIT
if ! timeout 8 rpicam-hello -t 5000 --nopreview --post-process-file "$ASSET" 2>&1 | tee "$OUTPUT"; then
  echo "Hailo camera test command failed."
  exit 1
fi
if grep -q "HailoRT not ready" "$OUTPUT"; then
  echo "HailoRT is not ready for camera inference."
  exit 1
fi
if ! grep -q "Hailo device:" "$OUTPUT"; then
  echo "Camera opened, but Hailo inference was not confirmed."
  exit 1
fi
echo "Hailo vision test completed."
