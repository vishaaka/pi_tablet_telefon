#!/usr/bin/env bash
set -euo pipefail

echo "== OS =="
uname -a
cat /etc/os-release

echo
echo "== CPU/RAM =="
getconf LONG_BIT
free -h

echo
echo "== Power/throttle =="
if command -v vcgencmd >/dev/null 2>&1; then
  vcgencmd get_throttled
  vcgencmd measure_temp || true
else
  echo "vcgencmd not found"
fi

echo
echo "== PCIe =="
lspci || true

echo
echo "== USB =="
lsusb || true

echo
echo "== Audio =="
aplay -l || true
arecord -l || true

echo
echo "== Display session =="
echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unknown}"
echo "WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-none}"
