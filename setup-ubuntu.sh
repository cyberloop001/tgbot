#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "Installing venv + dependencies..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
chmod +x start-bot.sh stop-bot.sh setup-ubuntu.sh bot-bg.sh remove-ubuntu.sh

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env — edit it and set BOT_TOKEN, DEVELOPER_CHAT_ID, PARTNER_CHAT_ID"
else
  echo ".env already exists"
fi

echo
echo "Done. Next:"
echo "  1) nano .env   # put your secrets"
echo "  2) ./start-bot.sh"
echo "  3) ./stop-bot.sh   # when finished"
