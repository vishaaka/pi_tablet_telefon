#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/pi_tablet_telefon}"
BACKEND_DIR="$REPO_DIR/backend"

cd "$BACKEND_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Backend installed in $BACKEND_DIR"
echo "Run:"
echo ". $BACKEND_DIR/.venv/bin/activate"
echo "uvicorn app.main:app --host 0.0.0.0 --port 8080"
