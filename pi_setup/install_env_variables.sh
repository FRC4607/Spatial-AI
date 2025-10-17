#!/bin/bash

export SPATIAL_AI_MODE="dev"
export SPATIAL_AI_HOST="frc4607-spatial-ai"
export RESOLUTION="med"
export MODEL="./models/2025/07-25_15-28-56/yolov5n.json
echo "SPATIAL_AI_MODE=${SPATIAL_AI_MODE}"
echo "SPATIAL_AI_HOST=${SPATIAL_AI_HOST}"
echo "RESOLUTION=${RESOLUTION}"
echo "MODEL=${MODEL}"

echo "Done setting up environment variables."