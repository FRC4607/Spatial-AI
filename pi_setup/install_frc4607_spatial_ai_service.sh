#!/bin/bash

set -e
set -u
set -o pipefail

SERVICE_FILE="/etc/systemd/system/frc4607-spatial-ai.service"
WORKING_DIR="/home/frc4607/Spatial-AI"
VENV_PATH="$WORKING_DIR/venv"
PYTHON_SCRIPT="$WORKING_DIR/spatial_ai/spatial_ai_device.py"
LOG_DIR="/media/RECORDINGS"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Validate directories exist
echo "Validating paths..."
if [ ! -d "$WORKING_DIR" ]; then
    echo "Error: Working directory $WORKING_DIR does not exist"
    exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment $VENV_PATH does not exist"
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script $PYTHON_SCRIPT does not exist"
    exit 1
fi

if [ ! -d "$LOG_DIR" ]; then
    echo "Warning: Log directory $LOG_DIR does not exist."
    echo "         Logs will fail until USB is mounted at $LOG_DIR"
fi

# Create the service file
echo "Creating service file at $SERVICE_FILE..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FRC4607 Spatial AI Service
After=network.target

[Service]
Type=simple
User=frc4607
Group=frc4607
WorkingDirectory=$WORKING_DIR
Environment=VIRTUAL_ENV=$VENV_PATH
Environment=PYTHONPATH=$WORKING_DIR
ExecStart=$VENV_PATH/bin/python $PYTHON_SCRIPT
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/frc4607-spatial-ai.log
StandardError=append:$LOG_DIR/frc4607-spatial-ai-error.log
SyslogIdentifier=frc4607-spatial-ai

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created successfully!"
echo ""
echo "Service configuration:"
echo "  - Starts after network is ready"
echo "  - Runs as frc4607 user"
echo "  - Auto-restarts on failure"
echo "  - Logs to $LOG_DIR (USB must be mounted)"
echo ""

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling service to start on boot..."
systemctl enable frc4607-spatial-ai.service

# Start the service now
echo "Starting service..."
systemctl start frc4607-spatial-ai.service

# Give it a moment to start
sleep 2

# Show the service status
echo ""
echo "Service status:"
systemctl status frc4607-spatial-ai.service --no-pager || true

echo ""
echo "Service installed and started successfully!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status frc4607-spatial-ai.service   # Check status"
echo "  sudo systemctl restart frc4607-spatial-ai.service  # Restart service"
echo "  sudo systemctl stop frc4607-spatial-ai.service     # Stop service"
echo "  sudo systemctl disable frc4607-spatial-ai.service  # Disable auto-start"
echo "  sudo journalctl -u frc4607-spatial-ai.service -f   # View logs in real-time"
echo "  sudo journalctl -u frc4607-spatial-ai.service -n 50  # View last 50 log lines"
echo ""
echo "Note: Ensure USB is mounted at $LOG_DIR for logging to work"