#!/bin/bash

sudo apt update
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-opencv \
    build-essential

echo "Done installing required packages."