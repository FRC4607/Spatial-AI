#!/bin/bash

# Script to add custom aliases to ~/.bashrc

BASHRC="$HOME/.bashrc"

# Check if aliases already exist
if grep -q "# FRC4607 Custom Aliases" "$BASHRC"; then
    echo "Aliases already exist in $BASHRC"
    echo "Remove them manually if you want to re-add."
    exit 1
fi

# Add aliases to .bashrc
cat >> "$BASHRC" << 'EOF'

# FRC4607 Custom Aliases
# Fix permissions recursively on the entire USB
alias fixrecordings='sudo chown -R frc4607:frc4607 /media/RECORDINGS && sudo chmod -R 775 /media/RECORDINGS'

# Service commands
alias servicestatus='sudo systemctl status frc4607-spatial-ai.service'
alias servicestop='sudo systemctl stop frc4607-spatial-ai.service'
alias servicestart='sudo systemctl start frc4607-spatial-ai.service'

# Log commands
alias viewlogs='tail -n 1000 /media/RECORDINGS/frc4607-spatial-ai-error.log'
alias deletelogs='sudo rm -f /media/RECORDINGS/*.log'
EOF

echo "Aliases added to $BASHRC"
