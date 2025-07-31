#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 \"Your Name\" \"you@example.com\" \"https://github.com/FRC4607/Spatial-AI.git\""
    exit 1
fi

./install_git_and_clone_repo.sh "$1" "$2" "$3"
./automount_usb_recordings.sh
