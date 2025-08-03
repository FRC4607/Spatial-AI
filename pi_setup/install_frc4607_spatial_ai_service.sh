#!/bin/bash

SERVICE_FILE="/etc/systemd/system/frc4607-spatial-ai.service"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Create the service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FRC4607 Spatial AI Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/Spatial-AI
Environment=VIRTUAL_ENV=/home/Spatial-AI/venv
Environment=PYTHONPATH=/home/Spatial-AI
ExecStart=/home/Spatial-AI/venv/bin/python /home/Spatial-AI/spatial_ai/spatial_ai_device.py
Restart=always
RestartSec=10
StandardOutput=append:/media/RECORDINGS/frc4607-spatial-ai.log
StandardError=append:/media/RECORDINGS/frc4607-spatial-ai-error.log
SyslogIdentifier=frc4607-spatial-ai

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at $SERVICE_FILE"
echo "Run 'systemctl daemon-reload' to reload systemd"