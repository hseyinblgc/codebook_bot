import logging
from telegram import (Update, InlineKeyboardButton,
                      InlineKeyboardMarkup, WebAppInfo, Bot)
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from auth_token import make_token
import os


# Bot loglarını görmek için yapılandırma
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

user_token = os.getenv("USER_TOKEN", "")
miniapp = os.getenv("MINI_APP", "")
admin_id = int(os.getenv("ADMIN_ID", 0))

## USERBOT
_user_bot = Bot(token=user_token)
async def send_user_message(text: str, user_id: int) -> None:
    await _user_bot.send_message(chat_id=user_id, text=text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hata durumunda erken dön
    if update.message is None or update.message.from_user is None:
        if update.effective_message:
            await update.effective_message.reply_text("Hatalı istek.")
        return

    # Buradan itibaren user_id ve token güvenli
    user_id = update.message.from_user.id
    token = make_token(user_id, ttl_seconds=3600)
    miniapp_url = f"{miniapp}/?token={token}"

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

# Admin
async def requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Hata durumunda erken dön
    user = update.effective_user
    if user is None or user.id != (admin_id):
        return  # sessizce çık

    keyboard = [
        [
            InlineKeyboardButton(text="Onayla", callback_data="approve"),
            InlineKeyboardButton(text="Onaylama", callback_data="reject"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.effective_message:
        await update.effective_message.reply_text(
            "Hoş geldiniz! ...",
            reply_markup=reply_markup
        )


async def approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query is None:
        return

    await query.answer()

    if query.data == "approve":
        await query.edit_message_text("Onay verdiniz.")
    elif query.data == "reject":
        await query.edit_message_text("Onaylamadınız.")


if __name__ == '__main__':

    # Uygulamayı oluşturma ve başlatma
    application = ApplicationBuilder().token(user_token).build()

    # /start komutunu yakalayan handler
    start_handler = CommandHandler('start', start)
    requests_handler = CommandHandler('requests', requests)
    application.add_handler(start_handler)
    application.add_handler(requests_handler)
    application.add_handler(CallbackQueryHandler(approval_callback))
    application.run_polling()
