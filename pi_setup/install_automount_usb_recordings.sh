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

# Mount options based on filesystem type
if [[ "\$FSTYPE" == "vfat" ]]; then
    # FAT32 - use dmask and fmask for full permissions
    MOUNT_OPTS="rw,noatime,uid=$FRC_UID,gid=$FRC_GID,dmask=0000,fmask=0000"
elif [[ "\$FSTYPE" == "exfat" ]]; then
    # exFAT
    MOUNT_OPTS="rw,noatime,uid=$FRC_UID,gid=$FRC_GID,umask=0000"
elif [[ "\$FSTYPE" == "ntfs" ]]; then
    # NTFS
    MOUNT_OPTS="rw,noatime,uid=$FRC_UID,gid=$FRC_GID,umask=0000"
elif [[ "\$FSTYPE" == "ext4" || "\$FSTYPE" == "ext3" || "\$FSTYPE" == "ext2" ]]; then
    # ext filesystems
    MOUNT_OPTS="rw,noatime"
else
    # Default for unknown filesystems
    MOUNT_OPTS="rw,noatime"
fi

# Attempt to mount
/bin/mount -t "\$FSTYPE" -o "\$MOUNT_OPTS" "\$DEVICE" "\$MOUNT_POINT" 2>/dev/null

if /bin/mount | /bin/grep -q "\$MOUNT_POINT"; then
    # For ext filesystems, set ownership after mount
    if [[ "\$FSTYPE" == "ext4" || "\$FSTYPE" == "ext3" || "\$FSTYPE" == "ext2" ]]; then
        chown -R $FRC_UID:$FRC_GID "\$MOUNT_POINT"
        chmod -R 777 "\$MOUNT_POINT"
    fi
    
    # Ensure mount point directory itself has correct ownership
    chown $FRC_UID:$FRC_GID "\$MOUNT_POINT"
    
    /bin/logger "USB \$DEVICE (\$FSTYPE) mounted at \$MOUNT_POINT with full write access for frc4607"
    
    # Verify permissions (for debugging)
    /bin/logger "Mount point permissions: \$(stat -c '%a %U:%G' "\$MOUNT_POINT")"
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
echo "  User: frc4607 (UID=$FRC_UID, GID=$FRC_GID)"
echo "  FAT32: dmask=0000, fmask=0000 (full permissions)"
echo "  exFAT/NTFS: umask=0000"
echo "  EXT4: chmod 777 after mount"
echo ""
echo "USB drives will auto-mount under /media/<LABEL>"
echo ""
echo "To test with current USB:"
echo "  sudo umount /media/RECORDINGS"
echo "  sudo /usr/local/bin/usb-mount.sh /dev/sda1"
echo "  ls -la /media/RECORDINGS"