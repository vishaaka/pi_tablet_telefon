#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-/opt/pi-tablet-rust/sounds}"
sudo mkdir -p "$TARGET"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

tone() {
  local name="$1" low="$2" high="$3"
  sox -q -n "$work/$name.wav" synth 0.16 sine "$low" sine "$high" \
    gain -8 fade 0.01 0.16 0.02
}

tone dtmf-1 697 1209
tone dtmf-2 697 1336
tone dtmf-3 697 1477
tone dtmf-4 770 1209
tone dtmf-5 770 1336
tone dtmf-6 770 1477
tone dtmf-7 852 1209
tone dtmf-8 852 1336
tone dtmf-9 852 1477
tone dtmf-star 941 1209
tone dtmf-0 941 1336
tone dtmf-hash 941 1477

sox -q -n "$work/ring-on.wav" synth 1.4 sine 425 gain -13 fade 0.03 1.4 0.08
sox -q "$work/ring-on.wav" "$work/ringback.wav" pad 0 2.6
sox -q -n "$work/connect.wav" synth 0.14 sine 950 gain -8 fade 0.01 0.14 0.03
sox -q -n "$work/end.wav" synth 0.12 sine 620 gain -8 fade 0.01 0.12 0.03
sox -q -n "$work/delete.wav" synth 0.07 sine 330 gain -12 fade 0.01 0.07 0.02

sudo install -m 0644 "$work"/*.wav "$TARGET/"
echo "Phone tones generated in $TARGET"
