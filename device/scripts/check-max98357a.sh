#!/usr/bin/env bash
set -euo pipefail

echo "== Playback devices =="
aplay -l || true

echo
echo "== PipeWire/WirePlumber sinks =="
if command -v wpctl >/dev/null 2>&1; then
  wpctl status || true
else
  echo "wpctl not found"
fi

echo
echo "== Quick speaker test =="
echo "Use the MAX98357A card number from aplay -l, for example:"
echo "speaker-test -D plughw:CARD,0 -t wav -c 2"
echo
echo "If PipeWire is used, set default output from the desktop audio menu or:"
echo "wpctl set-default <sink-id>"
