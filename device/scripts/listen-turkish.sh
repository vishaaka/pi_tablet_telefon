#!/usr/bin/env bash
set -euo pipefail

WHISPER_COMMAND="${PI_WHISPER_COMMAND:-/opt/pi-tablet-stt/whisper.cpp/build/bin/whisper-cli}"
WHISPER_MODEL="${PI_WHISPER_MODEL:-/opt/pi-tablet-stt/whisper.cpp/models/ggml-tiny-q5_1.bin}"
CAPTURE_DEVICE="${PI_CAPTURE_DEVICE:-plughw:CARD=sndrpigooglevoi,DEV=0}"
WORK_DIR="${PI_STT_WORK_DIR:-/var/lib/pi-tablet-rust/stt}"
mkdir -p "$WORK_DIR"

input="${1:-}"
if [ -z "$input" ]; then
  input="$WORK_DIR/listen-$(date +%s%N).wav"
  timeout 14 sox -q -t alsa "$CAPTURE_DEVICE" -r 16000 -c 1 -b 16 "$input" \
    silence 1 0.10 2% 1 1.20 2% trim 0 12 || true
fi

normalized="$WORK_DIR/normalized-$(date +%s%N).wav"
ffmpeg -loglevel error -y -i "$input" -ar 16000 -ac 1 -c:a pcm_s16le "$normalized"
output="$(
  "$WHISPER_COMMAND" --model "$WHISPER_MODEL" --file "$normalized" \
    --language tr --no-timestamps --threads 4 2>/dev/null |
    sed -E 's/^[[:space:]]+//; /^$/d' |
    tail -1
)"
rm -f "$normalized"
if [[ "$input" == "$WORK_DIR/"* ]]; then
  rm -f "$input"
fi
if [[ "$output" == \[*\] ]] ||
  [[ "${output,,}" == *"müzik"* ]] ||
  [[ "${output,,}" == *"music"* ]] ||
  [[ "${output,,}" == *"sessizlik"* ]]; then
  output=""
fi
printf '%s\n' "$output"
