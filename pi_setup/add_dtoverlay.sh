#!/bin/bash

# Detect config.txt location (varies by Pi OS version)
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
else
    echo "Error: Could not find config.txt"
    exit 1
fi

echo "Found config file at: $CONFIG_FILE"

# Backup the original config
sudo cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "Backup created: $CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"

# Check if our settings already exist
if grep -q "dtoverlay=disable-bt" "$CONFIG_FILE" && \
   grep -q "dtoverlay=disable-wifi" "$CONFIG_FILE" && \
   grep -q "dtparam=audio=off" "$CONFIG_FILE"; then
    echo "Settings already present in $CONFIG_FILE"
    exit 0
fi

# Add settings to config.txt
echo "" | sudo tee -a "$CONFIG_FILE" > /dev/null
echo "# Minimal system configuration - added $(date)" | sudo tee -a "$CONFIG_FILE" > /dev/null
echo "dtoverlay=disable-bt" | sudo tee -a "$CONFIG_FILE" > /dev/null
echo "dtoverlay=disable-wifi" | sudo tee -a "$CONFIG_FILE" > /dev/null
echo "dtparam=audio=off" | sudo tee -a "$CONFIG_FILE" > /dev/null

echo "Settings added to $CONFIG_FILE"
echo "Done disabling unnessary hardware, reboot required for changes to take effect."
