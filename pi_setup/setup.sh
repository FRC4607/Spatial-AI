#!/bin/bash

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit if any command in a pipeline fails

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 \"Your Name\" \"you@example.com\" \"https://github.com/FRC4607/Spatial-AI.git\""
    exit 1
fi

echo ""
echo "Step 1: Setting up USB automount/remount..."
./install_automount_usb_recordings.sh
./install_remount_usb_recordings.sh
echo ""
sleep 3

echo ""
echo "Step 2: Setting up OAK-D camera UDEV rules..."
./install_movidius_udev_rules.sh
echo ""
sleep 3

echo ""
echo "Step 3: Installing required packages..."
./install_required_packages.sh
echo ""
sleep 3

echo ""
echo "Step 4: Disabling unnecessary services..."
./disable_services.sh
echo ""
sleep 3

echo ""
echo "Step 5: Installing git and cloning repository..."
./install_git_and_clone_repo.sh "$1" "$2" "$3"
echo ""
sleep 3

echo ""
echo "Step 6: Installing environment variables..."
./install_env_variables.sh
echo ""
sleep 3

echo ""
echo "Step 7: Disabling unnecessary hardware..."
./add_dtoverlay.sh
echo ""
sleep 3

echo ""
echo "Step 8: Installing the FRC4607 Spatial AI service..."
./install_frc4607_spatial_ai_service.sh
echo ""
sleep 3

echo ""
echo "Step 9: Installing command aliases..."
./add_aliases.sh
echo ""
sleep 3

# echo ""
# echo "Step 8: Install RO and RW mount scripts..."
# ./install_rw_ro_mount_scripts.sh
# echo ""
# sleep 3

echo ""
echo "Setup completed successfully! Rebooting in read-only now..."
sleep 10
sudo reboot
