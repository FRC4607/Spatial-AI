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
pip install -e "${workspace}"

# Install precommit
pip install pre-commit

# Vscode exports
export PYTHONPATH=$workspace
export PYTHONDONTWRITEBYTECODE=1