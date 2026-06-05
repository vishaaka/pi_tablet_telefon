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
sudo cp "$CONFIG_FILE" "$CONFIG_FILE.inmp441-backup"

echo "Disabling plain max98357a overlay for experimental duplex I2S test..."
sudo sed -i 's/^dtoverlay=max98357a/# dtoverlay=max98357a # disabled for INMP441 experiment/' "$CONFIG_FILE"

if ! grep -q "^dtoverlay=googlevoicehat-soundcard" "$CONFIG_FILE"; then
  {
    echo ""
    echo "# Pi Tablet Telefon - experimental INMP441 I2S microphone + I2S speaker"
    echo "dtoverlay=googlevoicehat-soundcard"
  } | sudo tee -a "$CONFIG_FILE" >/dev/null
else
  echo "dtoverlay=googlevoicehat-soundcard already present"
fi

echo
echo "Experimental INMP441 overlay configured."
echo "Reboot, then run:"
echo "bash device/scripts/check-inmp441.sh"
