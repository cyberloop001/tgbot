# Telegram Bridge Bot

Relays messages two ways between your **developer** and **partner**.

```
Developer  ←→  Bot  ←→  Partner
```

When the developer sends something to the bot, the partner receives it.
When the partner sends something to the bot, the developer receives it.
Text, photos, files, voice, video, stickers, and most other media are copied across.

## Setup (once)

### 1. Create the bot

1. Open Telegram and talk to [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token**

### 2. Install and configure

```powershell
cd D:\work\tgbot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and paste the bot token:

```env
BOT_TOKEN=paste_token_here
DEVELOPER_CHAT_ID=
PARTNER_CHAT_ID=
```

### 3. Get chat IDs

1. Start the bot temporarily with empty IDs replaced by placeholders, **or** put any temporary numbers and use `/whoami`.

Easiest path:

1. Put your bot token in `.env`
2. Temporarily set both IDs to your own user ID (get it from [@userinfobot](https://t.me/userinfobot) or later from `/whoami`)
3. Run the bot
4. From the **developer** Telegram account, open the bot and send `/start` then `/whoami`
5. From the **partner** Telegram account, open the bot and send `/start` then `/whoami`
6. Put those two user IDs into `.env` as `DEVELOPER_CHAT_ID` and `PARTNER_CHAT_ID`
7. Restart the bot

Both people **must** press **Start** on the bot at least once, or Telegram will block delivery.

### 4. Run

```powershell
.\.venv\Scripts\Activate.ps1
python bot.py
```

Keep this window open while you want the bridge running.

## How to use

1. Developer opens the bot chat and types (or sends a file/photo)
2. Partner gets the same content in their bot chat
3. Partner replies in the bot chat
4. Developer gets the reply

## Free on-demand (start / stop yourself)

No cloud cost. Run the bot only when you need it. Machine must stay on and online while it runs.

### Windows

**Start:** double-click `start-bot.bat`  
**Stop:** close that window, `Ctrl+C`, or double-click `stop-bot.bat`

### Ubuntu

```bash
# one-time setup
chmod +x setup-ubuntu.sh start-bot.sh stop-bot.sh
./setup-ubuntu.sh
nano .env   # set BOT_TOKEN, DEVELOPER_CHAT_ID, PARTNER_CHAT_ID

# whenever you need the bridge
./start-bot.sh

# stop
./stop-bot.sh
# or press Ctrl+C in the start terminal
```

Run in background (optional):

```bash
nohup ./start-bot.sh > bot.log 2>&1 &
./stop-bot.sh
```

## Deploy to Railway (24/7 cloud)

This bot uses **long polling** (`python bot.py` keeps asking Telegram for new messages). That means the cloud process must stay running.

### Cost reality (2026)

| Plan | Cost | Notes |
| --- | --- | --- |
| Railway Trial | $0 for 30 days ($5 credit) | Good for first deploy |
| Railway Free | $0 + $1 usage/month | Always-on polling usually burns the $1 and then **stops** |
| Railway Hobby | **$5/month** | Best cheap option for reliable 24/7 |

For a bridge you use every day, plan on **Hobby ($5/mo)**.

### Steps

1. **Stop the local bot** (`Ctrl+C`). Only one instance may run.
2. Create a GitHub repo and push this project (**never push `.env`** — it is already in `.gitignore`).
3. Sign up at [railway.app](https://railway.app) and connect GitHub.
4. **New Project** → **Deploy from GitHub repo** → select this repo.
5. Open the service → **Variables** → add:
   - `BOT_TOKEN`
   - `DEVELOPER_CHAT_ID`
   - `PARTNER_CHAT_ID`
6. Set **Start Command** to: `python bot.py`  
   (or rely on the included `Procfile`: `worker: python bot.py`)
7. Deploy, then open **Logs**. You want to see:
   `Starting bridge: developer=... partner=...` and `Application started`
8. Test in Telegram: message DevPro from one account; the other should receive it.

### After deploy

- Pushing to GitHub usually redeploys automatically.
- If you see `Conflict: terminated by other getUpdates`, something else is still running the same bot (your PC). Stop the local process.
- To change IDs/token later: edit Variables in Railway and redeploy/restart.

## Notes

- This uses the official Bot API. Both sides talk to **the bot**, not each other directly.
- If you need to keep existing private DMs unchanged (no bot in the middle), that requires a different approach (Telegram user client / Telethon). Say if you want that instead.
- Do not commit your `.env` file; it contains secrets.
