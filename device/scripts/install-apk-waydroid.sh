#!/usr/bin/env bash
set -euo pipefail

APK_PATH="${1:-android-phone-sim/app/build/outputs/apk/debug/app-debug.apk}"

if [ ! -f "$APK_PATH" ]; then
  echo "APK not found: $APK_PATH"
  exit 1
fi

waydroid app install "$APK_PATH"
waydroid app launch com.vishaaka.pitablettelefon
