# Rust Pi Tablet

This workspace is the Waydroid-free tablet replacement.

- `pi-tablet-shell`: native fullscreen Slint shell with phone keypad and app launcher.
- `pi-tablet-backend-rs`: low-memory Rust API compatible with the existing contact and call flow.

The Rust backend runs on port `8090`, uses native `espeak-ng` speech, and does not
require Python or Waydroid. The legacy runtime can be removed after the Rust kiosk
has been verified and a USB backup is present.
