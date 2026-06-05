#!/usr/bin/env bash
set -euo pipefail

echo "== Boot config audio overlays =="
grep -nE "max98357|googlevoicehat|i2s|dtparam=audio" /boot/firmware/config.txt /boot/config.txt 2>/dev/null || true

echo
echo "== Playback devices =="
aplay -l || true

echo
echo "== Capture devices =="
arecord -l || true

echo
echo "== PipeWire/WirePlumber audio graph =="
if command -v wpctl >/dev/null 2>&1; then
  wpctl status || true
else
  echo "wpctl not found"
fi

echo
echo "== Recording test examples =="
echo "Find the INMP441/voiceHAT capture card above, then run one of:"
echo "arecord -D plughw:CARD,0 -f S32_LE -r 48000 -c 1 -d 5 ~/inmp441-test.wav"
echo "arecord -D plughw:CARD,0 -f S16_LE -r 48000 -c 1 -d 5 ~/inmp441-test.wav"
echo "aplay ~/inmp441-test.wav"
