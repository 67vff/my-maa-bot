import logging
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- НАСТРОЙКИ (берутся из переменных окружения BotHost) ---
TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
MILLIDA_API_KEY = os.environ.get("MILLIDA_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Полный URL для отправки команд в консоль Millida ---
API_URL = "https://millida.net"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для привязки Telegram к аккаунту Minecraft.\n"
        "1. Зайди на сервер.\n"
        "2. Введи в игре /botlink.\n"
        "3. Отправь мне код командой: /confirm ТВОЙ_КОД"
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи код: /confirm ТВОЙ_КОД")
        return
    
    code = context.args[0]
    
    if not MILLIDA_API_KEY:
        await update.message.reply_text("Ошибка: API ключ Millida не настроен на сервере.")
        return

    try:
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "command": f"makaauth botconfirm {code}"
        }
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code in (200, 201, 204):
            await update.message.reply_text(
                f"✅ Код {code} подтвержден! Теперь зайди в игру и введи:\n"
                f"`/botaccept {code}`",
                parse_mode='Markdown'
            )
        else:
            error_details = response.text[:400] if response.text else "Пустой ответ от сервера"
            logger.error(f"Ошибка API: {response.status_code} - {response.text}")
            
            await update.message.reply_text(
                f"❌ Ошибка API Millida!\n"
                f"Код статуса: {response.status_code}\n"
                f"Ответ сервера:\n{error_details}"
            )
            
    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")
        await update.message.reply_text(f"❌ Ошибка подключения к API:\n{type(e).__name__}: {e}")

def main():
    if not TELEGRAM_TOKEN or not MILLIDA_API_KEY:
        logger.error("Критическая ошибка: не заданы BOT_TOKEN или MILLIDA_API_KEY в переменных окружения!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    
    logger.info("Бот успешно запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
