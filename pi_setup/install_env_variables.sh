#!/bin/bash

# Path to your virtual environment
VENV_PATH="$HOME/Spatial-AI/venv"
ACTIVATE="$VENV_PATH/bin/activate"
POSTACTIVATE="$VENV_PATH/bin/postactivate"

# Create postactivate file with your environment variables
cat << 'EOF' > "$POSTACTIVATE"
# === Spatial-AI environment variables ===
export SPATIAL_AI_MODE="dev"
export SPATIAL_AI_HOST="frc4607-spatial-ai"
export RESOLUTION="med"
export MODEL="./models/2025/07-25_15-28-56/yolov5n.json"
# =======================================
EOF

chmod +x "$POSTACTIVATE"

# Patch activate script to source postactivate if not already present
if ! grep -q "postactivate" "$ACTIVATE"; then
    echo '[ -f "$VIRTUAL_ENV/bin/postactivate" ] && . "$VIRTUAL_ENV/bin/postactivate"' >> "$ACTIVATE"
fi

echo "postactivate created and activate script patched."
echo "Environment variables will now be set whenever you run 'source $VENV_PATH/bin/activate'."
