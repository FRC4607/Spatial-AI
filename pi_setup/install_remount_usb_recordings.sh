#!/bin/bash
set -e
set -u
set -o pipefail

# --- 1. Create remount script ---
sudo tee /usr/local/bin/usb-remount-existing.sh > /dev/null <<'EOF'
#!/bin/bash
# Remount any USB storage devices that exist at boot

logger "usb-remount-existing: checking for connected USB storage devices..."

for dev in /dev/sd*[0-9]; do
    if [ -b "$dev" ]; then
        logger "usb-remount-existing: attempting to mount $dev"
        /usr/local/bin/usb-mount.sh "$dev"
    fi
done

logger "usb-remount-existing: completed scan"
EOF

sudo chmod +x /usr/local/bin/usb-remount-existing.sh
echo "Created /usr/local/bin/usb-remount-existing.sh"

# --- 2. Create systemd service ---
SERVICE_FILE="/etc/systemd/system/usb-remount-existing.service"

sudo tee "$SERVICE_FILE" > /dev/null <<'EOF'
[Unit]
Description=Remount existing USB drives on boot
After=multi-user.target
RequiresMountsFor=/media

[Service]
Type=oneshot
ExecStart=/usr/local/bin/usb-remount-existing.sh
RemainAfterExit=no
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "Created $SERVICE_FILE"

# --- 3. Enable + reload systemd ---
sudo systemctl daemon-reload
sudo systemctl enable usb-remount-existing.service

echo "Enabled usb-remount-existing.service (will run at boot)"

# --- 4. Optionally run immediately ---
echo ""
read -p "Run now to test? [y/N]: " RUN_NOW
if [[ "${RUN_NOW,,}" == "y" ]]; then
    sudo systemctl start usb-remount-existing.service
    echo "Service started manually."
else
    echo "You can test later with: sudo systemctl start usb-remount-existing.service"
fi

echo ""
echo "Installation complete!"
echo "  - Script: /usr/local/bin/usb-remount-existing.sh"
echo "  - Service: /etc/systemd/system/usb-remount-existing.service"
echo ""
echo "USB drives connected at boot will now be auto-mounted."
