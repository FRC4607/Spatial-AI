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


# Detect site-packages inside the active venv
SITE_PACKAGES=$(python -c "import site; print([p for p in site.getsitepackages() if 'site-packages' in p][0])")
CUSTOM_FILE="$SITE_PACKAGES/sitecustomize.py"

# And disable future warnings
cat <<EOF > "$CUSTOM_FILE"
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
EOF

# Vscode exports
export PYTHONPATH=$workspace
export PYTHONDONTWRITEBYTECODE=1