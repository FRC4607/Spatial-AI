#!/bin/bash

GIT_NAME="$1"
GIT_EMAIL="$2"
REPO_URL="$3"

# Install Git if not already installed
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt install -y git || { echo "Git installation failed."; exit 1; }
else
    echo "Git is already installed: $(git --version)"
fi

echo "Configuring Git user..."
git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"

echo "Git config set:"
git config --global --list

# Clone the repository
TARGET_PARENT="/home/${GIT_NAME}"
mkdir -p "$TARGET_PARENT"
cd "$TARGET_PARENT"
REPO_DIR=$(basename "${REPO_URL%%.git*}")
if [ -d "$REPO_DIR" ]; then
    echo "Directory '$REPO_DIR' already exists. Skipping clone."
else
    echo "Cloning repository from $REPO_URL..."
    git clone "$REPO_URL" || { echo "Failed to clone repo."; exit 1; }
fi

echo "Done installing Git and cloning repo."
