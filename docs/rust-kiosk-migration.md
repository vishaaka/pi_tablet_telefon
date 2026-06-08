# Rust Kiosk Migration

The native Rust tablet runs directly on Raspberry Pi OS and removes Waydroid from the normal startup path.

## Components

- Native fullscreen Slint shell
- Rust contact and call backend on port `8090`
- Chromium kiosk launcher for YouTube Kids
- Native GCompris and Tux Paint launchers
- Existing Hailo camera inference support on the host
- Existing Python backend retained during the transition

## Safety

The installer refuses to run unless `/mnt/pi-backup/LATEST` points to a backup containing valid SHA-256 checksums.

## Install

```bash
cd ~/pi_tablet_telefon
bash device/scripts/install-rust-tablet.sh
sudo reboot
```

## Return To Waydroid

```bash
cd ~/pi_tablet_telefon
bash device/scripts/rollback-to-waydroid.sh
sudo reboot
```

The migration disables Waydroid services but does not remove Waydroid files. This makes rollback quick and preserves the verified USB backup as the final recovery option.
