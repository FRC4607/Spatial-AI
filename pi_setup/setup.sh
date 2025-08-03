#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 \"Your Name\" \"you@example.com\" \"https://github.com/FRC4607/Spatial-AI.git\""
    exit 1
fi

./install_git_and_clone_repo.sh "$1" "$2" "$3"      # Install git and clone Spatial-AI
./install_required_packages.sh                      # Install required packages
./install_automount_usb_recordings.sh               # Setup USB flash drive
./install_movidius_udev_rules.sh                    # Setup OAK-D camera UDEV rules
# ./install_env_variables.sh
# ./install_frc4607_spatial_ai_service.sh
# ./disable_services.sh
