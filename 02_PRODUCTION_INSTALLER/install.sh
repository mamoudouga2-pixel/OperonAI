#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .[test]
python -m pytest -q
