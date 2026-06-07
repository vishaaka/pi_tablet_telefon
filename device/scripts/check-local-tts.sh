#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKEND_DIR="$REPO_DIR/backend"
MODEL="${PI_PIPER_MODEL:-/opt/pi-tablet-ai/piper/tr_TR-dfki-medium.onnx}"

echo "== Piper package =="
"$BACKEND_DIR/.venv/bin/python" -c "import importlib.metadata; print(importlib.metadata.version('piper-tts'))"

echo
echo "== Turkish model =="
ls -lh "$MODEL" "$MODEL.json"

echo
echo "== Backend TTS health =="
curl -fsS http://127.0.0.1:8080/health | "$BACKEND_DIR/.venv/bin/python" -c \
  "import json,sys; print(json.dumps(json.load(sys.stdin)['tts'], ensure_ascii=False, indent=2))"

echo
echo "== Recent generated audio =="
find "$BACKEND_DIR/generated_audio" -maxdepth 1 -type f -printf '%T@ %p\n' |
  sort -nr |
  head -3 |
  cut -d' ' -f2- |
  xargs -r ls -lh
