#!/usr/bin/env bash
# One-time setup (Mac/Linux). Run from anywhere: bash scripts/setup.sh
set -e
cd "$(dirname "$0")/.."
[ -f .env ] || { cp .env.example .env; echo "Created .env from .env.example. Fill in your own keys."; }
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r api/requirements.txt
(cd web && npm install)
.venv/bin/python scripts/check_env.py
echo "Setup done. Next: scripts/run_api.sh, scripts/run_bot.sh, scripts/run_web.sh (three terminals)."
