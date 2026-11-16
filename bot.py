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

# --- Базовый URL API Millida для отправки команд ---
API_URL = "https://api.millida.net/v2/hosting/command" 

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
        await update.message.reply_text("Ошибка: API ключ Millida не настроен.")
        return

    try:
        headers = {
            "Authorization": f"Bearer {MILLIDA_API_KEY}",
            "Content-Type": "application/json"
        }
        # Отправляем команду в консоль сервера (на kapcha)
        data = {
            "command": f"makaauth botconfirm {code}"
        }
        
        response = requests.post(API_URL, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            await update.message.reply_text(
                f"Код {code} подтвержден! Теперь зайди в игру и введи:\n"
                f"`/botaccept {code}`",
                parse_mode='Markdown'
            )
        else:
            logger.error(f"Ошибка API: {response.status_code} - {response.text}")
            await update.message.reply_text(f"Ошибка API Millida: {response.status_code}. Проверь ключ и права.")
            
    except Exception as e:
        logger.error(f"Ошибка запроса: {e}")
        await update.message.reply_text(f"Ошибка подключения к API: {e}")

def main():
    if not TELEGRAM_TOKEN or not MILLIDA_API_KEY:
        logger.error("Не заданы BOT_TOKEN или MILLIDA_API_KEY!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    print("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
