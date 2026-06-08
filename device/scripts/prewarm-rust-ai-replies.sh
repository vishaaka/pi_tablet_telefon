#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${PI_TABLET_RUST_URL:-http://127.0.0.1:8090}"
CONTACTS=(asya deniz mira atlas zeynep kerem)
MESSAGES=(
  "Merhaba"
  "Nasilsin?"
  "Bugun ne yapalim?"
  "Oyun oynayalim"
  "Bilmece sor"
  "Kisa hikaye anlat"
  "Tesekkur ederim"
)

curl -fsS "$BASE_URL/health" >/dev/null
for contact in "${CONTACTS[@]}"; do
  call_id="$(
    curl -fsS -X POST -H 'Content-Type: application/json' \
      -d "{\"contact_id\":\"$contact\"}" "$BASE_URL/calls/start" |
      grep -oE '[0-9a-f]{8}-[0-9a-f-]{27}' |
      head -1
  )"
  for message in "${MESSAGES[@]}"; do
    curl -fsS -X POST -H 'Content-Type: application/json' \
      -d "{\"text\":\"$message\"}" "$BASE_URL/calls/$call_id/message" >/dev/null
  done
  curl -fsS -X POST "$BASE_URL/calls/$call_id/end" >/dev/null || true
done

echo "Rust AI quick replies and voices are cached."
