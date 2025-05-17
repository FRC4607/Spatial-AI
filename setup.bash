#!/usr/bin/env bash

# Workspace
export workspace=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Virtual environment
python -m venv "${workspace}/venv"
source ${workspace}/venv/bin/activate

# Get latest PIP
pip install --upgrade pip

# Install required packages
pip install -r "${workspace}/requirements.txt"

# Install this local package into the venv
pip install --editable "${workspace}."

# Install precommit hooks
pre-commit intall

# Vscode exports
export PYTHONPATH=$workspace
export PYTHONDONTWRITEBYTECODE=1