import logging
import asyncio
from uuid import uuid4

from telegram import (Update, InlineKeyboardButton,
                      InlineKeyboardMarkup, WebAppInfo, Bot)
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config import user_token
# Bot loglarını görmek için yapılandırma
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = user_token

## ADMINBOT
class Admin:
    def __init__(self, *, admin_token: str, user_token: str, chat_id: int):
        self.chat_id = chat_id
        self._admin_bot = Bot(token=admin_token)
        self._decision_lock = asyncio.Lock()

    async def request_admin_decision(
        self,
        text: str,
        *,
        timeout_seconds: int = 300,
    ) -> dict:
        async with self._decision_lock:
            request_id = uuid4().hex[:8]
            approve_data = f"approve:{request_id}"
            reject_data = f"reject:{request_id}"

            keyboard = InlineKeyboardMarkup(
                [[
                    InlineKeyboardButton("Onayla", callback_data=approve_data),
                    InlineKeyboardButton("Reddet", callback_data=reject_data),
                ]]
            )

            sent = await self._admin_bot.send_message(
                chat_id=self.chat_id,
                text=text,
                reply_markup=keyboard,
            )

            updates = await self._admin_bot.get_updates(timeout=0)
            offset = updates[-1].update_id + 1 if updates else None

            loop = asyncio.get_running_loop()
            deadline = loop.time() + timeout_seconds

            while loop.time() < deadline:
                remaining = int(deadline - loop.time())
                updates = await self._admin_bot.get_updates(
                    offset=offset,
                    timeout=min(30, max(1, remaining)),
                    allowed_updates=["callback_query", "message"],
                )

                for update in updates:
                    offset = update.update_id + 1
                    callback = update.callback_query
                    if not callback:
                        continue
                    
                    # 1. Önemli Kontrol: Mesaj var mı ve erişilebilir mi?
                    # isinstance kontrolü linter'a bunun standart bir Message olduğunu kanıtlar.
                    if not callback.message or not hasattr(callback.message, 'chat'):
                        continue

                    # callback.message.chat.id kullanımı daha garantidir
                    if callback.message.chat.id != self.chat_id:
                        continue

                    data = callback.data or ""
                    if data == approve_data:
                        await callback.answer("Onaylandi")
                        await self._admin_bot.edit_message_reply_markup(
                            chat_id=self.chat_id,
                            message_id=callback.message.message_id,
                            reply_markup=None,
                        )
                        await self._admin_bot.send_message(
                            chat_id=self.chat_id,
                            text="Basvuru onaylandi.",
                            reply_to_message_id=sent.message_id,
                        )
                        return {"status": "approved", "reason": None}

                    if data == reject_data:
                        await callback.answer("Red secildi")
                        await self._admin_bot.edit_message_reply_markup(
                            chat_id=self.chat_id,
                            message_id=callback.message.message_id,
                            reply_markup=None,
                        )
                        reason_prompt = await self._admin_bot.send_message(
                            chat_id=self.chat_id,
                            text="Red sebebini yazin:",
                            reply_to_message_id=sent.message_id,
                        )

                        reason, offset = await self._wait_reject_reason(
                            offset=offset,
                            chat_id=self.chat_id,
                            prompt_message_id=reason_prompt.message_id,
                            deadline=deadline,
                        )
                        await self._admin_bot.send_message(
                            chat_id=self.chat_id,
                            text=f"Basvuru reddedildi. Sebep: {reason}",
                            reply_to_message_id=sent.message_id,
                        )
                        return {"status": "rejected", "reason": reason}

            await self._admin_bot.send_message(
                chat_id=self.chat_id,
                text="Karar suresi doldu. Islem zaman asimina ugradi.",
                reply_to_message_id=sent.message_id,
            )
            return {"status": "timeout", "reason": None}

    async def _wait_reject_reason(
        self,
        *,
        offset: int | None,
        chat_id: int,
        prompt_message_id: int,
        deadline: float,
    ) -> tuple[str, int | None]:
        loop = asyncio.get_running_loop()

        while loop.time() < deadline:
            remaining = int(deadline - loop.time())
            updates = await self._admin_bot.get_updates(
                offset=offset,
                timeout=min(30, max(1, remaining)),
                allowed_updates=["message"],
            )

            for update in updates:
                offset = update.update_id + 1
                msg = update.message
                if not msg or msg.chat_id != chat_id or not msg.text:
                    continue

                if msg.reply_to_message and msg.reply_to_message.message_id == prompt_message_id:
                    return msg.text.strip(), offset

                return msg.text.strip(), offset

        return "Sebep belirtilmedi", offset


## USERBOT
chat_id = ""
_user_bot = Bot(token=user_token)
async def send_user_message(text: str) -> None:
    await _user_bot.send_message(chat_id=chat_id, text=text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mini App URL (HTTPS olmak zorundadır)
    if update.message is not None and update.message.from_user is not None:
        user_id = update.message.from_user.id
    else:
        # Write here if there is no user info
        user_id = None
    miniapp_url = f"https://www.google.com/search?q={user_id}"

    # Inline klavye butonu oluşturma
    # 'web_app' parametresi butona tıklandığında Mini App'in açılmasını sağlar
    keyboard = [
        [
            InlineKeyboardButton(
                text="Uygulamayı Başlat",
                web_app=WebAppInfo(url=miniapp_url)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.effective_message:
        await update.effective_message.reply_text(
            "Hoş geldiniz! ...",
            reply_markup=reply_markup
        )


if __name__ == '__main__':

    # Uygulamayı oluşturma ve başlatma
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start komutunu yakalayan handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.run_polling()
