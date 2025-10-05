#!/bin/bash

set -e
set -u
set -o pipefail

# Check if running as root, if not, re-run with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Re-running with sudo..."
    sudo "$0" "$@"
    exit $?
fi

echo "========================================="
echo "Setting up Raspberry Pi OS in Read-Only Mode"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "Step 1: Disabling services that write to disk..."
systemctl disable triggerhappy.service 2>/dev/null || true
systemctl disable logrotate.service 2>/dev/null || true
systemctl disable logrotate.timer 2>/dev/null || true

echo "Step 2: Disabling swap..."
systemctl disable dphys-swapfile.service 2>/dev/null || true
swapoff -a 2>/dev/null || true

echo "Step 3: Modifying systemd services to use tmpfs..."
# Disable man-db updates
systemctl disable man-db.timer 2>/dev/null || true

# Move /var/log to tmpfs
echo "tmpfs /var/log tmpfs nodev,nosuid,size=30M 0 0" >> /etc/fstab

# Move /var/tmp to tmpfs
echo "tmpfs /var/tmp tmpfs nodev,nosuid,size=30M 0 0" >> /etc/fstab

# Move /tmp to tmpfs (usually already there, but ensure it)
echo "tmpfs /tmp tmpfs nodev,nosuid,size=50M 0 0" >> /etc/fstab

echo "Step 4: Configuring systemd for read-only root..."
# Create directory for random seed (if it doesn't exist)
mkdir -p /var/lib/systemd 2>/dev/null || true

# Create override directory for fake-hwclock service
mkdir -p /etc/systemd/system/fake-hwclock.service.d

# Link random seed to tmpfs location
cat >> /etc/systemd/system/fake-hwclock.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=/bin/true
EOF

echo "Step 5: Moving frequently written files to tmpfs..."
# Create directory structure
mkdir -p /var/lib/systemd/timers

# Add more tmpfs mounts
cat >> /etc/fstab << 'EOF'
tmpfs /var/lib/dhcp tmpfs nodev,nosuid,size=1M 0 0
tmpfs /var/lib/dhcpcd5 tmpfs nodev,nosuid,size=1M 0 0
tmpfs /var/spool tmpfs nodev,nosuid,size=10M 0 0
tmpfs /var/lib/systemd tmpfs nodev,nosuid,size=5M 0 0
EOF

echo "Step 6: Modifying /etc/fstab for read-only root filesystem..."
# Backup original fstab
cp /etc/fstab /etc/fstab.backup

# Modify root partition to be read-only
sed -i 's/\(.*\/\s*ext4\s*defaults\)/\1,ro/' /etc/fstab
# Also handle different formats
sed -i 's/\(.*\/\s*ext4\s*\S*\)/&,ro/' /etc/fstab

# Modify boot partition to be read-only
sed -i 's/\(.*\/boot.*vfat\s*defaults\)/\1,ro/' /etc/fstab

echo "Step 7: Creating helper scripts for remounting..."

# Create script to remount as read-write
cat > /usr/local/bin/rw << 'EOF'
#!/bin/bash
sudo mount -o remount,rw /
sudo mount -o remount,rw /boot
echo "Filesystems remounted as READ-WRITE"
EOF
chmod +x /usr/local/bin/rw

# Create script to remount as read-only
cat > /usr/local/bin/ro << 'EOF'
#!/bin/bash
sudo mount -o remount,ro /
sudo mount -o remount,ro /boot
echo "Filesystems remounted as READ-ONLY"
EOF
chmod +x /usr/local/bin/ro

echo "Step 8: Configuring systemd-random-seed service..."
systemctl disable systemd-random-seed.service 2>/dev/null || true

echo "Step 9: Disabling filesystem check on boot..."
tune2fs -c -1 -i 0 /dev/mmcblk0p2 2>/dev/null || \
tune2fs -c -1 -i 0 /dev/sda2 2>/dev/null || \
echo "Could not disable fsck (filesystem may use different device name)"

echo ""
echo "========================================="
echo "Read-Only Filesystem Setup Complete!"
echo "========================================="
echo ""
echo "Helper commands created:"
echo "  rw  - Remount filesystems as read-write (for updates/changes)"
echo "  ro  - Remount filesystems as read-only (return to safe mode)"
echo ""
echo "IMPORTANT: After reboot, the system will be READ-ONLY."
echo "Use 'rw' command before making any changes."
echo "Use 'ro' command to return to read-only mode."
echo ""
