#!/usr/bin/env bash
set -euo pipefail

echo "== Waydroid status =="
waydroid status

echo
echo "== Installed Waydroid apps =="
waydroid app list || true

echo
echo "To open Android UI:"
echo "waydroid show-full-ui"
