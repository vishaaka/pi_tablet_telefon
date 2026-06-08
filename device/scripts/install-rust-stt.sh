#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${PI_STT_DIR:-/opt/pi-tablet-stt}"
WHISPER_DIR="$INSTALL_DIR/whisper.cpp"
MODEL="$WHISPER_DIR/models/ggml-tiny-q5_1.bin"

sudo apt update
sudo apt install -y git cmake sox libsox-fmt-alsa ffmpeg
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R "${SUDO_USER:-$USER}:${SUDO_USER:-$USER}" "$INSTALL_DIR"

if [ ! -d "$WHISPER_DIR/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git "$WHISPER_DIR"
else
  git -C "$WHISPER_DIR" pull --ff-only
fi

cmake -S "$WHISPER_DIR" -B "$WHISPER_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_EXAMPLES=ON -DWHISPER_BUILD_TESTS=OFF
cmake --build "$WHISPER_DIR/build" --config Release -j2

if [ ! -f "$MODEL" ]; then
  bash "$WHISPER_DIR/models/download-ggml-model.sh" tiny-q5_1
fi

test -x "$WHISPER_DIR/build/bin/whisper-cli"
test -f "$MODEL"
echo "Local Turkish whisper.cpp STT installed."
