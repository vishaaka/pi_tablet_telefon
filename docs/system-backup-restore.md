# Full System Restore Backup

The compact restore bundle contains the complete root filesystem, boot files, partition table, installed package list, systemd unit inventory, disk header, and SHA-256 checksums.

It is a full logical system backup rather than a raw 117 GB byte-for-byte disk image. This allows the working system to fit on a 32 GB USB drive while preserving Waydroid, applications, AI models, configuration, and user data.

## Create Backup

Mount an ext4 USB drive and run:

```bash
sudo mkdir -p /mnt/pi-backup
sudo mount /dev/sda1 /mnt/pi-backup
sudo chown "$USER:$USER" /mnt/pi-backup
bash device/scripts/create-system-backup.sh /mnt/pi-backup
```

The script stops the tablet services during capture and restarts the backend afterward.

## Verify Backup

```bash
BACKUP="$(cat /mnt/pi-backup/LATEST)"
cd "$BACKUP"
sha256sum -c SHA256SUMS
zstd -t rootfs.tar.zst
zstd -t boot-firmware.tar.zst
```

## Restore Overview

1. Boot the Pi from another Raspberry Pi OS card or attach the target card to another Linux system.
2. Recreate the target partitions using `meta/partition-table.sfdisk` when restoring to an equal or larger card.
3. Format and mount the root and boot partitions.
4. Extract `rootfs.tar.zst` into the mounted root partition.
5. Extract `boot-firmware.tar.zst` into the mounted boot partition.
6. Confirm `/etc/fstab`, filesystem UUIDs, and boot command line before rebooting.

Example extraction:

```bash
sudo tar --xattrs --acls --numeric-owner -I zstd -xpf rootfs.tar.zst -C /mnt/restore-root
sudo tar --xattrs --acls --numeric-owner -I zstd -xpf boot-firmware.tar.zst -C /mnt/restore-boot
```
