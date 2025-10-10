#!/bin/bash

set -e
set -u
set -o pipefail

echo "Installing USB auto-mount + auto-unmount with full write permissions for all users..."

# Get the UID and GID of frc4607 user
FRC_UID=$(id -u frc4607)
FRC_GID=$(id -g frc4607)

echo "Detected frc4607 user: UID=$FRC_UID, GID=$FRC_GID"

# ========================
# 1. Create USB mount script
# ========================
MOUNT_SCRIPT="/usr/local/bin/usb-mount.sh"

sudo tee "$MOUNT_SCRIPT" > /dev/null << EOF
#!/bin/bash

DEVICE="\$1"
sleep 1

FSTYPE=\$(blkid -o value -s TYPE "\$DEVICE")
LABEL=\$(blkid -o value -s LABEL "\$DEVICE")

[ -z "\$LABEL" ] && LABEL=\$(basename "\$DEVICE")
MOUNT_POINT="/media/\$LABEL"

mkdir -p "\$MOUNT_POINT"

# Default mount options to allow global write access
MOUNT_OPTS="defaults,noatime,umask=000"

# Adjust mount options for specific filesystems
if [[ "\$FSTYPE" == "vfat" || "\$FSTYPE" == "exfat" || "\$FSTYPE" == "ntfs" ]]; then
    MOUNT_OPTS="defaults,noatime,umask=000,uid=$FRC_UID,gid=$FRC_GID"
fi

/bin/mount -t "\$FSTYPE" -o "\$MOUNT_OPTS" "\$DEVICE" "\$MOUNT_POINT" 2>/dev/null

if /bin/mount | /bin/grep -q "\$MOUNT_POINT"; then
    # Set ownership for ext4 and other filesystems
    if [[ "\$FSTYPE" == "ext4" || "\$FSTYPE" == "ext3" || "\$FSTYPE" == "ext2" ]]; then
        chown -R $FRC_UID:$FRC_GID "\$MOUNT_POINT"
        chmod -R 775 "\$MOUNT_POINT"
    fi
    # Also set ownership of the mount point directory itself (for all filesystem types)
    chown $FRC_UID:$FRC_GID "\$MOUNT_POINT"
    /bin/logger "USB \$DEVICE mounted at \$MOUNT_POINT with write access for frc4607 user"
else
    /bin/logger "Failed to mount \$DEVICE"
    rmdir "\$MOUNT_POINT" 2>/dev/null
fi
EOF

sudo chmod +x "$MOUNT_SCRIPT"

# ========================
# 2. Create USB unmount script
# ========================
UNMOUNT_SCRIPT="/usr/local/bin/usb-unmount.sh"

sudo tee "$UNMOUNT_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash

DEVICE="$1"
sleep 1

MOUNTED=$(/bin/mount | /bin/grep "$DEVICE" | awk '{ print $3 }')

if [ -n "$MOUNTED" ]; then
    /bin/umount "$DEVICE"
    /bin/logger "USB $DEVICE unmounted from $MOUNTED"
    /bin/rmdir "$MOUNTED" 2>/dev/null
fi
EOF

sudo chmod +x "$UNMOUNT_SCRIPT"

# ========================
# 3. Create udev rules
# ========================
RULE_FILE="/etc/udev/rules.d/99-usb-mount.rules"

sudo tee "$RULE_FILE" > /dev/null <<EOF
KERNEL=="sd[a-z][0-9]", ACTION=="add", RUN+="/usr/local/bin/usb-mount.sh /dev/%k"
KERNEL=="sd[a-z][0-9]", ACTION=="remove", RUN+="/usr/local/bin/usb-unmount.sh /dev/%k"
EOF

# ========================
# 4. Reload udev
# ========================
echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

# ========================
# 5. Ensure /media exists
# ========================
sudo mkdir -p /media

echo ""
echo "Configuration complete!"
echo "  FAT/exFAT/NTFS: uid=$FRC_UID, gid=$FRC_GID, umask=000"
echo "  EXT4/EXT3/EXT2: ownership set after mount"
echo ""
echo "USB drives will auto-mount under /media/<LABEL> with write access for frc4607 user."
echo ""
echo "To apply changes to currently mounted USB:"
echo "  1. Unplug USB drive"
echo "  2. Plug it back in"
echo "  Or run: sudo umount /media/RECORDINGS && sudo /usr/local/bin/usb-mount.sh /dev/sda1"