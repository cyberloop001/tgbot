#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Stop any existing instance first (avoids Telegram Conflict)
pkill -f "[b]ot.py" 2>/dev/null || true
sleep 1

if [[ ! -x .venv/bin/python ]]; then
  echo "Virtualenv missing. Run:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "Starting bridge bot... (Ctrl+C to stop)"
exec .venv/bin/python bot.py
