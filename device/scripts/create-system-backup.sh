#!/usr/bin/env bash
set -euo pipefail

TARGET_ROOT="${1:-/mnt/pi-backup}"
SOURCE_DISK="${PI_BACKUP_SOURCE_DISK:-/dev/mmcblk0}"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$TARGET_ROOT/pi-tablet-full-$STAMP"
LOG_FILE="$BACKUP_DIR/backup.log"

if [ ! -b "$SOURCE_DISK" ]; then
  echo "Source disk not found: $SOURCE_DISK"
  exit 1
fi
if ! mountpoint -q "$TARGET_ROOT"; then
  echo "Backup target is not mounted: $TARGET_ROOT"
  exit 1
fi
if [ "$(findmnt -no FSTYPE "$TARGET_ROOT")" = "vfat" ]; then
  echo "Backup target must not be FAT32 because archives exceed 4 GB."
  exit 1
fi
if [ "$(df --output=avail -B1 "$TARGET_ROOT" | tail -1)" -lt 10737418240 ]; then
  echo "Backup target needs at least 10 GB free."
  exit 1
fi

mkdir -p "$BACKUP_DIR/meta"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Pi Tablet full restore backup"
echo "Started: $(date -Is)"
echo "Source: $SOURCE_DISK"
echo "Target: $BACKUP_DIR"

restart_services() {
  sudo systemctl start pi-tablet-backend.service 2>/dev/null || true
  sudo systemctl start pi-tablet-local-ai.service 2>/dev/null || true
}
trap restart_services EXIT

sudo systemctl stop pi-tablet-phone-autostart.service 2>/dev/null || true
waydroid session stop 2>/dev/null || true
sudo systemctl stop waydroid-container.service 2>/dev/null || true
sudo systemctl stop pi-tablet-backend.service 2>/dev/null || true
sudo systemctl stop pi-tablet-local-ai.service 2>/dev/null || true
sync

uname -a >"$BACKUP_DIR/meta/uname.txt"
lsblk -o NAME,SIZE,FSTYPE,UUID,PARTUUID,MOUNTPOINTS,MODEL,TRAN >"$BACKUP_DIR/meta/lsblk.txt"
findmnt --real >"$BACKUP_DIR/meta/findmnt.txt"
df -hT >"$BACKUP_DIR/meta/df.txt"
dpkg-query -W -f='${binary:Package} ${Version}\n' >"$BACKUP_DIR/meta/packages.txt"
systemctl list-unit-files >"$BACKUP_DIR/meta/systemd-unit-files.txt"
sudo sfdisk -d "$SOURCE_DISK" >"$BACKUP_DIR/meta/partition-table.sfdisk"
sudo dd if="$SOURCE_DISK" of="$BACKUP_DIR/meta/disk-header-16MiB.img" bs=1M count=16 status=progress

echo "Archiving boot partition..."
sudo tar --xattrs --acls --numeric-owner -I 'zstd -T1 -6' -cpf "$BACKUP_DIR/boot-firmware.tar.zst" /boot/firmware

echo "Archiving root filesystem..."
sudo tar \
  --xattrs --acls --numeric-owner --one-file-system \
  --exclude="$TARGET_ROOT" \
  --exclude=/home/vish/system-backups \
  --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/run \
  --exclude=/tmp --exclude=/mnt --exclude=/media \
  -I 'zstd -T1 -6' -cpf "$BACKUP_DIR/rootfs.tar.zst" /

echo "Creating checksums..."
(cd "$BACKUP_DIR" && sha256sum boot-firmware.tar.zst rootfs.tar.zst meta/disk-header-16MiB.img >SHA256SUMS)
(cd "$BACKUP_DIR" && sha256sum -c SHA256SUMS)

echo "$BACKUP_DIR" >"$TARGET_ROOT/LATEST"
sync
echo "Completed: $(date -Is)"
du -sh "$BACKUP_DIR"
