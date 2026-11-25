"""
Two-way Telegram bridge bot.

Messages from the developer are relayed to the partner, and vice versa.
Both parties talk to this bot; the bot copies messages across.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("bridge")

# Python 3.12+ / 3.15 no longer auto-create an event loop in main thread
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


def _parse_optional_id(name: str, raw: str | None) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    # Ignore common placeholders so /whoami works during setup
    if value in {"111111111", "222222222", "0"}:
        return None
    try:
        return int(value)
    except ValueError:
        logger.error("%s must be a numeric Telegram chat/user ID, got: %r", name, value)
        sys.exit(1)


def load_config() -> tuple[str, int | None, int | None]:
    token = os.getenv("BOT_TOKEN", "").strip()
    placeholder = (
        not token
        or token.lower().startswith("paste")
        or "your_token" in token.lower()
        or token == "123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        or not re.fullmatch(r"\d+:[A-Za-z0-9_-]{30,}", token)
    )
    if placeholder:
        logger.error(
            "BOT_TOKEN in .env is missing or still a placeholder.\n"
            "1) Open @BotFather in Telegram\n"
            "2) /mybots -> DevPro -> API Token\n"
            "3) Paste the token into D:\\work\\tgbot\\.env as BOT_TOKEN=...\n"
            "4) Run: python bot.py"
        )
        sys.exit(1)

    developer_id = _parse_optional_id("DEVELOPER_CHAT_ID", os.getenv("DEVELOPER_CHAT_ID"))
    partner_id = _parse_optional_id("PARTNER_CHAT_ID", os.getenv("PARTNER_CHAT_ID"))

    if developer_id is not None and partner_id is not None and developer_id == partner_id:
        logger.error("DEVELOPER_CHAT_ID and PARTNER_CHAT_ID must be different")
        sys.exit(1)

    return token, developer_id, partner_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    developer_id = context.bot_data.get("developer_id")
    partner_id = context.bot_data.get("partner_id")
    if developer_id and partner_id:
        text = (
            "Bridge bot is online.\n"
            "Send me a message and I will relay it to the other side.\n\n"
            "Tip: use /whoami to see your Telegram chat ID."
        )
    else:
        text = (
            "Bot is online (setup mode).\n"
            "Send /whoami, then put your ID into .env.\n"
            "You need both DEVELOPER_CHAT_ID and PARTNER_CHAT_ID before bridging works."
        )
    await update.message.reply_text(text)


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    user = update.effective_user
    chat = update.effective_chat
    lines = [
        f"Your user ID: {user.id}",
        f"This chat ID: {chat.id if chat else 'n/a'}",
    ]
    if user.username:
        lines.append(f"Username: @{user.username}")
    await update.message.reply_text("\n".join(lines))


async def relay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Copy any inbound message from one side to the other."""
    message = update.message
    if not message or not update.effective_chat:
        return

    developer_id = context.bot_data.get("developer_id")
    partner_id = context.bot_data.get("partner_id")
    if not developer_id or not partner_id:
        await message.reply_text(
            "Bridge is not configured yet.\n"
            "Send /whoami from both accounts, put both IDs into .env, then restart the bot."
        )
        return

    sender_id = update.effective_chat.id

    if sender_id == developer_id:
        target_id = partner_id
        direction = "developer → partner"
    elif sender_id == partner_id:
        target_id = developer_id
        direction = "partner → developer"
    else:
        await message.reply_text(
            "You are not registered as developer or partner for this bridge.\n"
            f"Your chat ID is {sender_id}. Add it to .env and restart the bot."
        )
        return

    try:
        await context.bot.copy_message(
            chat_id=target_id,
            from_chat_id=sender_id,
            message_id=message.message_id,
        )
        logger.info("Relayed %s (msg %s)", direction, message.message_id)
    except Exception:
        logger.exception("Failed to relay %s (msg %s)", direction, message.message_id)
        await message.reply_text(
            "Could not deliver that message. "
            "Make sure the other person has started the bot with /start."
        )


def main() -> None:
    token, developer_id, partner_id = load_config()
    if developer_id and partner_id:
        logger.info("Starting bridge: developer=%s partner=%s", developer_id, partner_id)
    else:
        logger.warning(
            "Starting in setup mode (chat IDs not set yet). "
            "/start and /whoami work; message bridging is off until both IDs are in .env."
        )

    app = Application.builder().token(token).build()
    app.bot_data["developer_id"] = developer_id
    app.bot_data["partner_id"] = partner_id

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(MessageHandler(~filters.COMMAND, relay))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
