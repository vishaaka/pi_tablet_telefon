#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${PI_LOCAL_AI_DIR:-/opt/pi-tablet-ai}"
LLAMA_DIR="$INSTALL_DIR/llama.cpp"
WHISPER_DIR="$INSTALL_DIR/whisper.cpp"
MODEL_DIR="$INSTALL_DIR/models"
MODEL_FILE="$MODEL_DIR/qwen3-0.6b-q4_k_m.gguf"
MODEL_URL="${PI_LOCAL_AI_MODEL_URL:-https://huggingface.co/Open4bits/Qwen3-0.6b-gguf/resolve/main/qwen3-0.6b-Q4_K_M.gguf}"
SERVICE_FILE="/etc/systemd/system/pi-tablet-local-ai.service"
BACKEND_DROPIN="/etc/systemd/system/pi-tablet-backend.service.d/local-ai.conf"
RUN_USER="${SUDO_USER:-$USER}"
RUN_HOME="$(getent passwd "$RUN_USER" | cut -d: -f6)"
BUILD_JOBS="${PI_LOCAL_AI_BUILD_JOBS:-1}"

sudo apt update
sudo apt install -y build-essential cmake git curl libcurl4-openssl-dev

sudo mkdir -p "$INSTALL_DIR"
sudo chown -R "$RUN_USER:$RUN_USER" "$INSTALL_DIR"
mkdir -p "$MODEL_DIR"

if [ ! -s "$MODEL_FILE" ]; then
  echo "Downloading the low-memory Q4 local chat model..."
  curl -fL --retry 5 --retry-delay 3 -o "$MODEL_FILE.part" "$MODEL_URL"
  mv "$MODEL_FILE.part" "$MODEL_FILE"
fi

if [ ! -d "$LLAMA_DIR/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$LLAMA_DIR"
else
  git -C "$LLAMA_DIR" pull --ff-only
fi
cmake -S "$LLAMA_DIR" -B "$LLAMA_DIR/build" -DLLAMA_CURL=ON -DCMAKE_BUILD_TYPE=Release
cmake --build "$LLAMA_DIR/build" --config Release -j"$BUILD_JOBS" --target llama-server

if [ ! -d "$WHISPER_DIR/.git" ]; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git "$WHISPER_DIR"
else
  git -C "$WHISPER_DIR" pull --ff-only
fi
cmake -S "$WHISPER_DIR" -B "$WHISPER_DIR/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$WHISPER_DIR/build" --config Release -j"$BUILD_JOBS" --target whisper-cli
if [ ! -f "$WHISPER_DIR/models/ggml-tiny.bin" ]; then
  bash "$WHISPER_DIR/models/download-ggml-model.sh" tiny
fi

sudo tee "$SERVICE_FILE" >/dev/null <<SERVICE
[Unit]
Description=Pi Tablet local Qwen voice chat model
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$LLAMA_DIR
Environment=HOME=$RUN_HOME
ExecStart=$LLAMA_DIR/build/bin/llama-server -m $MODEL_FILE --host 127.0.0.1 --port 8081 -c 768 -t 2 -np 1 --jinja
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

sudo mkdir -p "$(dirname "$BACKEND_DROPIN")"
sudo tee "$BACKEND_DROPIN" >/dev/null <<DROPIN
[Unit]
After=pi-tablet-local-ai.service
Wants=pi-tablet-local-ai.service

[Service]
Environment=PI_AI_PROVIDER_OVERRIDE=llama_cpp
Environment=PI_AI_API_BASE_OVERRIDE=http://127.0.0.1:8081/v1
Environment=PI_AI_MODEL_OVERRIDE=Qwen3-0.6B-Q4_K_M
Environment=PI_AI_TIMEOUT_SECONDS=45
Environment=PI_STT_COMMAND=$WHISPER_DIR/build/bin/whisper-cli
Environment=PI_STT_MODEL=$WHISPER_DIR/models/ggml-tiny.bin
Environment=PI_STT_LANGUAGE=tr
Environment=PI_STT_THREADS=2
Environment=PI_MIC_WAIT_SECONDS=30
Environment=PI_MIC_MAX_SECONDS=30
Environment=PI_MIC_SILENCE_SECONDS=2.0
DROPIN

sudo systemctl daemon-reload
sudo systemctl enable --now pi-tablet-local-ai.service
sudo systemctl restart pi-tablet-backend.service
sudo systemctl status pi-tablet-local-ai.service --no-pager

echo "Waiting for local model startup..."
for _ in $(seq 1 120); do
  if curl -fsS http://127.0.0.1:8081/health >/dev/null 2>&1; then
    break
  fi
  sleep 5
done

curl -fsS http://127.0.0.1:8081/health
echo
curl -fsS http://127.0.0.1:8080/health
echo
