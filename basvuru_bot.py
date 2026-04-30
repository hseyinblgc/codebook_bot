import logging
from telegram import (Update, InlineKeyboardButton,
                      InlineKeyboardMarkup, WebAppInfo)
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config import user_token
# Bot loglarını görmek için yapılandırma
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = user_token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mini App URL (HTTPS olmak zorundadır)
    miniapp_url = "https://google.com"

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

    await update.message.reply_text(
        "Hoş geldiniz! Mini App'i başlatmak için aşağıdaki butona tıklayın:",
        reply_markup=reply_markup
    )

if __name__ == '__main__':

    # Uygulamayı oluşturma ve başlatma
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start komutunu yakalayan handler
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.run_polling()
