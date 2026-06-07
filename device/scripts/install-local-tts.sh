#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKEND_DIR="$REPO_DIR/backend"
VENV="$BACKEND_DIR/.venv"
PIPER_DIR="${PI_PIPER_DIR:-/opt/pi-tablet-ai/piper}"
VOICE="${PI_PIPER_VOICE:-tr_TR-dfki-medium}"
MODEL="$PIPER_DIR/$VOICE.onnx"
CONFIG="$MODEL.json"
BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium"
BACKEND_DROPIN="/etc/systemd/system/pi-tablet-backend.service.d/local-tts.conf"
RUN_USER="${SUDO_USER:-$USER}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Backend virtualenv not found: $VENV"
  echo "Run: bash device/scripts/install-backend.sh $REPO_DIR"
  exit 1
fi

sudo apt update
sudo apt install -y ffmpeg curl
"$VENV/bin/pip" install --upgrade piper-tts edge-tts

sudo mkdir -p "$PIPER_DIR"
sudo chown -R "$RUN_USER:$RUN_USER" "$PIPER_DIR"

if [ ! -f "$MODEL" ]; then
  curl -fL --retry 3 -o "$MODEL" "$BASE_URL/$VOICE.onnx?download=true"
fi
if [ ! -f "$CONFIG" ]; then
  curl -fL --retry 3 -o "$CONFIG" "$BASE_URL/$VOICE.onnx.json?download=true"
fi

sudo mkdir -p "$(dirname "$BACKEND_DROPIN")"
sudo tee "$BACKEND_DROPIN" >/dev/null <<DROPIN
[Service]
Environment=PI_TTS_ENABLED_OVERRIDE=true
Environment=PI_TTS_PROVIDER_OVERRIDE=edge_tts
Environment=PI_PIPER_MODEL=$MODEL
Environment=PI_PIPER_VOLUME=1.0
Environment=PI_TTS_GAIN_DB=6
DROPIN

sudo systemctl daemon-reload
sudo systemctl restart pi-tablet-backend.service

echo "Testing natural Turkish TTS with local Piper fallback..."
export PI_TTS_ENABLED_OVERRIDE=true
export PI_TTS_PROVIDER_OVERRIDE=edge_tts
export PI_PIPER_MODEL="$MODEL"
export PI_PIPER_VOLUME=1.0
export PI_TTS_GAIN_DB=6
cd "$BACKEND_DIR"
"$VENV/bin/python" - <<'PY'
from app.personas import CONTACTS
from app.tts_engine import synthesize_for_contact, tts_status

result = synthesize_for_contact("local-tts-test", CONTACTS[0], "Merhaba, yerel Türkçe ses sistemi hazır.")
print(tts_status())
print(result)
if not result.audio_url:
    raise SystemExit(result.error or "Local TTS did not create audio")
PY

curl -fsS http://127.0.0.1:8080/health
echo
