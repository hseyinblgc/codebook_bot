
import asyncio
from uuid import uuid4
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import admin_token, user_token, admin_id

BOT_TOKEN = admin_token
CHAT_ID = admin_id


async def send_user_message(text: str):
    bot = Bot(token=user_token)
    await bot.send_message(chat_id=CHAT_ID, text=text)


_DECISION_LOCK = asyncio.Lock()


async def request_admin_decision(
    text: str,
    *,
    timeout_seconds: int = 300,
) -> dict:
    """Send one-time approval request and wait for button response.

    Returns:
        {"status": "approved" | "rejected" | "timeout", "reason": str | None}
    """
    async with _DECISION_LOCK:
        bot = Bot(token=BOT_TOKEN)
        request_id = uuid4().hex[:8]
        approve_data = f"approve:{request_id}"
        reject_data = f"reject:{request_id}"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Onayla", callback_data=approve_data),
                    InlineKeyboardButton("Reddet", callback_data=reject_data),
                ]
            ]
        )

        sent = await bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            reply_markup=keyboard,
        )

        updates = await bot.get_updates(timeout=0)
        offset = updates[-1].update_id + 1 if updates else None

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds

        while loop.time() < deadline:
            remaining = int(deadline - loop.time())
            updates = await bot.get_updates(
                offset=offset,
                timeout=min(30, max(1, remaining)),
                allowed_updates=["callback_query", "message"],
            )

            for update in updates:
                offset = update.update_id + 1
                callback = update.callback_query
                if not callback:
                    continue

                if callback.message.chat_id != CHAT_ID:
                    continue

                data = callback.data or ""
                if data == approve_data:
                    await callback.answer("Onaylandi")
                    await bot.edit_message_reply_markup(
                        chat_id=CHAT_ID,
                        message_id=callback.message.message_id,
                        reply_markup=None,
                    )
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text="Basvuru onaylandi.",
                        reply_to_message_id=sent.message_id,
                    )
                    return {"status": "approved", "reason": None}

                if data == reject_data:
                    await callback.answer("Red secildi")
                    await bot.edit_message_reply_markup(
                        chat_id=CHAT_ID,
                        message_id=callback.message.message_id,
                        reply_markup=None,
                    )
                    reason_prompt = await bot.send_message(
                        chat_id=CHAT_ID,
                        text="Red sebebini yazin:",
                        reply_to_message_id=sent.message_id,
                    )

                    reason, offset = await _wait_reject_reason(
                        bot,
                        offset,
                        CHAT_ID,
                        reason_prompt.message_id,
                        deadline,
                    )
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"Basvuru reddedildi. Sebep: {reason}",
                        reply_to_message_id=sent.message_id,
                    )
                    return {"status": "rejected", "reason": reason}

        await bot.send_message(
            chat_id=CHAT_ID,
            text="Karar suresi doldu. Islem zaman asimina ugradi.",
            reply_to_message_id=sent.message_id,
        )
        return {"status": "timeout", "reason": None}


async def _wait_reject_reason(
    bot: Bot,
    offset: int | None,
    chat_id: int,
    prompt_message_id: int,
    deadline: float,
) -> tuple[str, int | None]:
    loop = asyncio.get_running_loop()

    while loop.time() < deadline:
        remaining = int(deadline - loop.time())
        updates = await bot.get_updates(
            offset=offset,
            timeout=min(30, max(1, remaining)),
            allowed_updates=["message"],
        )

        for update in updates:
            offset = update.update_id + 1
            msg = update.message
            if not msg or msg.chat_id != chat_id or not msg.text:
                continue

            if (
                msg.reply_to_message
                and msg.reply_to_message.message_id == prompt_message_id
            ):
                return msg.text.strip(), offset

            return msg.text.strip(), offset

    return "Sebep belirtilmedi", offset
