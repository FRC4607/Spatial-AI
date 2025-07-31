#!/bin/bash

echo "Installing USB auto-mount + auto-unmount..."

# ========================
# 1. Create USB mount script
# ========================
MOUNT_SCRIPT="/usr/local/bin/usb-mount.sh"

sudo tee "$MOUNT_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash

DEVICE=$1

# Wait to settle
sleep 1

FSTYPE=$(blkid -o value -s TYPE "$DEVICE")
LABEL=$(blkid -o value -s LABEL "$DEVICE")

# Fallback if no label
[ -z "$LABEL" ] && LABEL=$(basename "$DEVICE")

MOUNT_POINT="/media/$LABEL"

mkdir -p "$MOUNT_POINT"

mount -t "$FSTYPE" -o defaults,noatime "$DEVICE" "$MOUNT_POINT" 2>/dev/null

if mount | grep -q "$MOUNT_POINT"; then
    logger "USB $DEVICE mounted at $MOUNT_POINT"
else
    logger "Failed to mount $DEVICE"
fi
EOF

sudo chmod +x "$MOUNT_SCRIPT"

# ========================
# 2. Create USB unmount script
# ========================
UNMOUNT_SCRIPT="/usr/local/bin/usb-unmount.sh"

sudo tee "$UNMOUNT_SCRIPT" > /dev/null << 'EOF'
#!/bin/bash

DEVICE=$1

# Wait for device removal to fully settle
sleep 1

MOUNTED=$(mount | grep "$DEVICE" | awk '{ print $3 }')

if [ -n "$MOUNTED" ]; then
    umount "$DEVICE"
    logger "🔌 USB $DEVICE unmounted from $MOUNTED"
    rmdir "$MOUNTED" 2>/dev/null
fi
EOF

sudo chmod +x "$UNMOUNT_SCRIPT"

# ========================
# 3. Create udev rules
# ========================
RULE_FILE="/etc/udev/rules.d/99-usb-mount.rules"

sudo tee "$RULE_FILE" > /dev/null <<EOF
KERNEL=="sd[a-z][0-9]", ACTION=="add", RUN+="$MOUNT_SCRIPT /dev/%k"
KERNEL=="sd[a-z][0-9]", ACTION=="remove", RUN+="$UNMOUNT_SCRIPT /dev/%k"
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

echo "Done! Plug in a USB drive to auto-mount under /media/<LABEL>, and it will auto-unmount on removal."
