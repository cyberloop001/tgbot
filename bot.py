"""
Two-way Telegram bridge bot with operator approval.

Developer/partner messages are held until the operator approves them.
Only approved content is delivered to the other side.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
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


@dataclass
class PendingMessage:
    pending_id: str
    from_chat_id: int
    message_id: int
    target_id: int
    direction: str
    # Operator's approval card message id (for reply-to editing)
    review_message_id: int | None = None


def _parse_optional_id(name: str, raw: str | None) -> int | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value in {"111111111", "222222222", "333333333", "0"}:
        return None
    try:
        return int(value)
    except ValueError:
        logger.error("%s must be a numeric Telegram chat/user ID, got: %r", name, value)
        sys.exit(1)


def load_config() -> tuple[str, int | None, int | None, int | None]:
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
            "2) /mybots -> your bot -> API Token\n"
            "3) Paste the token into .env as BOT_TOKEN=...\n"
            "4) Run: python bot.py"
        )
        sys.exit(1)

    developer_id = _parse_optional_id("DEVELOPER_CHAT_ID", os.getenv("DEVELOPER_CHAT_ID"))
    partner_id = _parse_optional_id("PARTNER_CHAT_ID", os.getenv("PARTNER_CHAT_ID"))
    operator_id = _parse_optional_id("OPERATOR_CHAT_ID", os.getenv("OPERATOR_CHAT_ID"))

    if developer_id is not None and partner_id is not None and developer_id == partner_id:
        logger.error("DEVELOPER_CHAT_ID and PARTNER_CHAT_ID must be different")
        sys.exit(1)

    return token, developer_id, partner_id, operator_id


def _approval_keyboard(pending_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{pending_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject:{pending_id}"),
            ]
        ]
    )


def _find_pending_by_review(
    pending: dict[str, PendingMessage], review_message_id: int
) -> PendingMessage | None:
    for item in pending.values():
        if item.review_message_id == review_message_id:
            return item
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    developer_id = context.bot_data.get("developer_id")
    partner_id = context.bot_data.get("partner_id")
    operator_id = context.bot_data.get("operator_id")
    chat_id = update.effective_chat.id if update.effective_chat else None

    if chat_id == operator_id:
        text = (
            "Operator mode.\n"
            "Pending messages from developer/partner will appear here.\n"
            "Tap Approve / Reject, or reply to a pending message with your own text "
            "to send that text instead."
        )
    elif developer_id and partner_id and operator_id:
        text = (
            "Bridge bot is online.\n"
            "Your messages are held for operator approval before delivery.\n\n"
            "Tip: use /whoami to see your Telegram chat ID."
        )
    else:
        text = "Bot is online (setup mode).\nSend /whoami."
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


async def handle_incoming(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hold developer/partner messages for operator approval."""
    message = update.message
    if not message or not update.effective_chat:
        return

    developer_id = context.bot_data.get("developer_id")
    partner_id = context.bot_data.get("partner_id")
    operator_id = context.bot_data.get("operator_id")
    pending: dict[str, PendingMessage] = context.bot_data.setdefault("pending", {})

    if not developer_id or not partner_id or not operator_id:
        await message.reply_text(
            "Bridge is not configured yet.\n"
            "Set DEVELOPER_CHAT_ID, PARTNER_CHAT_ID, and OPERATOR_CHAT_ID in .env, "
            "then restart the bot."
        )
        return

    sender_id = update.effective_chat.id

    # Operator: reply to a pending card with custom text to send that instead
    if sender_id == operator_id:
        if message.reply_to_message:
            item = _find_pending_by_review(pending, message.reply_to_message.message_id)
            if item and message.text:
                try:
                    await context.bot.send_message(chat_id=item.target_id, text=message.text)
                    pending.pop(item.pending_id, None)
                    await message.reply_text(f"Sent your approved text ({item.direction}).")
                    logger.info("Operator custom send %s", item.direction)
                except Exception:
                    logger.exception("Failed custom send %s", item.direction)
                    await message.reply_text(
                        "Could not deliver. Make sure the recipient started the bot with /start."
                    )
                return
        await message.reply_text(
            "To send a custom message: reply to a pending approval card with your text.\n"
            "Or tap Approve / Reject on a pending card."
        )
        return

    if sender_id == developer_id:
        target_id = partner_id
        direction = "developer → partner"
        label = "Developer"
    elif sender_id == partner_id:
        target_id = developer_id
        direction = "partner → developer"
        label = "Partner"
    else:
        await message.reply_text(
            "You are not registered for this bridge.\n"
            f"Your chat ID is {sender_id}."
        )
        return

    pending_id = uuid.uuid4().hex[:10]
    item = PendingMessage(
        pending_id=pending_id,
        from_chat_id=sender_id,
        message_id=message.message_id,
        target_id=target_id,
        direction=direction,
    )
    pending[pending_id] = item

    try:
        # Show operator the original content
        await context.bot.copy_message(
            chat_id=operator_id,
            from_chat_id=sender_id,
            message_id=message.message_id,
        )
        review = await context.bot.send_message(
            chat_id=operator_id,
            text=(
                f"Pending from {label} ({direction})\n"
                f"Approve to send the original, Reject to drop it, "
                f"or reply to this message with your own text to send that instead."
            ),
            reply_markup=_approval_keyboard(pending_id),
        )
        item.review_message_id = review.message_id
        logger.info("Queued %s (pending=%s)", direction, pending_id)
    except Exception:
        pending.pop(pending_id, None)
        logger.exception("Failed to queue %s", direction)
        await message.reply_text(
            "Could not queue for approval. "
            "Make sure the operator has started the bot with /start."
        )


async def on_approval_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return

    operator_id = context.bot_data.get("operator_id")
    if update.effective_user.id != operator_id:
        await query.answer("Only the operator can approve messages.", show_alert=True)
        return

    await query.answer()
    action, _, pending_id = query.data.partition(":")
    pending: dict[str, PendingMessage] = context.bot_data.setdefault("pending", {})
    item = pending.pop(pending_id, None)

    if not item:
        await query.edit_message_text("This request was already handled or expired.")
        return

    if action == "reject":
        await query.edit_message_text(f"Rejected ({item.direction}).")
        logger.info("Rejected %s (pending=%s)", item.direction, pending_id)
        return

    if action == "approve":
        try:
            await context.bot.copy_message(
                chat_id=item.target_id,
                from_chat_id=item.from_chat_id,
                message_id=item.message_id,
            )
            await query.edit_message_text(f"Approved and sent ({item.direction}).")
            logger.info("Approved %s (pending=%s)", item.direction, pending_id)
        except Exception:
            # Put it back so they can retry / custom-send
            pending[pending_id] = item
            logger.exception("Failed to deliver approved %s", item.direction)
            await query.edit_message_text(
                f"Approve failed ({item.direction}). "
                "Recipient may need to /start the bot. Request kept pending — "
                "reply to the copied message above with custom text, or ask them to /start."
            )
            # Restore buttons on a new message if edit lost them
            await context.bot.send_message(
                chat_id=operator_id,
                text=f"Still pending ({item.direction}).",
                reply_markup=_approval_keyboard(pending_id),
            )


def main() -> None:
    token, developer_id, partner_id, operator_id = load_config()
    if developer_id and partner_id and operator_id:
        logger.info(
            "Starting bridge with approval: developer=%s partner=%s operator=%s",
            developer_id,
            partner_id,
            operator_id,
        )
    else:
        logger.warning(
            "Starting in setup mode. Set DEVELOPER_CHAT_ID, PARTNER_CHAT_ID, "
            "and OPERATOR_CHAT_ID in .env for approval bridging."
        )

    app = Application.builder().token(token).build()
    app.bot_data["developer_id"] = developer_id
    app.bot_data["partner_id"] = partner_id
    app.bot_data["operator_id"] = operator_id
    app.bot_data["pending"] = {}

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("whoami", whoami))
    app.add_handler(CallbackQueryHandler(on_approval_button, pattern=r"^(approve|reject):"))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_incoming))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
