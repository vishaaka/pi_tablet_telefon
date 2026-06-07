#!/usr/bin/env bash
set -euo pipefail

ASSET="${1:-/usr/share/rpi-camera-assets/hailo_yolov8_inference.json}"

echo "== Hailo device =="
lspci | grep -i hailo || true
ls -l /dev/hailo* 2>/dev/null || true

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
timeout 8 rpicam-hello -t 5000 --nopreview --post-process-file "$ASSET"
echo "Hailo vision test completed."
