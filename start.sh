#!/usr/bin/env bash
# One-click setup and launch for DWG AI Extractor.
# Usage: chmod +x start.sh && ./start.sh

set -euo pipefail
cd "$(dirname "$0")"

VENV_PYTHON=".venv/bin/python"

# 1. Create venv (first run only)
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "\033[36m[1/3] Creating virtual environment...\033[0m"
    python3 -m venv .venv
else
    echo -e "\033[90m[1/3] Venv already exists, skipping.\033[0m"
fi

# 2. Install / update dependencies
echo -e "\033[36m[2/3] Installing dependencies...\033[0m"
"$VENV_PYTHON" -m pip install -e ".[dev]" -q --disable-pip-version-check

# 3. Launch GUI
echo -e "\033[32m[3/3] Launching GUI...\033[0m"
"$VENV_PYTHON" -m frontend.desktop.app
