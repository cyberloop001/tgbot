#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if pkill -f "[b]ot.py"; then
  echo "Bot stopped."
else
  echo "Bot was not running."
fi
