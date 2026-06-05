#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="/boot/firmware/config.txt"

if [ ! -f "$CONFIG_FILE" ]; then
  CONFIG_FILE="/boot/config.txt"
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Raspberry Pi config.txt not found."
  exit 1
fi

echo "Using config file: $CONFIG_FILE"
sudo cp "$CONFIG_FILE" "$CONFIG_FILE.pi-tablet-backup"

if ! grep -q "^dtoverlay=max98357a" "$CONFIG_FILE"; then
  {
    echo ""
    echo "# Pi Tablet Telefon - MAX98357A I2S speaker output"
    echo "dtoverlay=max98357a"
  } | sudo tee -a "$CONFIG_FILE" >/dev/null
else
  echo "dtoverlay=max98357a already present"
fi

echo
echo "MAX98357A overlay configured."
echo "Reboot, then run:"
echo "bash device/scripts/check-max98357a.sh"
