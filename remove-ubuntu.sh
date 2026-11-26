#!/usr/bin/env bash
# Stop the bot and remove local install artifacts on Ubuntu.
# Keeps source code and .env by default.
# Usage:
#   ./remove-ubuntu.sh           # soft remove (venv, logs, pid)
#   ./remove-ubuntu.sh --all     # also delete .env

set -euo pipefail
cd "$(dirname "$0")"

REMOVE_ENV=0
if [[ "${1:-}" == "--all" ]]; then
  REMOVE_ENV=1
fi

echo "Stopping bot (if running)..."
if [[ -x ./bot-bg.sh ]]; then
  ./bot-bg.sh stop || true
else
  pkill -f "[.]venv/bin/python bot.py" 2>/dev/null || true
  pkill -f "[b]ot.py" 2>/dev/null || true
  rm -f .bot.pid
fi

echo "Removing virtualenv and runtime files..."
rm -rf .venv venv
rm -f .bot.pid bot.log
rm -rf __pycache__
find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

if [[ "$REMOVE_ENV" -eq 1 ]]; then
  echo "Removing .env..."
  rm -f .env
else
  echo "Keeping .env (use ./remove-ubuntu.sh --all to delete it too)."
fi

echo "Done. Project source files were kept."
echo "To reinstall later: ./setup-ubuntu.sh"
