#!/usr/bin/env bash
set -euo pipefail

echo "== Local AI service =="
systemctl status pi-tablet-local-ai --no-pager

echo
echo "== llama.cpp health =="
curl -fsS http://127.0.0.1:8081/health

echo
echo "== Pi Tablet backend health =="
curl -fsS http://127.0.0.1:8080/health

echo
echo "== Whisper files =="
ls -lh /opt/pi-tablet-ai/whisper.cpp/build/bin/whisper-cli
ls -lh /opt/pi-tablet-ai/whisper.cpp/models/ggml-tiny.bin
