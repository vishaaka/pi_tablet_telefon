# Rust Pi Tablet

This workspace is the Waydroid-free tablet replacement.

- `pi-tablet-shell`: native fullscreen Slint shell with phone keypad and app launcher.
- `pi-tablet-backend-rs`: low-memory Rust API compatible with the existing contact and call flow.

The first deployment runs the Rust backend on port `8090` beside the existing Python backend. After verification, the installer disables Waydroid and makes the Rust shell the graphical startup application.
