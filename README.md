# Telegram Bridge Bot

Relays messages two ways between your **developer** and **partner**, with **your approval** in the middle.

```
Developer / Partner  →  Bot  →  You (operator) approve  →  Other side
```

Nothing is delivered until you approve it (or reply with your own replacement text).

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
OPERATOR_CHAT_ID=
```

### 3. Get chat IDs

1. Put your bot token in `.env` and run the bot
2. From the **developer** account → DevPro → `/start` → `/whoami`
3. From the **partner** account → `/start` → `/whoami`
4. From **your operator** account (the one that will approve) → `/start` → `/whoami`
5. Put those three IDs into `.env`, then restart the bot

All three accounts **must** press **Start** at least once.

### 4. Run

```powershell
.\.venv\Scripts\Activate.ps1
python bot.py
```

Keep this window open while you want the bridge running.

## How to use

1. Developer or partner sends a message to the bot
2. **You** (operator) receive a copy plus **Approve / Reject** buttons
3. Choose one:
   - **Approve** → original message is sent to the other side
   - **Reject** → nothing is sent
   - **Reply** to the pending card with your own text → that text is sent instead
4. Only what you approve (or rewrite) is delivered

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
nano .env   # set BOT_TOKEN, DEVELOPER_CHAT_ID, PARTNER_CHAT_ID, OPERATOR_CHAT_ID

# whenever you need the bridge
./start-bot.sh

# stop
./stop-bot.sh
# or press Ctrl+C in the start terminal
```

Run in background (optional):

```bash
chmod +x bot-bg.sh
./bot-bg.sh start      # start in background
./bot-bg.sh stop       # stop
./bot-bg.sh restart
./bot-bg.sh status
./bot-bg.sh logs       # follow bot.log
```

Remove local install (stops bot, deletes `.venv` / logs; keeps source):

```bash
chmod +x remove-ubuntu.sh
./remove-ubuntu.sh           # keep .env
./remove-ubuntu.sh --all     # also delete .env
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
