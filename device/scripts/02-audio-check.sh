#!/usr/bin/env bash
set -euo pipefail

echo "== Playback devices =="
aplay -l || true

echo
echo "== Capture devices =="
arecord -l || true

echo
echo "== USB audio devices =="
lsusb | grep -i -E "audio|sound|microphone|c-media|realtek|usb" || true

echo
echo "For speaker test run:"
echo "speaker-test -t wav -c 2"
echo
echo "For a 5-second mic recording test run:"
echo "arecord -d 5 -f cd ~/mic-test.wav && aplay ~/mic-test.wav"
