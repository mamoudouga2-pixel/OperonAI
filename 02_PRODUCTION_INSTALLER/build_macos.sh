#!/usr/bin/env bash
set -euo pipefail
python3 -m pip install -U pyinstaller
pyinstaller --onefile --name LMCAWorkerInstaller launcher.py
echo "Build output: dist/LMCAWorkerInstaller"
