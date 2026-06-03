#!/usr/bin/env bash
set -euo pipefail

echo "Checking PCIe devices..."
lspci | grep -i hailo || true

echo "Checking HailoRT firmware identify..."
hailortcli fw-control identify
